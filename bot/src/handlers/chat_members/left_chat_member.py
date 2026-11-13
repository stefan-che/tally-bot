from aiogram.types import Message, User
from colorama import Fore
from myTypes.roles import Role
from src.utils.access import getBot, getRole
from src.utils.telegram import send_message

# # USED IN MIDDLEWARE

async def left_chat_member(event: Message, member: User):
    print(Fore.BLUE+"[LEFT CHAT MEMBER EVENT]"+Fore.BLACK, event)
    
    left_member = member
    this_bot = await getBot()
    print(Fore.CYAN+"[LEFT CHAT MEMBER]\n", Fore.BLACK)

    # "BOT REMOVED"
    if left_member.id == this_bot.id:
        print(Fore.RED+"BOT IS REMOVED\n", Fore.BLACK)
    # "USER REMOVED"
    else:
        text = (await get_goodbye(left_member)).format(left_member.username)

        print(Fore.LIGHTGREEN_EX+f"GOODBYE {Fore.LIGHTYELLOW_EX}{text}\n", Fore.BLACK)
        await send_message(event.chat.id, text)

async def get_goodbye(member):
    is_owner = await getRole(member.id) == Role.OWNER
    if is_owner:
        return "<b>{}</b> (owner) has left the chat."
    return "<b>{}</b> has left the chat. Goodbye!"
