# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors import ChatWriteForbidden, UserIsBlocked, InputUserDeactivated, FloodWait
from datetime import datetime, timedelta
import asyncio
from config import COMMAND_PREFIX, DEVELOPER_USER_ID
from utils import LOGGER
from core import total_users

def setup_sudo_handler(app: Client):
    async def update_user_activity(user_id: int):
        """Update or insert user activity timestamp in total_users collection."""
        current_time = datetime.utcnow()
        total_users.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "last_active": current_time}},
            upsert=True
        )

    async def get_active_users():
        """Calculate active users based on time periods."""
        current_time = datetime.utcnow()
        daily_active = total_users.count_documents({"last_active": {"$gte": current_time - timedelta(days=1)}})
        weekly_active = total_users.count_documents({"last_active": {"$gte": current_time - timedelta(days=7)}})
        monthly_active = total_users.count_documents({"last_active": {"$gte": current_time - timedelta(days=30)}})
        annual_active = total_users.count_documents({"last_active": {"$gte": current_time - timedelta(days=365)}})
        total = total_users.count_documents({})
        return daily_active, weekly_active, monthly_active, annual_active, total

    @app.on_message(filters.command("stats", prefixes=COMMAND_PREFIX) & filters.private)
    async def stats_command(client: Client, message: Message):
        user_id = message.from_user.id
        if user_id != DEVELOPER_USER_ID:
            return  # Silently ignore for non-developers

        await update_user_activity(user_id)
        LOGGER.info(f"/stats command received from developer {user_id}")

        daily_active, weekly_active, monthly_active, annual_active, total = await get_active_users()

        stats_message = (
            "**✘《 Private Content Forwarder ↯ 》**\n"
            "**✘━━━━━━━━━━━↯**\n"
            f"**✘ Daily Active: {daily_active} ↯**\n"
            f"**✘ Weekly Active: {weekly_active} ↯**\n"
            f"**✘ Monthly Active: {monthly_active} ↯**\n"
            f"**✘ Annual Active: {annual_active} ↯**\n"
            "**✘━━━━━━━━━━━↯**\n"
            f"**✘ Total Users: {total} ↯**"
        )

        await message.reply_text(stats_message, parse_mode=ParseMode.MARKDOWN)

    @app.on_message(filters.command("gcast", prefixes=COMMAND_PREFIX) & filters.private)
    async def gcast_command(client: Client, message: Message):
        user_id = message.from_user.id
        if user_id != DEVELOPER_USER_ID:
            return  # Silently ignore for non-developers

        await update_user_activity(user_id)
        LOGGER.info(f"/gcast command received from developer {user_id}")

        if not message.reply_to_message:
            await message.reply_text(
                "**❌ Please reply to a message to broadcast!**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        broadcast_message = message.reply_to_message
        start_time = datetime.utcnow()
        success_count = 0
        blocked_count = 0
        failed_count = 0
        deactivated_count = 0
        flood_wait_count = 0

        # Get all user IDs
        users = total_users.find({}, {"user_id": 1})
        user_ids = [user["user_id"] for user in users]

        # Prepare inline button for gcast
        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton("Updates Channel", url="https://t.me/TheSmartDev")
        ]])

        for target_user_id in user_ids:
            while True:
                try:
                    sent_message = await client.copy_message(
                        chat_id=target_user_id,
                        from_chat_id=user_id,
                        message_id=broadcast_message.id,
                        reply_markup=buttons,
                        parse_mode=ParseMode.MARKDOWN if broadcast_message.text or broadcast_message.caption else None
                    )
                    try:
                        await client.pin_chat_message(target_user_id, sent_message.id, both_sides=True)
                    except Exception as e:
                        LOGGER.warning(f"Failed to pin gcast message for user {target_user_id}: {e}")
                    success_count += 1
                    await asyncio.sleep(0.5)  # Prevent rate-limiting
                    break
                except FloodWait as e:
                    flood_wait_count += 1
                    wait_time = e.value + 5  # Add buffer
                    LOGGER.warning(f"FloodWait triggered for user {target_user_id} during gcast: waiting {wait_time} seconds")
                    await asyncio.sleep(wait_time)
                    continue
                except UserIsBlocked:
                    blocked_count += 1
                    LOGGER.info(f"User {target_user_id} blocked the bot during gcast")
                    break
                except InputUserDeactivated:
                    deactivated_count += 1
                    LOGGER.info(f"User {target_user_id} is deactivated during gcast")
                    break
                except Exception as e:
                    failed_count += 1
                    LOGGER.error(f"Failed to send gcast to user {target_user_id}: {e}")
                    break

        # Send report to developer
        time_taken = (datetime.utcnow() - start_time).total_seconds()
        report_message = (
            "**📢 Global Broadcast Report ↯**\n"
            "**✘━━━━━━━━━━━↯**\n"
            f"**✘ Successful: {success_count} ↯**\n"
            f"**✘ Blocked: {blocked_count} ↯**\n"
            f"**✘ Deactivated: {deactivated_count} ↯**\n"
            f"**✘ Failed: {failed_count} ↯**\n"
            f"**✘ Flood Waits: {flood_wait_count} ↯**\n"
            f"**✘ Time Taken: {int(time_taken)} seconds ↯**\n"
            "**✘━━━━━━━━━━━↯**\n"
            "**✅ Broadcast completed!**"
        )

        await client.send_message(
            chat_id=user_id,
            text=report_message,
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.info(f"Gcast completed: {success_count} successes, {blocked_count} blocked, {deactivated_count} deactivated, {failed_count} failed, {flood_wait_count} flood waits")

    @app.on_message(filters.command("acast", prefixes=COMMAND_PREFIX) & filters.private)
    async def acast_command(client: Client, message: Message):
        user_id = message.from_user.id
        if user_id != DEVELOPER_USER_ID:
            return  # Silently ignore for non-developers

        await update_user_activity(user_id)
        LOGGER.info(f"/acast command received from developer {user_id}")

        if not message.reply_to_message:
            await message.reply_text(
                "**❌ Please reply to a message to broadcast!**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        broadcast_message = message.reply_to_message
        start_time = datetime.utcnow()
        success_count = 0
        blocked_count = 0
        failed_count = 0
        deactivated_count = 0
        flood_wait_count = 0

        # Get all user IDs
        users = total_users.find({}, {"user_id": 1})
        user_ids = [user["user_id"] for user in users]

        for target_user_id in user_ids:
            while True:
                try:
                    sent_message = await client.forward_messages(
                        chat_id=target_user_id,
                        from_chat_id=user_id,
                        message_ids=broadcast_message.id
                    )
                    try:
                        await client.pin_chat_message(target_user_id, sent_message.id, both_sides=True)
                    except Exception as e:
                        LOGGER.warning(f"Failed to pin acast message for user {target_user_id}: {e}")
                    success_count += 1
                    await asyncio.sleep(0.5)  # Prevent rate-limiting
                    break
                except FloodWait as e:
                    flood_wait_count += 1
                    wait_time = e.value + 5  # Add buffer
                    LOGGER.warning(f"FloodWait triggered for user {target_user_id} during acast: waiting {wait_time} seconds")
                    await asyncio.sleep(wait_time)
                    continue
                except UserIsBlocked:
                    blocked_count += 1
                    LOGGER.info(f"User {target_user_id} blocked the bot during acast")
                    break
                except InputUserDeactivated:
                    deactivated_count += 1
                    LOGGER.info(f"User {target_user_id} is deactivated during acast")
                    break
                except Exception as e:
                    failed_count += 1
                    LOGGER.error(f"Failed to send acast to user {target_user_id}: {e}")
                    break

        # Send report to developer
        time_taken = (datetime.utcnow() - start_time).total_seconds()
        report_message = (
            "**📢 Admin Broadcast Report ↯**\n"
            "**✘━━━━━━━━━━━↯**\n"
            f"**✘ Successful: {success_count} ↯**\n"
            f"**✘ Blocked: {blocked_count} ↯**\n"
            f"**✘ Deactivated: {deactivated_count} ↯**\n"
            f"**✘ Failed: {failed_count} ↯**\n"
            f"**✘ Flood Waits: {flood_wait_count} ↯**\n"
            f"**✘ Time Taken: {int(time_taken)} seconds ↯**\n"
            "**✘━━━━━━━━━━━↯**\n"
            "**✅ Broadcast completed!**"
        )

        await client.send_message(
            chat_id=user_id,
            text=report_message,
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.info(f"Acast completed: {success_count} successes, {blocked_count} blocked, {deactivated_count} deactivated, {failed_count} failed, {flood_wait_count} flood waits")

    app.add_handler(app.on_message, group=1)