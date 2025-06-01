# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import shutil
import asyncio
import logging
import subprocess
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import DEVELOPER_USER_ID, COMMAND_PREFIX
from utils import LOGGER

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = LOGGER

def check_session_permissions(session_file: str) -> bool:
    """Check if the session file is writable."""
    if not os.path.exists(session_file):
        logger.warning(f"Session file {session_file} does not exist")
        return True
    if not os.access(session_file, os.W_OK):
        logger.error(f"Session file {session_file} is not writable")
        try:
            os.chmod(session_file, 0o600)
            logger.info(f"Fixed permissions for {session_file}")
            return os.access(session_file, os.W_OK)
        except Exception as e:
            logger.error(f"Failed to fix permissions for {session_file}: {e}")
            return False
    return True

def setup_restart_handler(app: Client):
    """Set up handlers for restart and stop commands."""

    @app.on_message(filters.command(["restart", "reboot", "reload"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def restart(client: Client, message):
        """Handle /restart, /reboot, /reload commands to restart the bot."""
        user_id = message.from_user.id
        logger.info(f"/restart command from user {user_id}")

        try:
            response = await client.send_message(
                chat_id=message.chat.id,
                text="**✘ Restarting Restricted Content Downloader... ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
        except FloodWait as e:
            logger.warning(f"FloodWait during restart message: waiting {e.value + 5} seconds")
            await asyncio.sleep(e.value + 5)
            response = await client.send_message(
                chat_id=message.chat.id,
                text="**✘ Restarting Restricted Content Downloader... ↯**",
                parse_mode=ParseMode.MARKDOWN
            )

        if user_id != DEVELOPER_USER_ID:
            logger.info("User is not developer, sending restricted message")
            try:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Unauthorized! Only the Developer Can Restart! ↯**",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✘ Updates Channel ↯", url="https://t.me/TheSmartDevs"),
                            InlineKeyboardButton("✘ Source Code ↯", url="https://github.com/TheSmartDevs/RestrictedContentDL")
                        ]
                    ])
                )
            except FloodWait as e:
                logger.warning(f"FloodWait during unauthorized message edit: waiting {e.value + 5} seconds")
                await asyncio.sleep(e.value + 5)
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Unauthorized! Only the Developer Can Restart! ↯**",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✘ Updates Channel ↯", url="https://t.me/TheSmartDevs"),
                            InlineKeyboardButton("✘ Source Code ↯", url="https://github.com/TheSmartDevs/RestrictedContentDL")
                        ]
                    ])
                )
            return

        session_file = "RestrictedContentDL.session"
        if not check_session_permissions(session_file):
            try:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Restart Failed: Session File Not Writable! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )
            except FloodWait as e:
                logger.warning(f"FloodWait during session error message: waiting {e.value + 5} seconds")
                await asyncio.sleep(e.value + 5)
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Restart Failed: Session File Not Writable! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )
            return

        directories = ["downloads", "Assets"]
        deleted_dirs = []
        failed_dirs = []
        for directory in directories:
            try:
                if os.path.exists(directory):
                    shutil.rmtree(directory)
                    deleted_dirs.append(directory)
                    logger.info(f"Deleted directory: {directory}")
            except Exception as e:
                failed_dirs.append(directory)
                logger.error(f"Failed to delete directory {directory}: {e}")

        log_file = "botlog.txt"
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                logger.info(f"Deleted log file: {log_file}")
            except Exception as e:
                logger.error(f"Failed to delete log file {log_file}: {e}")

        start_script = "start.sh"
        if not os.path.exists(start_script):
            logger.error("Start script not found")
            try:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Restart Failed: Start Script Not Found! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )
            except FloodWait as e:
                logger.warning(f"FloodWait during script error message: waiting {e.value + 5} seconds")
                await asyncio.sleep(e.value + 5)
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Restart Failed: Start Script Not Found! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )
            return

        try:
            await asyncio.sleep(4)
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**✘ Restricted Content Downloader Restarted Successfully! ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
        except FloodWait as e:
            logger.warning(f"FloodWait during success message: waiting {e.value + 5} seconds")
            await asyncio.sleep(e.value + 5)
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**✘ RestrictedDL Restarted Successfully! ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to edit restart message: {e}")
            try:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Restart Failed! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )
            except FloodWait as e:
                logger.warning(f"FloodWait during failure message: waiting {e.value + 5} seconds")
                await asyncio.sleep(e.value + 5)
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Restart Failed! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )
            return

        try:
            subprocess.run(["bash", start_script], check=True)
            os._exit(0)
        except Exception as e:
            logger.error(f"Failed to execute restart command: {e}")
            try:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Restart Failed! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )
            except FloodWait as e:
                logger.warning(f"FloodWait during final failure message: waiting {e.value + 5} seconds")
                await asyncio.sleep(e.value + 5)
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Restart Failed! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )

    @app.on_message(filters.command(["stop", "kill", "off"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
    async def stop(client: Client, message):
        """Handle /stop, /kill, /off commands to stop the bot."""
        user_id = message.from_user.id
        logger.info(f"/stop command from user {user_id}")

        try:
            response = await client.send_message(
                chat_id=message.chat.id,
                text="**✘ Stopping Restricted Content Downloader... ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
        except FloodWait as e:
            logger.warning(f"FloodWait during stop message: waiting {e.value + 5} seconds")
            await asyncio.sleep(e.value + 5)
            response = await client.send_message(
                chat_id=message.chat.id,
                text="**✘ Stopping Restricted Content Downloader... ↯**",
                parse_mode=ParseMode.MARKDOWN
            )

        if user_id != DEVELOPER_USER_ID:
            logger.info("User is not developer, sending restricted message")
            try:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Unauthorized! Only the Developer Can Stop! ↯**",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✘ Updates Channel ↯", url="https://t.me/TheSmartDevs"),
                            InlineKeyboardButton("✘ Source Code ↯", url="https://github.com/TheSmartDevs/RestrictedContentDL")
                        ]
                    ])
                )
            except FloodWait as e:
                logger.warning(f"FloodWait during unauthorized stop message: waiting {e.value + 5} seconds")
                await asyncio.sleep(e.value + 5)
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Unauthorized! Only the Developer Can Stop! ↯**",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("✘ Updates Channel ↯", url="https://t.me/TheSmartDevs"),
                            InlineKeyboardButton("✘ Source Code ↯", url="https://github.com/TheSmartDevs/RestrictedContentDL")
                        ]
                    ])
                )
            return

        directories = ["downloads", "Assets"]
        deleted_dirs = []
        failed_dirs = []
        for directory in directories:
            try:
                if os.path.exists(directory):
                    shutil.rmtree(directory)
                    deleted_dirs.append(directory)
                    logger.info(f"Deleted directory: {directory}")
            except Exception as e:
                failed_dirs.append(directory)
                logger.error(f"Failed to delete directory {directory}: {e}")

        log_file = "botlog.txt"
        if os.path.exists(log_file):
            try:
                os.remove(log_file)
                logger.info(f"Deleted log file: {log_file}")
            except Exception as e:
                logger.error(f"Failed to delete log file {log_file}: {e}")

        try:
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**✘ Restricted Content Downloader Stopped Successfully! ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
        except FloodWait as e:
            logger.warning(f"FloodWait during stop success message: waiting {e.value + 5} seconds")
            await asyncio.sleep(e.value + 5)
            await client.edit_message_text(
                chat_id=message.chat.id,
                message_id=response.id,
                text="**✘ Restricted Content Downloader Stopped Successfully! ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Failed to edit stop message: {e}")
            try:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Stop Failed! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )
            except FloodWait as e:
                logger.warning(f"FloodWait during stop failure message: waiting {e.value + 5} seconds")
                await asyncio.sleep(e.value + 5)
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Stop Failed! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )
            return

        try:
            subprocess.run(["pkill", "-f", "main.py"], check=True)
            os._exit(0)
        except Exception as e:
            logger.error(f"Failed to stop bot: {e}")
            try:
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Stop Failed! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )
            except FloodWait as e:
                logger.warning(f"FloodWait during final stop failure message: waiting {e.value + 5} seconds")
                await asyncio.sleep(e.value + 5)
                await client.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=response.id,
                    text="**❌ Stop Failed! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )