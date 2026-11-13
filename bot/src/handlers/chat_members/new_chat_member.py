from aiogram.types import Message, User
from colorama import Fore
from myTypes.roles import Role
from src.utils.access import getBot, getRole
from src.utils.telegram import send_message


async def new_chat_member(event: Message, member: User):
    print(Fore.BLUE+"[NEW CHAT MEMBER EVENT]"+Fore.BLACK, event)
    
    new_member = member
    
    this_bot = await getBot()
    print(Fore.CYAN+"[NEW CHAT MEMBER]\n", Fore.BLACK, new_member.id)

    # "BOT ADDED"
    if new_member.id == this_bot.id:
        print(Fore.LIGHTGREEN_EX+"BOT IS ADDED\n", Fore.BLACK)
        await send_message(event.chat.id, f"Hi everyone!\nYour chat_id: {event.chat.id}")
    # "USER ADDED" - no greeting message in chat (disabled on purpose)
    else:
        print(Fore.LIGHTGREEN_EX+f"NEW MEMBER: {Fore.LIGHTYELLOW_EX}{new_member.username} ({new_member.id})", Fore.BLACK)



async def get_greeting(member):
    is_owner = await getRole(member.id) == Role.OWNER
    if is_owner:
        return "Welcome, <b>{}</b>. The owner has joined the chat.\n"
    return "Welcome, <b>{}</b>!\n"
