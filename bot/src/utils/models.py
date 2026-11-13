from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import datetime

def model_to_dict(obj):
    result = {}
    for key, value in obj.__dict__.items():
        if not key.startswith('_') and not callable(value):
            if isinstance(value, uuid.UUID):
                # Convert UUID to string
                result[key] = str(value)
            elif isinstance(value, datetime.datetime):
                # Convert datetime to ISO formatted string
                result[key] = value.isoformat()
            else:
                result[key] = value
    return result

def convert_arr_models_to_dict(models):
    return [model_to_dict(model) for model in models]

async def save_new_db_values(session, Model, seed):
    print()
    for data in seed:
        print(f"Adding New Data: ", data)
        user = Model(**data)
        session.add(user)

async def delete_all_values(session: AsyncSession, Model):
        delete_stmt = delete(Model)
        # Execute the delete statement
        rows = await session.execute(delete_stmt)
        print("Deleted all rows:", Model)