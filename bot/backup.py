import json
import asyncio
from colorama import Fore
from sqlalchemy import select
from src.utils.models import convert_arr_models_to_dict
from db import session_maker, User, Account, History

async def dump_table(session, Model, filename):
    print(f"Dumping {Model.__tablename__} to {filename}")
    result = await session.execute(select(Model))
    rows = result.scalars().all()
    data = convert_arr_models_to_dict(rows)
    print(f"Dumping {len(data)} rows from {Model.__tablename__} to {filename}")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Dumped {len(data)} rows from {Model.__tablename__} to {filename}")

async def main():
    async with session_maker() as session:
        await dump_table(session, User, "users.json")
        await dump_table(session, Account, "accounts.json")
        await dump_table(session, History, "histories.json")

if __name__ == "__main__":
    asyncio.run(main())