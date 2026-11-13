import os
from colorama import Fore
from aiogram import types, Bot
from aiogram.types import BufferedInputFile, InputFile
from aiogram.enums import ParseMode
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
print(f'{Fore.BLACK}BOT_TOKEN :::{Fore.BLUE} {"set" if BOT_TOKEN else "NOT SET"} {Fore.BLACK}\n');  # never log the token itself
bot = Bot(BOT_TOKEN)

async def answer(msg: types.Message, text: str, reply_markup=None, parse_mode=ParseMode.HTML, link_preview_options=None) -> types.Message:

    extra = {} if link_preview_options is None else {"link_preview_options": link_preview_options}
    return await msg.answer(text, reply_markup=reply_markup, parse_mode=parse_mode, **extra)

async def reply(msg: types.Message, text: str, reply_markup=None, parse_mode=ParseMode.HTML) -> types.Message:
    return await msg.reply(text, reply_markup=reply_markup, parse_mode=parse_mode)

async def send_message(chat_id: int, text: str, reply_markup=None, parse_mode=ParseMode.HTML) -> types.Message:
    return await bot.send_message(chat_id, text, parse_mode=parse_mode, reply_markup=reply_markup);

async def edit_message(text: str, chat_id: int, message_id: int, reply_markup=None, parse_mode=ParseMode.HTML, link_preview_options=None) -> types.Message:
    extra = {} if link_preview_options is None else {"link_preview_options": link_preview_options}
    return await bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, parse_mode=parse_mode, reply_markup=reply_markup, **extra);

async def edit_reply_markup(keyboard, chat_id, message_id):
    return await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=keyboard)

async def delete_message(chat_id, message_id):
    return await bot.delete_message(chat_id, message_id);

async def send_document(chat_id, file):
    if not isinstance(file, (InputFile, str)):
        try:
            data = file.read()
            filename = os.path.basename(getattr(file, "name", "") or "document")
        finally:
            file.close()
        file = BufferedInputFile(data, filename=filename)
    return await bot.send_document(chat_id, file);

def get_text_message(update: types.Update, callback: bool = False) -> str:
    if update.message:
        if update.message.caption:
            return update.message.caption
        return update.message.text
    elif update.channel_post:
        return update.channel_post.text
    elif callback and update.callback_query:
        return update.callback_query.message.text
    return None

def get_text_from_message(msg: types.Message) -> str:
    print(f'{Fore.BLACK}[get_text_from_message] {Fore.CYAN} {msg}{Fore.BLACK}');
    if type(msg) == str:
        return msg;
    if getattr(msg, "caption", None):
        return msg.caption
    return msg.text

def get_user_from_update(update: types.Update) -> types.User:
    if update.message:
        return update.message.from_user
    elif update.callback_query:
        return update.callback_query.from_user
    return None

def get_chat_from_update(update: types.Update) -> types.Chat:
    if update.message:
        return update.message.chat
    elif update.callback_query:
        return update.callback_query.message.chat
    elif update.channel_post:
        return update.channel_post.chat
    return None