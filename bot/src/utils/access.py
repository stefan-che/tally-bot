import os
from myTypes.roles import Role
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()
bot = Bot(os.getenv("BOT_TOKEN"))

async def getRole(user_id: str) -> Role:
    owner_id = os.getenv("OWNER_ID")
    if str(user_id) == owner_id:
        return Role.OWNER
    else:
        return Role.USER
    
async def getBot():
    this_bot = await bot.get_me()
    print("THIS_BOT", this_bot);
    return (this_bot)