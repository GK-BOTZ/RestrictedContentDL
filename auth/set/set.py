#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
from pyrogram import filters
from pyrogram.types import BotCommand
from pyrogram.enums import ParseMode
from config import DEVELOPER_USER_ID
from utils import LOGGER

BOT_COMMANDS = [
    BotCommand("start", "みStart Private Content Downloader Bot↯"),
    BotCommand("help", "みGet Help Menu & Commands↯"),
    BotCommand("info", "みGet User Info & Plan Info From Database↯"),
    BotCommand("plans", "みSee Available Plans & Purchase↯"),
    BotCommand("buy", "みPurchase Premium Plans With Star↯"),
    BotCommand("dl", "みDownload Restricted Content From Public Source↯"),
    BotCommand("pdl", "みDownload Restricted Content From Private Source↯"),
    BotCommand("pbdl", "みDownload Batch Media From Private Source↯"),
    BotCommand("bdl", "みDownload Batch From Public Source↯"),
    BotCommand("login", "みLogin To Account↯"),
    BotCommand("logout", "みLog Out From Account↯"),
    BotCommand("profile", "みGet Profile Info & Plan Status↯"),
    BotCommand("getthumb", "みGet Custom Thumbnail↯"),
    BotCommand("setthumb", "みSet Or Change Custom Thumbnail↯"),
    BotCommand("rmthumb", "みRemove Custom Thumbnail↯"),
]

def setup_set_handler(app):
    @app.on_message(filters.command("set") & filters.user(DEVELOPER_USER_ID))
    async def set_commands(client, message):
        await client.set_bot_commands(BOT_COMMANDS)
        await client.send_message(
            chat_id=message.chat.id,
            text="み  ¡**BotFather Commands Successfully Set**↯",
            parse_mode=ParseMode.MARKDOWN
        )
        LOGGER.info(f"BotFather commands set by owner {message.from_user.id}")