# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from utils import LOGGER

async def handle_callback_query(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    message_id = callback_query.message.id
    user_fullname = f"{callback_query.from_user.first_name} {callback_query.from_user.last_name or ''}".strip()

    if callback_query.data == "main_menu":
        menu_message = (
            "<b>🌟 Welcome to Your Content Savior! 🌟</b>\n"
            "<b>This bot is your ultimate companion for downloading restricted content from both public and private Telegram Chats! 💥</b>\n"
            "<b>━━━━━━━━━━━━━━━━</b>\n"
            "<b>⭐️ Command Center ⭐️</b>\n"
            "<b>⭐️ /plans — Discover premium plans to unlock advanced features</b>\n"
            "<b>⭐️ /buy — Purchase a premium plan for enhanced access</b>\n"
            "<b>⭐️ /profile — Check your account status and premium details</b>\n"
            "<b>⭐️ /getthumb — View your custom thumbnail for media downloads</b>\n"
            "<b>⭐️ /setthumb — Set or update a custom thumbnail for videos</b>\n"
            "<b>💀 /rmthumb — Remove your custom thumbnail</b>\n"
            "<b>⭐️ /dl — Download media from public restricted sources</b>\n"
            "<b>💥 /pdl — Access and download from private restricted sources</b>\n"
            "<b>⭐️ /bdl — Batch download from public channels or groups</b>\n"
            "<b>💥 /pbdl — Batch download from private sources</b>\n"
            "<b>📈 /info — Get detailed account information</b>\n"
            "<b>⁉️ /login — Log in to scrape private messages (premium only)</b>\n"
            "<b>✅ /logout — Log out and clear your account data</b>\n"
            "<b>━━━━━━━━━━━━━━━━</b>"
        )
        reply_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Back", callback_data="menu_back"),
                InlineKeyboardButton("Close", callback_data="menu_close")
            ]
        ])
        try:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=menu_message,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            await callback_query.answer()
            LOGGER.info(f"Menu displayed for user {user_id}")
        except Exception as e:
            await callback_query.message.reply_text(
                "<b>❌ Error displaying menu. Please try again.</b>",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            LOGGER.error(f"Error displaying menu for user {user_id}: {e}")

    elif callback_query.data == "menu_back":
        start_message = (
            f"<b>Hi {user_fullname}! Welcome To This Bot</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━━</b>\n"
            "<b> PrivateContentSaver💥</b> <b>: The ultimate toolkit on Telegram, offering public, private channels, groups, supergroups & also batch link supported!</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━━</b>\n"
            '<b>🔔 Don\'t Forget To <a href="https://t.me/TheSmartDev">Join Here</a> For Updates!</b>'
        )
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Menu", callback_data="main_menu")]
        ])
        try:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=start_message,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            await callback_query.answer()
            LOGGER.info(f"Returned to start message for user {user_id}")
        except Exception as e:
            await callback_query.message.reply_text(
                "<b>❌ Error returning to start message. Please try again.</b>",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            LOGGER.error(f"Error returning to start message for user {user_id}: {e}")

    elif callback_query.data == "menu_close":
        try:
            await callback_query.message.delete()
            await callback_query.answer()
            LOGGER.info(f"Menu closed for user {user_id}")
        except Exception as e:
            await callback_query.message.reply_text(
                "<b>❌ Error closing menu. Please try again.</b>",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
            LOGGER.error(f"Error closing menu for user {user_id}: {e}")