# Copyright @ISmartDevs
# Channel t.me/TheSmartDev
import uuid
import hashlib
import time
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.raw.functions.messages import SendMedia, SetBotPrecheckoutResults
from pyrogram.raw.types import (
    InputMediaInvoice,
    Invoice,
    DataJSON,
    LabeledPrice,
    UpdateBotPrecheckoutQuery,
    UpdateNewMessage,
    MessageService,
    MessageActionPaymentSentMe,
    PeerUser,
    PeerChat,
    PeerChannel,
    ReplyInlineMarkup,
    KeyboardButtonRow,
    KeyboardButtonBuy
)
from pyrogram.handlers import MessageHandler, CallbackQueryHandler, RawUpdateHandler
from pyrogram.enums import ParseMode
from pyrogram.errors import UserIdInvalid, UsernameInvalid, PeerIdInvalid
from config import COMMAND_PREFIX, DEVELOPER_USER_ID
from utils import LOGGER
from core import prem_plan1, prem_plan2, prem_plan3, daily_limit

# Plan configurations
PLANS = {
    "plan1": {"stars": 150, "name": "Plan Premium 1", "accounts": 1, "max_downloads": 1000, "private_support": True, "inbox_support": False},
    "plan2": {"stars": 500, "name": "Plan Premium 2", "accounts": 5, "max_downloads": 2000, "private_support": True, "inbox_support": True},
    "plan3": {"stars": 1000, "name": "Plan Premium 3", "accounts": 10, "max_downloads": "unlimited", "private_support": True, "inbox_support": True}
}

# Shared Strings and Emojis
PLAN_OPTIONS_TEXT = """
**💎 Choose your Premium Plan 💎**

**Plan Premium 1 - 150 🌟**  
• 1 Account Login  
• Validity 1 Month  
• Mass Content Downloader (Max 1000)  
• Private Chat/Channel Supported ✅  
• Private Inbox/Bot Supported ❌  

**Plan Premium 2 - 500 🌟**  
• 5 Account Login  
• Validity 1 Month  
• Mass Content Downloader (Max 2000)  
• Private Chat/Channel Supported ✅  
• Private Inbox/Bot Supported ✅  

**Plan Premium 3 - 1000 🌟**  
• 10 Account Login  
• Validity 1 Month  
• Mass Content Unlimited  
• Private Chat/Channel Supported ✅  
• Private Inbox/Bot Supported ✅  

**👉 Choose a plan to unlock these features!**
"""

PAYMENT_SUCCESS_TEXT = """
**✅ Plan Purchase Successful!**

**🎉 Thanks {0} for purchasing {1} with {2} Stars!**  
Your premium features are now active! Enjoy 🚀  

**🧾 Transaction ID: {3}**
"""

ADMIN_NOTIFICATION_TEXT = """
**🌟 New Plan Purchase!**  
**✨ From: {0} 💫**  
**⁉️ User ID: {1}**  
**🌐 Username: {2}**  
**💥 Plan: {3}**  
**🌟 Amount: {4} Stars**  
**📝 Transaction ID: {5}**
"""

INVOICE_CREATION_TEXT = "**Generating invoice for {0} Stars... Please wait ⏳**"
INVOICE_CONFIRMATION_TEXT = "**✅ Invoice for {0} Stars has been generated! Proceed to pay via the button below.**"
DUPLICATE_INVOICE_TEXT = "**🚫 Wait! Another purchase is already in progress!**"
INVOICE_FAILED_TEXT = "**❌ Invoice creation failed! Try again.**"
PAYMENT_FAILED_TEXT = "**❌ Payment declined! Contact support.**"

# Store active invoices to prevent duplicates
active_invoices = {}

