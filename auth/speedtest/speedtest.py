# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import asyncio
import subprocess
import json
from concurrent.futures import ThreadPoolExecutor
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import FloodWait
from config import DEVELOPER_USER_ID, COMMAND_PREFIX
from utils import LOGGER

# Helper function to convert speed to human-readable format
def speed_convert(size: float, is_mbps: bool = False) -> str:
    if is_mbps:
        return f"{size:.2f} Mbps"
    power = 2**10
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}bps"

# Helper function to convert bytes to human-readable file size
def get_readable_file_size(size_in_bytes: int) -> str:
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    power = 1024
    n = 0
    power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    while size_in_bytes >= power:
        size_in_bytes /= power
        n += 1
    return f"{size_in_bytes:.2f} {power_labels[n]}"

# Function to perform speed test
def run_speedtest():
    try:
        # Use speedtest-cli for detailed JSON output
        result = subprocess.run(["speedtest-cli", "--secure", "--json"], capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception("Speedtest failed.")
        data = json.loads(result.stdout)
        return data
    except Exception as e:
        LOGGER.error(f"Speedtest error: {e}")
        return {"error": str(e)}

# Async function to handle speed test logic
async def run_speedtest_task(client: Client, chat_id: int, status_message: Message):
    # Run speed test in background thread
    with ThreadPoolExecutor() as pool:
        try:
            result = await asyncio.get_running_loop().run_in_executor(pool, run_speedtest)
        except Exception as e:
            LOGGER.error(f"Error running speedtest task: {e}")
            try:
                await status_message.edit_text(
                    "**❌ Speed Test API Unavailable! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )
            except FloodWait as e:
                LOGGER.warning(f"FloodWait during API error message: waiting {e.value + 5} seconds")
                await asyncio.sleep(e.value + 5)
                await status_message.edit_text(
                    "**❌ Speed Test API Unavailable! ↯**",
                    parse_mode=ParseMode.MARKDOWN
                )
            return

    if "error" in result:
        try:
            await status_message.edit_text(
                f"**❌ Speed Test Failed↯**",
                parse_mode=ParseMode.MARKDOWN
            )
        except FloodWait as e:
            LOGGER.warning(f"FloodWait during failure message: waiting {e.value + 5} seconds")
            await asyncio.sleep(e.value + 5)
            await status_message.edit_text(
                f"**❌ Speed Test Failed↯**",
                parse_mode=ParseMode.MARKDOWN
            )
        return

    # Format the results with project-themed design
    response_text = (
        "**✘《 Restricted Content Downloader Speedtest ↯ 》**\n"
        "**✘━━━━━━━━━━━━━━━━━━━━━━━↯**\n"
        f"**✘ Upload Speed:** `{speed_convert(result['upload'])}`\n"
        f"**✘ Download Speed:** `{speed_convert(result['download'])}`\n"
        f"**✘ Ping:**`{result['ping']:.2f} ms`\n"
        f"**✘ Timestamp:** `{result['timestamp']}`\n"
        f"**✘ Data Sent:** `{get_readable_file_size(int(result['bytes_sent']))}`\n"
        f"**✘ Data Received:** `{get_readable_file_size(int(result['bytes_received']))}`\n"
        "**✘《 Server Info ↯ 》**\n"
        f"**✘ Name:** `{result['server']['name']}`\n"
        f"**✘ Country:** `{result['server']['country']}, {result['server']['cc']}`\n"
        f"**✘ Sponsor:** `{result['server']['sponsor']}`\n"
        f"**✘ Latency:** `{result['server']['latency']:.2f} ms`\n"
        f"**✘ Latitude:** `{result['server']['lat']}`\n"
        f"**✘ Longitude:**`{result['server']['lon']}`\n"
        "**✘《 Client Info ↯ 》**\n"
        f"**✘ IP Address:** `{result['client']['ip']}`\n"
        f"**✘ Latitude:** `{result['client']['lat']}`\n"
        f"**✘ Longitude:** `{result['client']['lon']}`\n"
        f"**✘ Country:** `{result['client']['country']}`\n"
        f"**✘ ISP:** `{result['client']['isp']}`\n"
        f"**✘ ISP Rating:** `{result['client'].get('isprating', 'N/A')}`\n"
        "**✘━━━━━━━━━━━━━━━━━━━━━━━↯**\n"
        "**✘ Powered by @TheSmartDev ↯**"
    )

    # Create inline keyboard with Updates Channel button
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✘ Updates Channel ↯", url="https://t.me/TheSmartDevs")]
    ])

    # Delete the status message
    try:
        await status_message.delete()
    except FloodWait as e:
        LOGGER.warning(f"FloodWait during status message deletion: waiting {e.value + 5} seconds")
        await asyncio.sleep(e.value + 5)
        await status_message.delete()

    # Send the final result
    try:
        await client.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    except FloodWait as e:
        LOGGER.warning(f"FloodWait during result message: waiting {e.value + 5} seconds")
        await asyncio.sleep(e.value + 5)
        await client.send_message(
            chat_id=chat_id,
            text=response_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )

# Handler for speed test command
async def speedtest_handler(client: Client, message: Message):
    user_id = message.from_user.id
    LOGGER.info(f"/speedtest command from user {user_id}")

    if user_id != DEVELOPER_USER_ID:
        LOGGER.info("User is not developer, sending restricted message")
        try:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Kids Are Disallowed To Do This ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
        except FloodWait as e:
            LOGGER.warning(f"FloodWait during unauthorized message: waiting {e.value + 5} seconds")
            await asyncio.sleep(e.value + 5)
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Kids Are Disallowed To Do This ↯**",
                parse_mode=ParseMode.MARKDOWN
            )
        return

    # Send initial status message
    try:
        status_message = await client.send_message(
            chat_id=message.chat.id,
            text="**✘ Running Speedtest Wait ↯**",
            parse_mode=ParseMode.MARKDOWN
        )
    except FloodWait as e:
        LOGGER.warning(f"FloodWait during status message: waiting {e.value + 5} seconds")
        await asyncio.sleep(e.value + 5)
        status_message = await client.send_message(
            chat_id=message.chat.id,
            text="**✘ Running Speedtest Wait ↯**",
            parse_mode=ParseMode.MARKDOWN
        )

    # Schedule the speed test task
    asyncio.create_task(run_speedtest_task(client, message.chat.id, status_message))

# Setup function to add the speed test handler
def setup_speed_handler(app: Client):
    app.add_handler(MessageHandler(
        speedtest_handler,
        filters.command("speedtest", prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
    ))