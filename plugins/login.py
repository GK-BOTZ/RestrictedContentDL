# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import os
import uuid
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid,
    MessageNotModified
)
from asyncio.exceptions import TimeoutError
import asyncio
from datetime import datetime
from config import COMMAND_PREFIX
from utils.logging_setup import LOGGER
from core import prem_plan1, prem_plan2, prem_plan3, user_sessions

# Constants for timeouts
TIMEOUT_OTP = 600  # 10 minutes
TIMEOUT_2FA = 300  # 5 minutes

session_data = {}

def setup_login_handler(app: Client):
    async def get_plan_limits(user_id: int) -> tuple[bool, int]:
        current_time = datetime.utcnow()
        if prem_plan3.find_one({"user_id": user_id, "expiry_date": {"$gt": current_time}}):
            return True, 10  # Plan3: 10 accounts
        elif prem_plan2.find_one({"user_id": user_id, "expiry_date": {"$gt": current_time}}):
            return True, 5   # Plan2: 5 accounts
        elif prem_plan1.find_one({"user_id": user_id, "expiry_date": {"$gt": current_time}}):
            return True, 1   # Plan1: 1 account
        return False, 0      # Free user: 0 accounts

    @app.on_message(filters.command("login", prefixes=COMMAND_PREFIX) & filters.private)
    async def login_command(client: Client, message: Message):
        user_id = message.from_user.id
        LOGGER.info(f"/login command received from user {user_id}")

        is_premium, max_accounts = await get_plan_limits(user_id)
        if not is_premium:
            await message.reply_text(
                "**❌ Only Premium Users Can Use /login Use /plans For Purchase Premium**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Non-premium user {user_id} attempted /login")
            return

        # Check current number of sessions
        user_session = user_sessions.find_one({"user_id": user_id}) or {"sessions": []}
        current_sessions = user_session.get("sessions", [])
        if len(current_sessions) >= max_accounts:
            await message.reply_text(
                f"**❌ You Have Reached Limit Of  {max_accounts} Accounts {'s' if max_accounts > 1 else ''}! Use /logout To Clear Data.**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"User {user_id} exceeded account limit ({max_accounts})")
            return

        session_data[message.chat.id] = {"type": "Pyrogram", "user_id": user_id}
        await client.send_message(
            chat_id=message.chat.id,
            text=(
                "**💥 Welcome to the Login SetUp!**\n"
                "**━━━━━━━━━━━━━━━━━**\n"
                "**This is a Login Module. We store your session securely in our database to keep you logged in until you use /logout.**\n\n"
                "**Note: Do not share your OTP  with anyone.**"
            ),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Start", callback_data="session_start_pyrogram"),
                InlineKeyboardButton("Close", callback_data="session_close")
            ]]),
            parse_mode=ParseMode.MARKDOWN
        )

    @app.on_message(filters.command("logout", prefixes=COMMAND_PREFIX) & filters.private)
    async def logout_command(client: Client, message: Message):
        user_id = message.from_user.id
        LOGGER.info(f"/logout command received from user {user_id}")

        is_premium, _ = await get_plan_limits(user_id)
        if not is_premium:
            await message.reply_text(
                "**❌ Only Premium Users Can Use /login Use /plans For Purchase Premium**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Non-premium user {user_id} attempted /logout")
            return

        user_session = user_sessions.find_one({"user_id": user_id})
        if not user_session or not user_session.get("sessions"):
            await message.reply_text(
                "**❌ You're Not Logged In!**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"User {user_id} not logged in for /logout")
            return

        sessions = user_session.get("sessions", [])
        if len(sessions) == 1:
            # Single account: logout directly
            user_sessions.delete_one({"user_id": user_id})
            session_file = f"temp_session_{user_id}_{sessions[0]['session_id']}.session"
            if os.path.exists(session_file):
                os.remove(session_file)
            await message.reply_text(
                f"**✅ Successfully Logout From Account '{sessions[0]['account_name']}'!**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.info(f"User {user_id} logged out of account {sessions[0]['account_name']}")
        else:
            # Multiple accounts: show selection
            buttons = []
            for i in range(0, len(sessions), 2):
                row = []
                for session in sessions[i:i+2]:
                    row.append(InlineKeyboardButton(
                        session["account_name"],
                        callback_data=f"logout_select_{session['session_id']}"
                    ))
                buttons.append(row)
            buttons.append([InlineKeyboardButton("Cancel", callback_data="session_close")])
            await message.reply_text(
                "**📤 Select Account To Logout**",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN
            )

    @app.on_callback_query(filters.regex(r"^(session_(start|restart|close)|logout_select_)"))
    async def callback_query_handler(client, callback_query):
        data = callback_query.data
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id

        if data == "session_close":
            await callback_query.message.edit_text(
                "**❌ Cancelled. You Can Restart By Using /login**",
                parse_mode=ParseMode.MARKDOWN
            )
            if chat_id in session_data:
                if session_data[chat_id].get("client_obj"):
                    try:
                        await session_data[chat_id]["client_obj"].disconnect()
                    except Exception as e:
                        LOGGER.error(f"Error disconnecting client for user {user_id}: {e}")
                del session_data[chat_id]
            return

        if data.startswith("logout_select_"):
            session_id = data.split("_", 2)[2]
            user_session = user_sessions.find_one({"user_id": user_id})
            if user_session:
                sessions = user_session.get("sessions", [])
                for session in sessions:
                    if session["session_id"] == session_id:
                        sessions.remove(session)
                        user_sessions.update_one(
                            {"user_id": user_id},
                            {"$set": {"sessions": sessions}}
                        )
                        session_file = f"temp_session_{user_id}_{session_id}.session"
                        if os.path.exists(session_file):
                            os.remove(session_file)
                        await callback_query.message.edit_text(
                            f"**✅ Successfully Logout From Account '{session['account_name']}'!**",
                            parse_mode=ParseMode.MARKDOWN
                        )
                        LOGGER.info(f"User {user_id} logged out of account {session['account_name']}")
                        break
            return

        if data.startswith("session_start_"):
            session_type = "pyrogram"
            try:
                await callback_query.message.edit_text(
                    "**Send Your API_ID**",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Restart", callback_data=f"session_restart_{session_type}"),
                        InlineKeyboardButton("Close", callback_data="session_close")
                    ]]),
                    parse_mode=ParseMode.MARKDOWN
                )
                session_data[chat_id] = {"type": "Pyrogram", "user_id": user_id, "stage": "api_id"}
            except MessageNotModified:
                LOGGER.debug(f"Message not modified for session_start by user {user_id}")
                session_data[chat_id] = {"type": "Pyrogram", "user_id": user_id, "stage": "api_id"}

        elif data.startswith("session_restart_"):
            session_type = "pyrogram"
            # Reset session data
            if chat_id in session_data and session_data[chat_id].get("client_obj"):
                try:
                    await session_data[chat_id]["client_obj"].disconnect()
                except Exception as e:
                    LOGGER.error(f"Error disconnecting client during restart for user {user_id}: {e}")
            session_data[chat_id] = {"type": "Pyrogram", "user_id": user_id, "stage": "api_id"}
            try:
                await callback_query.message.edit_text(
                    "**Send Your API_ID (Restarted)**",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Restart", callback_data=f"session_restart_{session_type}"),
                        InlineKeyboardButton("Close", callback_data="session_close")
                    ]]),
                    parse_mode=ParseMode.MARKDOWN
                )
            except MessageNotModified:
                LOGGER.debug(f"Message not modified for session_restart by user {user_id}")

    @app.on_message(filters.text & filters.create(lambda _, __, message: message.chat.id in session_data))
    async def text_handler(client, message: Message):
        chat_id = message.chat.id
        if chat_id not in session_data:
            return

        session = session_data[chat_id]
        stage = session.get("stage")

        if stage == "api_id":
            try:
                api_id = int(message.text)
                session["api_id"] = api_id
                await client.send_message(
                    chat_id=message.chat.id,
                    text="**Send Your API_HASH**",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("Restart", callback_data=f"session_restart_pyrogram"),
                        InlineKeyboardButton("Close", callback_data="session_close")
                    ]]),
                    parse_mode=ParseMode.MARKDOWN
                )
                session["stage"] = "api_hash"
            except ValueError:
                await message.reply_text(
                    "**❌ Invalid API_ID Please Provide A Valid Integer**",
                    parse_mode=ParseMode.MARKDOWN
                )
                LOGGER.error(f"Invalid API ID provided by user {message.from_user.id}")

        elif stage == "api_hash":
            session["api_hash"] = message.text
            await client.send_message(
                chat_id=message.chat.id,
                text="**Send Your Phone Number\n[Example: +880xxxxxxxxxx]**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data=f"session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            session["stage"] = "phone_number"

        elif stage == "phone_number":
            session["phone_number"] = message.text
            otp_message = await client.send_message(
                chat_id=message.chat.id,
                text="**💥 Sending OTP Check PM...**",
                parse_mode=ParseMode.MARKDOWN
            )
            await send_otp(client, message, otp_message)

        elif stage == "otp":
            otp = ''.join([char for char in message.text if char.isdigit()])
            session["otp"] = otp
            otp_message = await client.send_message(
                chat_id=message.chat.id,
                text="**💥 Validating OTP...**",
                parse_mode=ParseMode.MARKDOWN
            )
            await validate_otp(client, message, otp_message)

        elif stage == "2fa":
            session["password"] = message.text
            await validate_2fa(client, message)

    async def send_otp(client, message, otp_message):
        session = session_data[message.chat.id]
        api_id = session["api_id"]
        api_hash = session["api_hash"]
        phone_number = session["phone_number"]
        user_id = session["user_id"]
        session_id = str(uuid.uuid4())

        # Use file-based storage
        session_name = f"temp_session_{user_id}_{session_id}"
        client_obj = Client(session_name, api_id, api_hash)
        await client_obj.connect()

        try:
            code = await client_obj.send_code(phone_number)
            session["client_obj"] = client_obj
            session["code"] = code
            session["stage"] = "otp"
            session["session_id"] = session_id

            asyncio.create_task(handle_otp_timeout(client, message))

            await client.send_message(
                chat_id=message.chat.id,
                text="**✅ Send The OTP As Text. Please Send A Text Message Embedding The OTP Like: 'AB5 CD0 EF3 GH7 IJ6'**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data=f"session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            await otp_message.delete()
        except ApiIdInvalid:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Invalid API_ID & API_HASH Combination**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data=f"session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            await otp_message.delete()
            LOGGER.error(f"Invalid API_ID/API_HASH for user {message.from_user.id}")
        except PhoneNumberInvalid:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Sorry The Phone Number Invalid**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data=f"session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            await otp_message.delete()
            LOGGER.error(f"Invalid phone number for user {message.from_user.id}")

    async def handle_otp_timeout(client, message):
        await asyncio.sleep(TIMEOUT_OTP)
        if message.chat.id in session_data and session_data[message.chat.id].get("stage") == "otp":
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌Your OTP Has Expired**",
                parse_mode=ParseMode.MARKDOWN
            )
            if session_data[message.chat.id].get("client_obj"):
                try:
                    await session_data[message.chat.id]["client_obj"].disconnect()
                except Exception as e:
                    LOGGER.error(f"Error disconnecting client during OTP timeout for user {message.from_user.id}: {e}")
            del session_data[message.chat.id]
            LOGGER.info(f"OTP timed out for user {message.from_user.id}")

    async def validate_otp(client, message, otp_message):
        session = session_data[message.chat.id]
        client_obj = session["client_obj"]
        phone_number = session["phone_number"]
        otp = session["otp"]
        code = session["code"]

        try:
            await client_obj.sign_in(phone_number, code.phone_code_hash, otp)
            await generate_session(client, message)
            await otp_message.delete()
        except PhoneCodeInvalid:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Sorry Bro Wrong OTP**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data=f"session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            await otp_message.delete()
            LOGGER.error(f"Invalid OTP provided by user {message.from_user.id}")
        except PhoneCodeExpired:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Your OTP Has Expired**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data=f"session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            await otp_message.delete()
            LOGGER.error(f"Expired OTP for user {message.from_user.id}")
        except SessionPasswordNeeded:
            session["stage"] = "2fa"
            asyncio.create_task(handle_2fa_timeout(client, message))
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ 2FA Is Required To Login Kindly Send Your 2 FA**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data=f"session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            await otp_message.delete()
            LOGGER.info(f"2FA required for user {message.from_user.id}")

    async def handle_2fa_timeout(client, message):
        await asyncio.sleep(TIMEOUT_2FA)
        if message.chat.id in session_data and session_data[message.chat.id].get("stage") == "2fa":
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Your 2 FA Input Is Expired**",
                parse_mode=ParseMode.MARKDOWN
            )
            if session_data[message.chat.id].get("client_obj"):
                try:
                    await session_data[message.chat.id]["client_obj"].disconnect()
                except Exception as e:
                    LOGGER.error(f"Error disconnecting client during 2FA timeout for user {message.from_user.id}: {e}")
            del session_data[message.chat.id]
            LOGGER.info(f"2FA timed out for user {message.from_user.id}")

    async def validate_2fa(client, message):
        session = session_data[message.chat.id]
        client_obj = session["client_obj"]
        password = session["password"]

        try:
            await client_obj.check_password(password=password)
            await generate_session(client, message)
        except PasswordHashInvalid:
            await client.send_message(
                chat_id=message.chat.id,
                text="**❌ Invalid 2 FA Password Provided**",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Restart", callback_data=f"session_restart_pyrogram"),
                    InlineKeyboardButton("Close", callback_data="session_close")
                ]]),
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error(f"Invalid 2FA password provided by user {message.from_user.id}")

    async def generate_session(client, message):
        session = session_data[message.chat.id]
        client_obj = session["client_obj"]
        user_id = session["user_id"]
        session_id = session["session_id"]

        # Fetch account name
        user_info = await client_obj.get_me()
        account_name = f"{user_info.first_name} {user_info.last_name or ''}".strip()

        string_session = await client_obj.export_session_string()

        # Store session in user_sessions
        user_sessions.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "sessions": {
                        "session_id": session_id,
                        "session_string": string_session,
                        "account_name": account_name
                    }
                }
            },
            upsert=True
        )

        # Wait to allow background updates to complete
        await asyncio.sleep(2)
        await client_obj.disconnect()

        # Clean up temporary session file
        session_file = f"temp_session_{user_id}_{session_id}.session"
        if os.path.exists(session_file):
            os.remove(session_file)

        await client.send_message(
            chat_id=message.chat.id,
            text=f"**✅ Successfully Logout From As '{account_name}'! You Can Now User /pdl To Download Private Media**",
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.info(f"Session string generated and saved for user {user_id} as {account_name}")
        del session_data[message.chat.id]

    app.add_handler(app.on_message, group=1)
    app.add_handler(app.on_callback_query, group=2)