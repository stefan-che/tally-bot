# syntax=docker/dockerfile:1
#
# Base: Chainguard Wolfi (glibc, rolling, patched daily) instead of Debian slim.
# Debian bookworm carried 5 CRITICAL / ~55 HIGH OS CVEs with "no fix" status;
# Wolfi ships them patched → OS layer scans clean (trivy CRITICAL/HIGH = 0).

# ── Builder stage: compile wheels into a self-contained venv ──────────────
FROM cgr.dev/chainguard/wolfi-base:latest AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apk add --no-cache python-3.11 python-3.11-dev build-base

COPY ./bot/requirements.txt /tmp/requirements.txt

RUN python3.11 -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/venv/bin/pip install -r /tmp/requirements.txt \
    && /opt/venv/bin/pip check \
    # Build tooling is not needed at runtime and vendors its own (vulnerable)
    # copies of urllib3/msgpack/setuptools → strip it from the shipped venv.
    && /opt/venv/bin/pip uninstall -y wheel setuptools \
    && /opt/venv/bin/python -m pip uninstall -y pip

# ── Runtime stage: python + tini only, no compilers ───────────────────────
FROM cgr.dev/chainguard/wolfi-base:latest AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:$PATH"

# libstdc++: needed by manylinux wheels (numpy, rapidfuzz); tzdata for local time
RUN apk upgrade --no-cache \
    && apk add --no-cache python-3.11 libstdc++ tini tzdata

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Application code only (venv / secrets / caches excluded via .dockerignore).
COPY ./bot /app/

# tini as PID 1 for correct signal handling / zombie reaping.
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python3", "main.py"]
