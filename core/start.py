# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from utils import LOGGER

def setup_start_handler(app: Client):
    @app.on_message(filters.command("start"))
    async def start(client: Client, message: Message):
        user_fullname = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
        start_message = f"""
<b>Hi {user_fullname}! Welcome To This Bot</b>
━━━━━━━━━━━━━━━━━━━
<b>PrivateContentSaver💥</b> : The ultimate toolkit on Telegram, offering public, private channels, groups, supergroups & also batch link supported!
━━━━━━━━━━━━━━━━━━━
<b>🔔 Don't Forget To <a href="https://t.me/TheSmartDev">Join Here</a> For Updates!</b>
"""
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Menu", callback_data="main_menu")]
        ])
        await message.reply_text(
            start_message,
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        LOGGER.info(f"Start command triggered by {message.from_user.id}")