def setup_plan_handler(app: Client):
    # Generate Plan Selection Buttons
    def get_plan_buttons():
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("Buy Plan 1", callback_data="buy_plan1"),
             InlineKeyboardButton("Buy Plan 2", callback_data="buy_plan2")],
            [InlineKeyboardButton("Buy Plan 3", callback_data="buy_plan3")]
        ])

    # Generate and Send Invoice
    async def generate_invoice(client: Client, chat_id: int, user_id: int, plan_key: str):
        if active_invoices.get(user_id):
            await client.send_message(chat_id, DUPLICATE_INVOICE_TEXT, parse_mode=ParseMode.MARKDOWN)
            return

        plan = PLANS[plan_key]
        amount = plan["stars"]
        plan_name = plan["name"]

        # Send loading message
        back_button = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="show_plan_options")]])
        loading_message = await client.send_message(
            chat_id,
            INVOICE_CREATION_TEXT.format(amount),
            parse_mode=ParseMode.MARKDOWN
        )

        try:
            active_invoices[user_id] = True

            # Generate unique payload
            timestamp = int(time.time())
            unique_id = str(uuid.uuid4())[:8]
            invoice_payload = f"plan_{plan_key}_{user_id}_{amount}_{timestamp}_{unique_id}"
            random_id = int(hashlib.sha256(invoice_payload.encode()).hexdigest(), 16) % (2**63)

            title = f"Purchase {plan_name}"
            description = f"Unlock premium features with {plan_name} for {amount} Stars. Enjoy {plan['accounts']} account(s), {plan['max_downloads']} downloads, and private chat support!"
            currency = "XTR"

            # Create Invoice object
            invoice = Invoice(
                currency=currency,
                prices=[LabeledPrice(label=f"⭐ {amount} Stars", amount=amount)],
                max_tip_amount=0,
                suggested_tip_amounts=[],
                recurring=False,
                test=False,
                name_requested=False,
                phone_requested=False,
                email_requested=False,
                shipping_address_requested=False,
                flexible=False
            )

            # Create InputMediaInvoice
            media = InputMediaInvoice(
                title=title,
                description=description,
                invoice=invoice,
                payload=invoice_payload.encode(),
                provider="STARS",
                provider_data=DataJSON(data="{}")
            )

            # Create ReplyInlineMarkup
            markup = ReplyInlineMarkup(
                rows=[
                    KeyboardButtonRow(
                        buttons=[
                            KeyboardButtonBuy(text=f"Buy {plan_name}")
                        ]
                    )
                ]
            )

            # Resolve peer
            peer = await client.resolve_peer(chat_id)

            # Send the invoice
            await client.invoke(
                SendMedia(
                    peer=peer,
                    media=media,
                    message="",
                    random_id=random_id,
                    reply_markup=markup
                )
            )

            # Edit loading message to confirmation
            await client.edit_message_text(
                chat_id,
                loading_message.id,
                INVOICE_CONFIRMATION_TEXT.format(amount),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_button
            )
            LOGGER.info(f"✅ Invoice sent for {plan_name} ({amount} stars) to user {user_id}")
        except Exception as e:
            LOGGER.error(f"❌ Failed to generate invoice for user {user_id}: {str(e)}")
            await client.edit_message_text(
                chat_id,
                loading_message.id,
                INVOICE_FAILED_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_button
            )
        finally:
            active_invoices.pop(user_id, None)

    # Handle /plans Command
    async def plans_command(client: Client, message: Message):
        user_id = message.from_user.id
        LOGGER.info(f"Plans command received: user: {user_id}, chat: {message.chat.id}")
        reply_markup = get_plan_buttons()
        await client.send_message(
            chat_id=message.chat.id,
            text=PLAN_OPTIONS_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

    # Handle /add Command
    async def add_premium_command(client: Client, message: Message):
        if message.from_user.id != DEVELOPER_USER_ID:
            await message.reply_text(
                "**❌ Only Admins can use this command!**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Unauthorized /add attempt by user {message.from_user.id}")
            return

        if len(message.command) != 3 or message.command[2] not in ["1", "2", "3"]:
            await message.reply_text(
                "**❌ Invalid format! Usage: /add {username/userid} {1, 2, or 3}**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Invalid /add format by admin {message.from_user.id}")
            return

        identifier = message.command[1]
        plan_number = message.command[2]
        plan_key = f"plan{plan_number}"
        target_user_id = None

        try:
            # Try resolving as user ID
            try:
                target_user_id = int(identifier)
            except ValueError:
                # Try resolving as username
                if identifier.startswith("@"):
                    identifier = identifier[1:]
                user = await client.get_users(identifier)
                target_user_id = user.id

            # Map plan number to collection
            plan_collection = {
                "plan1": prem_plan1,
                "plan2": prem_plan2,
                "plan3": prem_plan3
            }[plan_key]
            plan = PLANS[plan_key]
            expiry_date = datetime.utcnow() + timedelta(days=30)

            # Remove user from other plans
            for other_plan_key, other_collection in [
                ("plan1", prem_plan1),
                ("plan2", prem_plan2),
                ("plan3", prem_plan3)
            ]:
                if other_plan_key != plan_key:
                    other_collection.delete_one({"user_id": target_user_id})

            # Update user in the selected plan
            plan_collection.update_one(
                {"user_id": target_user_id},
                {
                    "$set": {
                        "user_id": target_user_id,
                        "plan": plan_key,
                        "plan_name": plan["name"],
                        "accounts": plan["accounts"],
                        "max_downloads": plan["max_downloads"],
                        "private_support": plan["private_support"],
                        "inbox_support": plan["inbox_support"],
                        "expiry_date": expiry_date
                    }
                },
                upsert=True
            )

            await message.reply_text(
                f"**✅ Promoted user {identifier} (ID: {target_user_id}) to {plan['name']}!**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.info(f"Promoted user {target_user_id} to {plan['name']} by admin {message.from_user.id}")

        except (UserIdInvalid, UsernameInvalid, PeerIdInvalid):
            await message.reply_text(
                f"**❌ Invalid username or user ID: {identifier}!**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error(f"Invalid user {identifier} in /add by admin {message.from_user.id}")
        except Exception as e:
            await message.reply_text(
                f"**❌ Error promoting user: {str(e)}**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error(f"Error in /add for user {identifier} by admin {message.from_user.id}: {str(e)}")

    # Handle /rm Command
    async def remove_premium_command(client: Client, message: Message):
        if message.from_user.id != DEVELOPER_USER_ID:
            await message.reply_text(
                "**❌ Only Admins can use this command!**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Unauthorized /rm attempt by user {message.from_user.id}")
            return

        if len(message.command) != 2:
            await message.reply_text(
                "**❌ Invalid format! Usage: /rm {username/userid}**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.warning(f"Invalid /rm format by admin {message.from_user.id}")
            return

        identifier = message.command[1]
        target_user_id = None

        try:
            # Try resolving as user ID
            try:
                target_user_id = int(identifier)
            except ValueError:
                # Try resolving as username
                if identifier.startswith("@"):
                    identifier = identifier[1:]
                user = await client.get_users(identifier)
                target_user_id = user.id

            # Remove user from all premium plans
            removed = False
            for plan_collection in [prem_plan1, prem_plan2, prem_plan3]:
                result = plan_collection.delete_one({"user_id": target_user_id})
                if result.deleted_count > 0:
                    removed = True

            if removed:
                await message.reply_text(
                    f"**✅ Removed user {identifier} (ID: {target_user_id}) from premium plans!**",
                    parse_mode=ParseMode.MARKDOWN
                )
                LOGGER.info(f"Removed user {target_user_id} from premium plans by admin {message.from_user.id}")
            else:
                await message.reply_text(
                    f"**❌ User {identifier} (ID: {target_user_id}) is not in any premium plan!**",
                    parse_mode=ParseMode.MARKDOWN
                )
                LOGGER.info(f"User {target_user_id} not in premium plans for /rm by admin {message.from_user.id}")

        except (UserIdInvalid, UsernameInvalid, PeerIdInvalid):
            await message.reply_text(
                f"**❌ Invalid username or user ID: {identifier}!**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error(f"Invalid user {identifier} in /rm by admin {message.from_user.id}")
        except Exception as e:
            await message.reply_text(
                f"**❌ Error removing user: {str(e)}**",
                parse_mode=ParseMode.MARKDOWN
            )
            LOGGER.error(f"Error in /rm for user {identifier} by admin {message.from_user.id}: {str(e)}")

    # Handle Callback Queries for Plan Selection
    async def handle_plan_callback(client: Client, callback_query: CallbackQuery):
        data = callback_query.data
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id

        LOGGER.info(f"Callback query received: data={data}, user: {user_id}, chat: {chat_id}")
        plan_mapping = {
            "buy_plan1": "plan1",
            "buy_plan2": "plan2",
            "buy_plan3": "plan3"
        }
        if data in plan_mapping:
            plan_key = plan_mapping[data]
            await generate_invoice(client, chat_id, user_id, plan_key)
            await callback_query.answer(f"✅ Invoice Generated for {PLANS[plan_key]['name']}!")
        elif data == "show_plan_options":
            reply_markup = get_plan_buttons()
            await client.edit_message_text(
                chat_id,
                callback_query.message.id,
                PLAN_OPTIONS_TEXT,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            await callback_query.answer()

    # Raw Update Handler for Payment Processing
    async def raw_update_handler(client: Client, update, users, chats):
        if isinstance(update, UpdateBotPrecheckoutQuery):
            try:
                await client.invoke(
                    SetBotPrecheckoutResults(
                        query_id=update.query_id,
                        success=True
                    )
                )
                LOGGER.info(f"✅ Pre-checkout query {update.query_id} OK for user {update.user_id}")
            except Exception as e:
                LOGGER.error(f"❌ Pre-checkout query {update.query_id} failed: {str(e)}")
                await client.invoke(
                    SetBotPrecheckoutResults(
                        query_id=update.query_id,
                        success=False,
                        error="Failed to process pre-checkout."
                    )
                )
        elif isinstance(update, UpdateNewMessage) and isinstance(update.message, MessageService) and isinstance(update.message.action, MessageActionPaymentSentMe):
            payment = update.message.action
            try:
                # Extract user_id and chat_id
                user_id = update.message.from_id.user_id if update.message.from_id and hasattr(update.message.from_id, 'user_id') else None
                if not user_id and users:
                    possible_user_ids = [uid for uid in users if uid > 0]
                    user_id = possible_user_ids[0] if possible_user_ids else None

                if isinstance(update.message.peer_id, PeerUser):
                    chat_id = update.message.peer_id.user_id
                elif isinstance(update.message.peer_id, PeerChat):
                    chat_id = update.message.peer_id.chat_id
                elif isinstance(update.message.peer_id, PeerChannel):
                    chat_id = update.message.peer_id.channel_id
                else:
                    chat_id = None

                if not user_id or not chat_id:
                    raise ValueError(f"Invalid chat_id ({chat_id}) or user_id ({user_id})")

                # Get user details
                user = users.get(user_id)
                full_name = f"{user.first_name} {getattr(user, 'last_name', '')}".strip() or "Unknown" if user else "Unknown"
                username = f"@{user.username}" if user and user.username else "@N/A"

                # Determine plan from payload
                payload = payment.payload.decode()
                plan_key = payload.split("_")[1]
                plan = PLANS.get(plan_key)
                if not plan:
                    raise ValueError(f"Invalid plan key in payload: {payload}")

                # Update user plan in database
                plan_collection = {
                    "plan1": prem_plan1,
                    "plan2": prem_plan2,
                    "plan3": prem_plan3
                }[plan_key]
                expiry_date = datetime.utcnow() + timedelta(days=30)

                # Remove user from other plans
                for other_plan_key, other_collection in [
                    ("plan1", prem_plan1),
                    ("plan2", prem_plan2),
                    ("plan3", prem_plan3)
                ]:
                    if other_plan_key != plan_key:
                        other_collection.delete_one({"user_id": user_id})

                plan_collection.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "user_id": user_id,
                            "plan": plan_key,
                            "plan_name": plan["name"],
                            "accounts": plan["accounts"],
                            "max_downloads": plan["max_downloads"],
                            "private_support": plan["private_support"],
                            "inbox_support": plan["inbox_support"],
                            "expiry_date": expiry_date
                        }
                    },
                    upsert=True
                )

                # Send success message to user
                await client.send_message(
                    chat_id=chat_id,
                    text=PAYMENT_SUCCESS_TEXT.format(full_name, plan["name"], payment.total_amount, payment.charge.id),
                    parse_mode=ParseMode.MARKDOWN
                )

                # Notify admins
                admin_text = ADMIN_NOTIFICATION_TEXT.format(full_name, user_id, username, plan["name"], payment.total_amount, payment.charge.id)
                for admin_id in [DEVELOPER_USER_ID] if isinstance(DEVELOPER_USER_ID, int) else DEVELOPER_USER_ID:
                    try:
                        await client.send_message(
                            chat_id=admin_id,
                            text=admin_text,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception as e:
                        LOGGER.error(f"❌ Failed to notify admin {admin_id}: {str(e)}")

                LOGGER.info(f"✅ Payment processed for user {user_id}: {plan['name']} ({payment.total_amount} Stars)")
            except Exception as e:
                LOGGER.error(f"❌ Payment processing failed for user {user_id if user_id else 'unknown'}: {str(e)}")
                if 'chat_id' in locals() and chat_id:
                    await client.send_message(
                        chat_id=chat_id,
                        text=PAYMENT_FAILED_TEXT,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📞 Support", url=f"tg://user?id={DEVELOPER_USER_ID}")]])
                    )

    # Register Handlers
    app.add_handler(
        MessageHandler(
            plans_command,
            filters = (filters.command(["plans", "buy"], prefixes=COMMAND_PREFIX) & (filters.private | filters.group))
        ),
        group=1
    )
    app.add_handler(
        MessageHandler(
            add_premium_command,
            filters=filters.command("add", prefixes=COMMAND_PREFIX) & filters.private
        ),
        group=1
    )
    app.add_handler(
        MessageHandler(
            remove_premium_command,
            filters=filters.command("rm", prefixes=COMMAND_PREFIX) & filters.private
        ),
        group=1
    )
    app.add_handler(
        CallbackQueryHandler(
            handle_plan_callback,
            filters=filters.regex(r'^(buy_plan[1-3]|show_plan_options)$')
        ),
        group=2
    )
    app.add_handler(
        RawUpdateHandler(raw_update_handler),
        group=3
    )