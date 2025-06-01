# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
from time import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode
from pyrogram.errors import PeerIdInvalid, BadRequest
from pyleaves import Leaves
from datetime import datetime
import re
import asyncio
from utils import (
    getChatMsgID,
    processMediaGroup,
    get_parsed_msg,
    fileSizeLimit,
    progressArgs,
    send_media,
    LOGGER
)
from config import COMMAND_PREFIX
from core import prem_plan1, prem_plan2, prem_plan3, user_sessions, user_activity_collection

pbdl_data = {}
user = None

def setup_pvdl_handler(app: Client):
    async def get_batch_limits(user_id: int) -> tuple[bool, int]:
        current_time = datetime.utcnow()
        if prem_plan3.find_one({"user_id": user_id, "expiry_date": {"$gt": current_time}}):
            return True, 300  # Plan3: 300 messages
        elif prem_plan2.find_one({"user_id": user_id, "expiry_date": {"$gt": current_time}}):
            return True, 200  # Plan2: 200 messages
        elif prem_plan1.find_one({"user_id": user_id, "expiry_date": {"$gt": current_time}}):
            return True, 100  # Plan1: 100 messages
        return False, 0      # Non-premium: 0 messages

    async def is_premium_user(user_id: int) -> bool:
        current_time = datetime.utcnow()
        for plan_collection in [prem_plan1, prem_plan2, prem_plan3]:
            plan = plan_collection.find_one({"user_id": user_id})
            if plan and plan.get("expiry_date", current_time) > current_time:
                return True
        return False

    async def get_user_client(user_id: int, session_id: str) -> Client:
        global user
        user_session = user_sessions.find_one({"user_id": user_id})
        if not user_session or not user_session.get("sessions"):
            return None
        session = next((s for s in user_session["sessions"] if s["session_id"] == session_id), None)
        if not session:
            return None
        if user is not None:
            try:
                await user.stop()
            except Exception as e:
                LOGGER.error(f"Error stopping existing user client for user {user_id}: {e}")
            user = None
        try:
            user = Client(
                f"user_session_{user_id}_{session_id}",
                workers=1000,
                session_string=session["session_string"]
            )
            await user.start()
            return user
        except Exception as e:
            LOGGER.error(f"Failed to initialize user client for user {user_id}, session {session_id}: {e}")
            return None

    async def show_account_selection(client: Client, message: Message, post_url: str = None):
        user_id = message.from_user.id
        user_session = user_sessions.find_one({"user_id": user_id})
        if not user_session or not user_session.get("sessions"):
            return None

        sessions = user_session.get("sessions", [])
        if len(sessions) == 1:
            return sessions[0]["session_id"]  # Auto-select if only one account

        pbdl_data[message.chat.id] = {"post_url": post_url, "message_id": message.id, "stage": "select_account"}

        buttons = []
        for i in range(0, len(sessions), 2):
            row = []
            for session in sessions[i:i+2]:
                row.append(InlineKeyboardButton(
                    session["account_name"],
                    callback_data=f"pbdl_select_{session['session_id']}"
                ))
            buttons.append(row)
        buttons.append([InlineKeyboardButton("Cancel", callback_data="pbdl_cancel_account")])

        await message.reply_text(
            "**📤 Select an account to use for private batch download:**",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN
        )
        return None

    @app.on_message(filters.command("pbdl", prefixes=COMMAND_PREFIX) & filters.private)
    async def pbdl_command(client: Client, message: Message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        LOGGER.info(f"/pbdl command received from user {user_id}")

        # Check premium status
        if not await is_premium_user(user_id):
            await message.reply_text(
                "**❌ Only premium users can use /pbdl! Upgrade: /plans**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Non-premium user {user_id} attempted /pbdl")
            return

        # Check if user has logged-in accounts
        user_session = user_sessions.find_one({"user_id": user_id})
        if not user_session or not user_session.get("sessions"):
            await message.reply_text(
                "**❌ You must log in with /login to use /pbdl!**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"User {user_id} not logged in for /pbdl")
            return

        # Extract URL
        if len(message.command) < 2:
            await message.reply_text(
                "**❌ Please provide a valid URL! Usage: /pbdl {url}**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"No URL provided in /pbdl command by user {user_id}")
            return

        post_url = message.command[1]
        if "?" in post_url:
            post_url = post_url.split("?", 1)[0]

        # Validate URL format
        match = re.match(r"(?:https?://)?(?:t\.me|telegram\.me)/(?:c/)?([a-zA-Z0-9_]+|\d+)/(\d+)", post_url)
        if not match:
            await message.reply_text(
                "**❌ Invalid URL! Please use a valid Telegram message link (e.g., https://t.me/c/123/456)**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Invalid URL format: {post_url} by user {user_id}")
            return

        # Show account selection
        selected_session_id = await show_account_selection(client, message, post_url)
        if selected_session_id:
            await prompt_message_count(client, message, selected_session_id, post_url)

    @app.on_callback_query(filters.regex(r"^(pbdl_(select_|cancel_account|confirm|cancel)_)"))
    async def pbdl_callback_handler(client, callback_query):
        data = callback_query.data
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id
        pbdl_info = pbdl_data.get(chat_id)

        if not pbdl_info or pbdl_info["user_id"] != user_id:
            await callback_query.message.edit_text(
                "**❌ Invalid or expired batch session!**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        if data == "pbdl_cancel_account" or data.startswith("pbdl_cancel_"):
            await callback_query.message.edit_text(
                "**❌ Private batch download cancelled.**",
                parse_mode=ParseMode.MARKDOWN
            )
            if chat_id in pbdl_data:
                del pbdl_data[chat_id]
            LOGGER.info(f"Private batch download cancelled by user {user_id}")
            return

        if data.startswith("pbdl_select_"):
            session_id = data.split("_", 2)[2]
            post_url = pbdl_info.get("post_url")
            original_message_id = pbdl_info.get("message_id")

            original_message = await client.get_messages(chat_id, original_message_id)
            await callback_query.message.delete()

            await prompt_message_count(client, original_message, session_id, post_url)

        elif data.startswith("pbdl_confirm_"):
            if pbdl_info.get("stage") != "confirmed":
                await callback_query.message.edit_text(
                    "**❌ Please enter the number of messages first!**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            await process_batch_download(client, callback_query.message, pbdl_info)
            if chat_id in pbdl_data:
                del pbdl_data[chat_id]

    async def prompt_message_count(client: Client, message: Message, session_id: str, post_url: str):
        chat_id = message.chat.id
        user_id = message.from_user.id
        pbdl_data[chat_id] = {
            "user_id": user_id,
            "session_id": session_id,
            "post_url": post_url,
            "stage": "await_count"
        }
        await message.reply_text(
            "**📥 How many messages do you want to scrape?**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Confirm", callback_data=f"pbdl_confirm_{chat_id}"),
                InlineKeyboardButton("Cancel", callback_data=f"pbdl_cancel_{chat_id}")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )

    @app.on_message(filters.text & filters.create(lambda _, __, message: message.chat.id in pbdl_data and pbdl_data[message.chat.id].get("stage") == "await_count"))
    async def count_handler(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        pbdl_info = pbdl_data.get(chat_id)
        if not pbdl_info or pbdl_info["user_id"] != user_id:
            return

        try:
            count = int(message.text)
            is_premium, max_messages = await get_batch_limits(user_id)
            if not is_premium:
                await message.reply_text(
                    "**❌ Only premium users can use /pbdl! Upgrade: /plans**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            if count < 1:
                await message.reply_text(
                    "**❌ Please enter a valid number greater than 0!**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            if count > max_messages:
                await message.reply_text(
                    f"**❌ You can only scrape up to {max_messages} messages! Upgrade: /plans**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            pbdl_info["count"] = count
            pbdl_info["stage"] = "confirmed"
            await message.reply_text(
                f"**✅ You have selected {count} message{'s' if count > 1 else ''} to scrape. Press confirm to start.**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Confirm", callback_data=f"pbdl_confirm_{chat_id}"),
                    InlineKeyboardButton("Cancel", callback_data=f"pbdl_cancel_{chat_id}")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
        except ValueError:
            await message.reply_text(
                "**❌ Please enter valid integer!**",
                parse_mode=ParseMode.MARKDOWN
            )

    async def process_batch_download(bot: Client, message: Message, pbdl_info: dict):
        user_id = pbdl_info["user_id"]
        chat_id = message.chat.id
        session_id = pbdl_info["session_id"]
        post_url = pbdl_info["post_url"]
        count = pbdl_info["count"]

        user_client = await get_user_client(user_id, session_id)
        if user_client is None:
            await message.reply_text(
                "**❌ Failed to initialize user client! Please try logging in again.**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Failed to initialize user client for user {user_id}, session {session_id}")
            return

        await message.edit_text(
            "**📥 Processing private batch download...**",
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            chat_id_from_url, start_message_id = getChatMsgID(post_url)
            message_ids = list(range(start_message_id, start_message_id + count))
            messages = await user_client.get_messages(chat_id=chat_id_from_url, message_ids=message_ids)

            user_data = user_activity_collection.find_one({"user_id": user_id})
            thumbnail_path = user_data.get("thumbnail_path") if user_data else None

            for chat_message in messages:
                if not chat_message:
                    continue

                LOGGER.info(f"Downloading media from message ID {chat_message.id} for user {user_id}")

                if chat_message.document or chat_message.video or chat_message.audio:
                    file_size = (
                        chat_message.document.file_size if chat_message.document else
                        chat_message.video.file_size if chat_message.video else
                        chat_message.audio.file_size
                    )
                    if not await fileSizeLimit(file_size, message, "download", True):
                        continue

                parsed_caption = await get_parsed_msg(chat_message.caption or "", chat_message.caption_entities)
                parsed_text = await get_parsed_msg(chat_message.text or "", chat_message.entities)

                if chat_message.media_group_id:
                    if not await processMediaGroup(chat_message, bot, message):
                        await bot.send_message(
                            chat_id=chat_id,
                            text="**❌ Could not extract any valid media from the media group.**",
                            parse_mode=ParseMode.MARKDOWN
                        )
                    continue

                elif chat_message.media:
                    start_time = time()
                    progress_message = await bot.send_message(
                        chat_id=chat_id,
                        text="**📥 Downloading Progress...**",
                        parse_mode=ParseMode.MARKDOWN
                    )

                    media_path = await chat_message.download(
                        progress=Leaves.progress_for_pyrogram,
                        progress_args=progressArgs("📥 Downloading Progress", progress_message, start_time)
                    )

                    LOGGER.info(f"Downloaded media: {media_path} for user {user_id}")

                    media_type = (
                        "photo" if chat_message.photo else
                        "video" if chat_message.video else
                        "audio" if chat_message.audio else
                        "document"
                    )
                    await send_media(
                        bot,
                        message,
                        media_path,
                        media_type,
                        parsed_caption,
                        progress_message,
                        start_time,
                        thumbnail_path=thumbnail_path
                    )

                    if os.path.exists(media_path):
                        os.remove(media_path)
                    await progress_message.delete()

                elif chat_message.text or chat_message.caption:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=parsed_text or parsed_caption,
                        parse_mode=ParseMode.MARKDOWN
                    )

                await asyncio.sleep(0.5)  # Prevent rate-limiting

            completion_msg = await bot.send_message(
                chat_id=chat_id,
                text="**✅ Batch process completed successfully.**",
                parse_mode=ParseMode.MARKDOWN
            )
            try:
                await bot.pin_chat_message(chat_id, completion_msg.id, both_sides=True)
            except Exception as e:
                LOGGER.warning(f"Failed to pin completion message for user {user_id}: {e}")

            LOGGER.info(f"Private batch download completed for user {user_id}: {count} messages from {post_url}")

        except (PeerIdInvalid, BadRequest):
            await bot.send_message(
                chat_id=chat_id,
                text="**❌ Make sure logged in user client is part of the channel.**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error(f"User {user_id} not part of chat for URL: {post_url}")
        except Exception as e:
            await bot.send_message(
                chat_id=chat_id,
                text=f"**❌ Error processing batch download: {str(e)}**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error(f"Failed to process batch download for user {user_id}: {e}")
        finally:
            if user:
                try:
                    await user.stop()
                except Exception as e:
                    LOGGER.error(f"Error stopping user client for user {user_id}: {e}")

    app.add_handler(app.on_message, group=1)
    app.add_handler(app.on_callback_query, group=2)