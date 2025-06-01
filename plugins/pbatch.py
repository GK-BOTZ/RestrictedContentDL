# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode, ChatType
from pyrogram.errors import ChannelInvalid, ChannelPrivate, PeerIdInvalid, FileReferenceExpired
from config import COMMAND_PREFIX
from utils import LOGGER
from core import daily_limit, prem_plan1, prem_plan2, prem_plan3, user_activity_collection
from datetime import datetime
import re
import asyncio

batch_data = {}

def setup_pbatch_handler(app: Client):
    async def get_batch_limits(user_id: int) -> tuple[bool, int]:
        current_time = datetime.utcnow()
        if prem_plan3.find_one({"user_id": user_id, "expiry_date": {"$gt": current_time}}):
            return True, 10000  # Plan3: 10000 messages
        elif prem_plan2.find_one({"user_id": user_id, "expiry_date": {"$gt": current_time}}):
            return True, 5000   # Plan2: 5000 messages
        elif prem_plan1.find_one({"user_id": user_id, "expiry_date": {"$gt": current_time}}):
            return True, 2000   # Plan1: 2000 messages
        return False, 10        # Free user: 10 messages

    async def is_premium_user(user_id: int) -> bool:
        current_time = datetime.utcnow()
        for plan_collection in [prem_plan1, prem_plan2, prem_plan3]:
            plan = plan_collection.find_one({"user_id": user_id})
            if plan and plan.get("expiry_date", current_time) > current_time:
                return True
        return False

    @app.on_message(filters.command("bdl", prefixes=COMMAND_PREFIX) & filters.private)
    async def bdl_command(client: Client, message: Message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        LOGGER.info(f"/bdl command received from user {user_id}")

        # Extract URL from command
        if len(message.command) < 2:
            await message.reply_text(
                "**❌ Please Provide A Valid URL! Useage: /bdl {url}**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"No URL provided in /bdl command by user {user_id}")
            return

        url = message.command[1]
        # Handle t.me and telegram.me URLs
        match = re.match(r"(?:https?://)?(?:t\.me|telegram\.me)/(?:c/)?([a-zA-Z0-9_]+)/(\d+)", url)
        if not match:
            await message.reply_text(
                "**❌ Sorry Invalid URL Provided**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Invalid URL format: {url} by user {user_id}")
            return

        channel_username, message_id = match.groups()
        message_id = int(message_id)
        is_private = "c/" in url

        # Check if it's a private link
        if is_private:
            await message.reply_text(
                "**🚨 Private Links Detected & They Require Premium Plan & Login Kindly Use /plans To Upgrade**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Private link {url} attempted by user {user_id} without login")
            return

        # Handle public links
        if not channel_username.startswith("@"):
            channel_username = f"@{channel_username}"

        # Check channel accessibility
        try:
            chat = await client.get_chat(channel_username)
            if chat.type not in [ChatType.CHANNEL, ChatType.SUPERGROUP]:
                await message.reply_text(
                    "**❌ This Command Only Can DL From Channel & Group!**",
                    parse_mode=ParseMode.MARKDOWN
                )
                LOGGER.error(f"Invalid chat type for {channel_username}: {chat.type}")
                return
        except (ChannelInvalid, PeerIdInvalid, ChannelPrivate):
            await message.reply_text(
                "**❌ Invalid Media Link Provided Or Media Private**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error(f"Invalid or private channel: {channel_username}")
            return
        except Exception as e:
            await message.reply_text(
                "**❌ Error Accessing The Channel Kindly Check The URL.**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error(f"Failed to fetch chat {channel_username}: {e}")
            return

        # Prompt for number of messages
        batch_data[chat_id] = {
            "user_id": user_id,
            "channel_username": channel_username,
            "start_message_id": message_id,
            "stage": "await_count"
        }
        await message.reply_text(
            "**📥 How Many Messages You Want To Scrape?**",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Confirm", callback_data=f"bdl_confirm_{chat_id}"),
                InlineKeyboardButton("Cancel", callback_data=f"bdl_cancel_{chat_id}")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )

    @app.on_message(filters.text & filters.create(lambda _, __, message: message.chat.id in batch_data and batch_data[message.chat.id].get("stage") == "await_count"))
    async def count_handler(client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        batch_info = batch_data.get(chat_id)
        if not batch_info or batch_info["user_id"] != user_id:
            return

        try:
            count = int(message.text)
            is_premium, max_messages = await get_batch_limits(user_id)
            if count < 1:
                await message.reply_text(
                    "**❌Please Enter A Valid Integer Greater Than 0!**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            if count > max_messages:
                await message.reply_text(
                    f"**❌ You Can Only Scrape{max_messages} Messages! {'ᴜᴘɢʀᴀᴅᴇ: /plans' if not is_premium else ''}**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            batch_info["count"] = count
            batch_info["stage"] = "confirmed"
            await message.reply_text(
                f"**✅ You Have Selected {count}Message{'s' if count > 1 else ''} To Scrape Press Confirm To Start**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Confirm", callback_data=f"bdl_confirm_{chat_id}"),
                    InlineKeyboardButton("Cancel", callback_data=f"bdl_cancel_{chat_id}")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
        except ValueError:
            await message.reply_text(
                "**❌ Please Provide A Valid Integer!**",
                parse_mode=ParseMode.MARKDOWN
            )

    @app.on_callback_query(filters.regex(r"^bdl_(confirm|cancel)_(\d+)$"))
    async def bdl_callback_handler(client, callback_query):
        data = callback_query.data
        chat_id = int(data.split("_")[2])
        user_id = callback_query.from_user.id
        batch_info = batch_data.get(chat_id)

        if not batch_info or batch_info["user_id"] != user_id:
            await callback_query.message.edit_text(
                "**❌ Invalid Or Expired Batch Session Bro !**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        if data.startswith("bdl_cancel_"):
            await callback_query.message.edit_text(
                "**❌Batch Restricted Content DL Cancelled**",
                parse_mode=ParseMode.MARKDOWN
            )
            del batch_data[chat_id]
            LOGGER.info(f"Batch download cancelled by user {user_id}")
            return

        if data.startswith("bdl_confirm_"):
            if batch_info.get("stage") != "confirmed":
                await callback_query.message.edit_text(
                    "**❌ Please Enter The Message Number Fast!**",
                    parse_mode=ParseMode.MARKDOWN
                )
                return

            channel_username = batch_info["channel_username"]
            start_message_id = batch_info["start_message_id"]
            count = batch_info["count"]
            is_premium = await is_premium_user(user_id)

            # Update daily limit
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            if not is_premium:
                user_limit = daily_limit.find_one({"user_id": user_id})
                downloads = user_limit.get("downloads", 0) if user_limit and user_limit.get("date") >= today else 0
                if downloads + count > 10:
                    await callback_query.message.edit_text(
                        f"**🚫 Daily Limits 10 Downloads Will Be Exceeded! Upgrade To Premium: /plans**",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    del batch_data[chat_id]
                    LOGGER.info(f"Daily limit exceeded for user {user_id}")
                    return
                daily_limit.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {"downloads": downloads + count, "date": today},
                        "$inc": {"total_downloads": count}
                    },
                    upsert=True
                )
            else:
                daily_limit.update_one(
                    {"user_id": user_id},
                    {"$inc": {"total_downloads": count}},
                    upsert=True
                )

            # Process batch download
            await callback_query.message.edit_text(
                "**📥 Processing Batch Download...**",
                parse_mode=ParseMode.MARKDOWN
            )

            try:
                # Fetch messages (start_message_id to start_message_id + count - 1)
                message_ids = list(range(start_message_id, start_message_id + count))
                messages = await client.get_messages(channel_username, message_ids)

                user_data = user_activity_collection.find_one({"user_id": user_id})
                thumbnail_file_id = user_data.get("thumbnail_file_id") if user_data else None

                for source_message in messages:
                    if not source_message:
                        continue

                    if source_message.video:
                        try:
                            if thumbnail_file_id:
                                try:
                                    test_photo = await client.send_photo(
                                        chat_id=user_id,
                                        photo=thumbnail_file_id,
                                        caption="**Validating thumbnail...**",
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                                    await test_photo.delete()
                                except Exception as e:
                                    thumbnail_file_id = None
                                    LOGGER.warning(f"Invalid thumbnail file_id for user {user_id}: {e}")
                                    await client.send_message(
                                        chat_id=chat_id,
                                        text="**⚠️Sorry Thumbnail Not Found Use /setthumb**",
                                        parse_mode=ParseMode.MARKDOWN
                                    )

                            await client.send_video(
                                chat_id=chat_id,
                                video=source_message.video.file_id,
                                caption=source_message.caption or "",
                                parse_mode=ParseMode.MARKDOWN if source_message.caption else None,
                                thumb=thumbnail_file_id if thumbnail_file_id else None
                            )
                            LOGGER.info(f"Sent video with {'custom' if thumbnail_file_id else 'default'} thumbnail for user {user_id}")
                        except FileReferenceExpired:
                            await client.send_video(
                                chat_id=chat_id,
                                video=source_message.video.file_id,
                                caption=source_message.caption or "",
                                parse_mode=ParseMode.MARKDOWN if source_message.caption else None
                            )
                            await client.send_message(
                                chat_id=chat_id,
                                text="**⚠️Sorry Thumbnail Not Found Use /setthumb**",
                                parse_mode=ParseMode.MARKDOWN
                            )
                            LOGGER.info(f"Sent video with default thumbnail for user {user_id} due to expired thumbnail")
                        except Exception as e:
                            await client.send_video(
                                chat_id=chat_id,
                                video=source_message.video.file_id,
                                caption=source_message.caption or "",
                                parse_mode=ParseMode.MARKDOWN if source_message.caption else None
                            )
                            await client.send_message(
                                chat_id=chat_id,
                                text="**Using Default Thumbnail**",
                                parse_mode=ParseMode.MARKDOWN
                            )
                            LOGGER.info(f"Sent video with default thumbnail for user {user_id} due to error: {e}")
                    else:
                        await client.copy_message(
                            chat_id=chat_id,
                            from_chat_id=channel_username,
                            message_id=source_message.id
                        )

                    await asyncio.sleep(0.5)  # Prevent rate-limiting

                # Send and pin completion message
                completion_msg = await client.send_message(
                    chat_id=chat_id,
                    text="**✅ Batch Process Completed Successfully**",
                    parse_mode=ParseMode.MARKDOWN
                )
                try:
                    await client.pin_chat_message(chat_id, completion_msg.id, both_sides=True)
                except Exception as e:
                    LOGGER.warning(f"Failed to pin completion message for user {user_id}: {e}")

                del batch_data[chat_id]
                LOGGER.info(f"Batch download completed for user {user_id}: {count} messages from {channel_username}")

            except Exception as e:
                await client.send_message(
                    chat_id=chat_id,
                    text=f"**❌Error Processing Batch DL {str(e)}**",
                    parse_mode=ParseMode.MARKDOWN
                )
                del batch_data[chat_id]
                LOGGER.error(f"Failed to process batch download for user {user_id}: {e}")

    app.add_handler(app.on_message, group=1)
    app.add_handler(app.on_callback_query, group=2)