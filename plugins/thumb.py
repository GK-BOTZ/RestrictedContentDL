# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode
from config import COMMAND_PREFIX
from utils import LOGGER
from pyrogram.handlers import MessageHandler
from core import user_activity_collection

def setup_thumb_handler(app: Client):
    async def setthumb_command(client: Client, message: Message):
        user_id = message.from_user.id
        if not message.reply_to_message or not message.reply_to_message.photo:
            await message.reply_text(
                "**Kindly reply to a photo to set it as default thumbnail**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        photo = message.reply_to_message.photo
        # Ensure Assets directory exists
        os.makedirs("Assets", exist_ok=True)
        # Define thumbnail path
        thumb_path = f"Assets/{user_id}_thumb.jpg"
        # Download the thumbnail
        try:
            await client.download_media(
                photo.file_id,
                file_name=thumb_path
            )
            # Store the thumbnail path in user_activity_collection
            user_activity_collection.update_one(
                {"user_id": user_id},
                {"$set": {"thumbnail_path": thumb_path}},
                upsert=True
            )
            await message.reply_text(
                "**✅ Thumbnail set successfully!**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.info(f"Thumbnail set for user {user_id} at {thumb_path}")
        except Exception as e:
            await message.reply_text(
                "**❌ Error setting thumbnail!**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error(f"Error setting thumbnail for user {user_id}: {e}")

    async def rmthumb_command(client: Client, message: Message):
        user_id = message.from_user.id
        user_data = user_activity_collection.find_one({"user_id": user_id})
        if not user_data or "thumbnail_path" not in user_data:
            await message.reply_text(
                "**❌ You don't have any thumbnail to delete**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        thumb_path = user_data["thumbnail_path"]
        try:
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
            user_activity_collection.update_one(
                {"user_id": user_id},
                {"$unset": {"thumbnail_path": ""}}
            )
            await message.reply_text(
                "**✅ Thumbnail removed successfully!**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.info(f"Thumbnail removed for user {user_id}")
        except Exception as e:
            await message.reply_text(
                "**❌ Error removing thumbnail!**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error(f"Error removing thumbnail for user {user_id}: {e}")

    async def getthumb_command(client: Client, message: Message):
        user_id = message.from_user.id
        user_data = user_activity_collection.find_one({"user_id": user_id})
        if not user_data or "thumbnail_path" not in user_data:
            await message.reply_text(
                "**❌ Sorry, you don't have any thumbnail set**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        thumb_path = user_data["thumbnail_path"]
        if os.path.exists(thumb_path):
            try:
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=thumb_path,
                    caption="**✅ Your current thumbnail**",
                    parse_mode=ParseMode.MARKDOWN
                )
                LOGGER.info(f"Thumbnail retrieved for user {user_id}")
            except Exception as e:
                await message.reply_text(
                    "**❌ Error retrieving thumbnail!**",
                    parse_mode=ParseMode.MARKDOWN
                )
                LOGGER.error(f"Error retrieving thumbnail for user {user_id}: {e}")
        else:
            await message.reply_text(
                "**❌ Thumbnail file missing! Please set a new one.**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error(f"Thumbnail file missing for user {user_id} at {thumb_path}")

    app.add_handler(
        MessageHandler(
            setthumb_command,
            filters=filters.command("setthumb", prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        ),
        group=1
    )
    app.add_handler(
        MessageHandler(
            rmthumb_command,
            filters=filters.command("rmthumb", prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        ),
        group=1
    )
    app.add_handler(
        MessageHandler(
            getthumb_command,
            filters=filters.command("getthumb", prefixes=COMMAND_PREFIX) & (filters.private | filters.group)
        ),
        group=1
    )