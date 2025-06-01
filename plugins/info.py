# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX
from utils import LOGGER
from core import prem_plan1, prem_plan2, prem_plan3, user_sessions, daily_limit
from pyrogram.handlers import MessageHandler

def setup_info_handler(app: Client):
    async def info_command(client: Client, message: Message):
        user_id = message.from_user.id
        user = message.from_user
        full_name = f"{user.first_name} {getattr(user, 'last_name', '')}".strip() or "Unknown"
        username = f"@{user.username}" if user.username else "@N/A"

        # Check membership status
        plan1 = prem_plan1.find_one({"user_id": user_id})
        plan2 = prem_plan2.find_one({"user_id": user_id})
        plan3 = prem_plan3.find_one({"user_id": user_id})
        membership = "free"
        if plan1:
            membership = "✨ Plan 1"
        elif plan2:
            membership = "🌟 Plan 2"
        elif plan3:
            membership = "💎 Plan 3"

        # Logged-in accounts
        session = user_sessions.find_one({"user_id": user_id})
        logged_in_accounts = 1 if session and session.get("session_string") else 0

        # Total downloads
        total_downloads = 0
        daily_record = daily_limit.find_one({"user_id": user_id})
        if daily_record:
            total_downloads = daily_record.get("total_downloads", 0)

        # Total purchased stars
        total_stars = 0
        if plan1:
            total_stars += 150
        if plan2:
            total_stars += 500
        if plan3:
            total_stars += 1000

        info_text = (
            f"<b>🆔 ID:</b> <code>{user_id}</code>\n"
            f"<b>👤 Name:</b> <code>{full_name}</code>\n"
            f"<b>📛 Username:</b> <code>{username}</code>\n"
            f"<b>🎖️ Membership:</b> <code>{membership}</code>\n"
            f"<b>🔗 Logged Accounts:</b> <code>{logged_in_accounts}</code>\n"
            f"<b>📥 Total Downloads:</b> <code>{total_downloads}</code>\n"
            f"<b>⭐ Total Stars:</b> <code>{total_stars}</code>"
        )

        await message.reply_text(info_text, parse_mode=ParseMode.HTML)
        LOGGER.info(f"✘ Info command triggered by user ↯ {user_id}")

    async def help_command(client: Client, message: Message):
        help_text = (
            "<b>💥 ContentSaver Help Menu</b>\n"
            "<b>This bot helps you download restricted content from both public and private sources.</b>\n"
            "<b>━━━━━━━━━━━━━━━━</b>\n"
            "<b>🌟 Command Center 🌟</b>\n"
            "<b>/plans</b> - View premium plans\n"
            "<b>/buy</b> - Buy a premium plan\n"
            "<b>/profile</b> - View your profile\n"
            "<b>/getthumb</b> - Show your thumbnail\n"
            "<b>/setthumb</b> - Set a thumbnail\n"
            "<b>/rmthumb</b> - Remove thumbnail\n"
            "<b>/dl</b> - Download from public sources\n"
            "<b>/pdl</b> - Download from private sources\n"
            "<b>/bdl</b> - Batch download (public)\n"
            "<b>/pbdl</b> - Batch download (private)\n"
            "<b>/info</b> - Account info\n"
            "<b>/login</b> - Login for premium\n"
            "<b>/logout</b> - Logout and clear data\n"
            "<b>━━━━━━━━━━━━━━━━</b>"
        )
        await message.reply_text(help_text, parse_mode=ParseMode.HTML)
        LOGGER.info(f"✘ Help command triggered by user ↯ {message.from_user.id}")

    app.add_handler(
        MessageHandler(
            info_command,
            filters=filters.command(["info", "profile"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        ),
        group=1
    )
    app.add_handler(
        MessageHandler(
            help_command,
            filters=filters.command("help", prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        ),
        group=1
    )