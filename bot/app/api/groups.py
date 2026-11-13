import traceback
from aiohttp import web
from db import session_maker
from db.query.group import get_groups_paginated

async def get_groups(request: web.Request) -> web.Response:
    try:
        page = max(1, int(request.rel_url.query.get("page", 1)))
        per_page = min(100, max(1, int(request.rel_url.query.get("per_page", 20))))
    except ValueError:
        return web.json_response({"error": "page and per_page must be integers"}, status=400)

    raw_tg_id = request.rel_url.query.get("tg_id")
    try:
        tg_id = int(raw_tg_id) if raw_tg_id is not None else None
    except ValueError:
        return web.json_response({"error": "tg_id must be an integer"}, status=400)

    try:
        async with session_maker() as session:
            groups, total = await get_groups_paginated(session, page=page, per_page=per_page, tg_id=tg_id)
    except Exception as e:
        traceback.print_exc()
        return web.json_response({"error": str(e)}, status=500)

    data = [
        {
            "id": str(g.id),
            "tg_id": g.tg_id,
            "title": g.title,
            "status": g.status,
            "chat_type": g.chat_type,
        }
        for g in groups
    ]

    total_pages = (total + per_page - 1) // per_page if total > 0 else 0

    return web.json_response({
        "data": data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    })