# API Reference

The base URL depends on the deployment configuration. All endpoints except `/health` require authentication.

## Authentication

Send the `X-API-KEY` header with the token set in the `API_TOKEN` environment variable.

```
X-API-KEY: <token>
```

If `ALLOWED_IPS` is set, requests are accepted only from the listed IP addresses (comma-separated). The client IP is taken from the `X-Forwarded-For` header, or from `request.remote`.

---

## GET /health

Service health check. Does not require authentication.

**Response `200`**
```json
{
  "status": "ok"
}
```

---

## GET /api/groups

Paginated list of groups.

**Query parameters**

| Parameter  | Type    | Default | Description                        |
|------------|---------|---------|------------------------------------|
| `page`     | integer | `1`     | Page number (≥ 1)                  |
| `per_page` | integer | `20`    | Records per page (1–100)           |
| `tg_id`    | integer | —       | Filter by Telegram chat_id         |

**Response `200`**
```json
{
  "data": [
    {
      "id": "uuid",
      "tg_id": 123456789,
      "title": "Group title",
      "status": "ACTIVE",
      "chat_type": "supergroup"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 42,
    "total_pages": 3
  }
}
```

**Group object fields**

| Field       | Type    | Description                                         |
|-------------|---------|-----------------------------------------------------|
| `id`        | string  | Group UUID in the database                          |
| `tg_id`     | integer | Telegram chat_id                                    |
| `title`     | string  | Chat title                                          |
| `status`    | string  | Status: `ACTIVE`, `INACTIVE`, etc.                  |
| `chat_type` | string  | Chat type: `group`, `supergroup`, `channel`, etc.   |

**Errors**

| Code | Description                                          |
|------|------------------------------------------------------|
| 400  | `page`/`per_page` are not integers, or `tg_id` is not an integer |
| 401  | Missing or invalid `X-API-KEY`                       |
| 403  | IP address is not in `ALLOWED_IPS`                   |
| 500  | Internal server error                                |

---

## GET /api/accounts

Paginated list of accounts. Supports filtering by user and group.

**Query parameters**

| Parameter  | Type    | Default | Description                           |
|------------|---------|---------|---------------------------------------|
| `page`     | integer | `1`     | Page number (≥ 1)                     |
| `per_page` | integer | `20`    | Records per page (1–100)              |
| `user_id`  | integer | —       | Filter by Telegram user_id            |
| `group_id` | string  | —       | Filter by group UUID                  |

**Response `200`**
```json
{
  "data": [
    {
      "id": "uuid",
      "group_id": "uuid",
      "user_id": 123456789,
      "name": "Main",
      "currency": "usdt",
      "amount": 1500.50,
      "decimal": 2,
      "wallets": [
        {"id": "uuid", "wallet_address": "TRx...", "network": "tron", "balance": 0.0},
        {"id": "uuid", "wallet_address": "TRy...", "network": "tron", "balance": 0.0}
      ]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 5,
    "total_pages": 1
  }
}
```

**Account object fields**

| Field      | Type    | Description                                          |
|------------|---------|------------------------------------------------------|
| `id`       | string  | Account UUID                                         |
| `group_id` | string  | UUID of the group the account belongs to             |
| `user_id`  | integer | Telegram user_id of the owner                        |
| `name`     | string  | Account name (up to 32 characters)                   |
| `currency` | string  | Account currency, lowercase (up to 32 characters)    |
| `amount`   | float   | Current balance                                      |
| `decimal`  | integer | Number of decimal places                             |
| `wallets`  | array   | Linked wallets (may be empty)                        |

**Wallet object fields**

| Field            | Type   | Description                                     |
|------------------|--------|-------------------------------------------------|
| `id`             | string | Wallet UUID                                     |
| `wallet_address` | string | Wallet address (up to 64 characters)            |
| `network`        | string | Wallet network (default `tron`)                 |
| `balance`        | float  | Wallet balance (sum of blockchain transactions) |

Results are sorted by `amount` in descending order.

**Errors**

| Code | Description                                           |
|------|-------------------------------------------------------|
| 400  | `page`/`per_page` are not integers, or `user_id` is not an integer |
| 401  | Missing or invalid `X-API-KEY`                        |
| 403  | IP address is not in `ALLOWED_IPS`                    |
| 500  | Internal server error                                 |

---

## POST /api/accounts/{id}/wallets

Add a wallet address to an account. Idempotent: if the address is already linked, returns `200` with the existing object; if a new one is added, returns `201`.

**Path parameters**

| Parameter | Type   | Description  |
|-----------|--------|--------------|
| `id`      | string | Account UUID |

**Request body** `Content-Type: application/json`

```json
{
  "wallet_address": "TRx...",
  "network": "tron"
}
```

**Body fields**

| Field            | Type   | Description                                                      |
|------------------|--------|------------------------------------------------------------------|
| `wallet_address` | string | Wallet address (up to 64 characters), required                   |
| `network`        | string | Wallet network (up to 32 characters), optional; default `tron`   |

**Response `200` / `201`**
```json
{
  "id": "uuid",
  "account_id": "uuid",
  "wallet_address": "TRx...",
  "network": "tron"
}
```

| Status | Meaning                                        |
|--------|------------------------------------------------|
| `201`  | Wallet added                                   |
| `200`  | Wallet already exists, no duplicate created    |

**Errors**

| Code | Description                                                  |
|------|--------------------------------------------------------------|
| 400  | `id` is not a UUID                                           |
| 400  | Invalid JSON in the request body                             |
| 400  | `wallet_address` is missing from the body                    |
| 400  | `wallet_address` is not a string                             |
| 400  | `wallet_address` is longer than 64 characters                |
| 401  | Missing or invalid `X-API-KEY`                               |
| 403  | IP address is not in `ALLOWED_IPS`                           |
| 404  | Account with the given `id` not found                        |
| 500  | Internal server error                                        |

---

## DELETE /api/accounts/{id}/wallets/{wallet_id}

Delete a specific wallet from an account.

**Path parameters**

| Parameter   | Type   | Description  |
|-------------|--------|--------------|
| `id`        | string | Account UUID |
| `wallet_id` | string | Wallet UUID  |

**Response `204`** — empty body.

**Errors**

| Code | Description                                      |
|------|--------------------------------------------------|
| 400  | `id` or `wallet_id` is not a UUID                |
| 401  | Missing or invalid `X-API-KEY`                   |
| 403  | IP address is not in `ALLOWED_IPS`               |
| 404  | Wallet with the given `wallet_id` not found      |
| 500  | Internal server error                            |
