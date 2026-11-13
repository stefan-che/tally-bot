from aiogram.enums import ParseMode
from aiogram.types import Message

async def get_help(message: Message):
    help_text = (
    "<b>Hi! 👋</b>\n"
    "<i>This bot keeps team accounts and shows exchange rates.</i>\n\n"
    
    "<b><u>Accounts:</u></b>\n\n"
    
    "<b>💰 Create an account</b>\n"
    "<code>/add [account name] [decimals]</code>\n"
    " ▪️ [decimals] — digits after the decimal point (default 0).\n\n"
    
    "<b>🗑️ Delete an account</b>\n"
    "<code>/delete [account name]</code>\n"
    "\n"
    
    "<b>➕➖ Add to / subtract from an account</b>\n"
    "<code>/[account name] [amount / formula] [comment]</code>\n"
    " ▪️ The formula must not contain spaces.\n"
    "\n\n"
    
    "<b><u>Users:</u></b>\n\n"
    
    "<b>🆔 User and chat ID</b>\n"
    "<code>/id</code>\n"
    "\n"
    
    "<b>👥 Users</b>\n"
    "<code>/users</code>\n"
    " ▪️ In a group — the group's users\n"
    " ▪️ In a private chat — all users of the system\n\n"
    
    "<b>💂‍♀️ Add a user</b>\n"
    "<code>/add_user [ID]</code>\n\n"
    
    "<b>👮‍♂️ Add an admin</b>\n"
    "<code>/add_admin [ID]</code>\n"
    " ▪️ In a group — admin of the chat\n"
    " ▪️ In a private chat — admin of the system\n\n"
    
    "<b>🗑️ Delete a user</b>\n"
    "<code>/delete_user [ID]</code>\n"
    " ▪️ In a group — removes the user from the chat\n"
    " ▪️ In a private chat — removes the user from the system\n\n"
    
    "<b>🔧 Change a role</b>\n"
    "<code>/update_role [ID] [Role]</code>\n"
    "\n\n"
    
    "<b><u>More commands:</u></b>\n\n"
    
    "<b>📚 Transaction history</b>\n"
    "<code>/history [account name]</code>\n"
    " ▪️ [account name] — optional\n\n"
    
    "<b>♻️ If an account balance is off:</b>\n"
    "<code>/update_balance [account name]</code>\n"
    " ▪️ Recalculates the account balance from its transactions.\n\n"
    
    "<b>📈 Exchange rates</b>\n"
    "<code>/rate [Coin 1]-[Coin 2] [amount]</code>\n"
    " ▪️ <b>Example:</b> <i>/rate ETH</i> or <i>/rate ETH-BTC</i>.\n"
    " ▪️ [Coin 2] — optional (default USDT).\n\n"

    # Groups
    "<b>👥 Groups</b>\n"
    "<code>/groups</code>\n"
    " ▪️ Lists the groups connected to the bot\n"
    " ▪️ With filters and sorting\n\n"
)

    await message.answer(help_text, parse_mode=ParseMode.HTML)