## RestrictedContentDL 🌟

A powerful Telegram bot for downloading and managing content from restricted public and private Telegram channels and groups. Built with Pyrofork, it supports seamless deployment on Heroku, VPS, or Docker, offering robust features for media scraping and user management. 💥

---

## Features 🌟

- **Public & Private Content Download**: Download media from public (`/dl`) and private (`/pdl`) restricted Telegram sources. ➕
- **Batch Downloading**: Efficiently download multiple media files from public (`/bdl`) and private (`/pbdl`) channels or groups. 📈
- **Custom Thumbnail Support**: Set (`/setthumb`), view (`/getthumb`), or remove (`/rmthumb`) custom thumbnails for media downloads. ⚙️
- **Premium Plan Management**: Explore plans (`/plans`), purchase (`/buy`), and check account status (`/profile`, `/info`). 💥
- **Admin Controls**: Broadcast messages (`/acast`, `/gcast`), manage logs (`/logs`), restart the bot (`/restart`, `/reload`, `/reboot`), view stats (`/stats`), and manage premium users (`/add`, `/rm`). 🌐
- **Dynamic Command Prefixes**: Supports multiple prefixes (`!`, `.`, `#`, `,`, `/`) for flexible command execution. ➕
- **Secure Login/Logout**: Premium users can log in (`/login`) to scrape private messages and log out (`/logout`) to clear data. 💀
- **BotFather Command Customization**: Owners can set commands using `/set` within the bot. ⚙️
- **Multi-Platform Deployment**: Deploy effortlessly on Heroku, VPS, or Docker Compose with clear setup instructions. 🌐

---

## Commands 📈

| Command    | Description                                      | Access         |
|------------|--------------------------------------------------|----------------|
| `/start`   | Start the Private Content Forwarder              | All Users ✅    |
| `/help`    | Get help about commands                          | All Users ✅    |
| `/plans`   | Discover premium plans to unlock advanced features| All Users ✅    |
| `/buy`     | Purchase a premium plan for enhanced access      | All Users ✅    |
| `/profile` | Check account status and premium details         | All Users ✅    |
| `/getthumb`| View your custom thumbnail for media downloads   | All Users ✅    |
| `/setthumb`| Set or update a custom thumbnail for videos      | All Users ✅    |
| `/rmthumb` | Remove your custom thumbnail                     | All Users ✅    |
| `/dl`      | Download media from public restricted sources    | All Users ✅    |
| `/pdl`     | Access and download from private restricted sources | Premium Users 💥 |
| `/bdl`     | Batch download from public channels or groups    | All Users ✅    |
| `/pbdl`    | Batch download from private sources              | Premium Users 💥 |
| `/info`    | Get detailed account information                 | All Users ✅    |
| `/login`   | Log in to scrape private messages               | Premium Users 💥 |
| `/logout`  | Log out and clear your account data             | All Users ✅    |
| `/acast`   | Send broadcast                                  | Admin Only 🌐  |
| `/gcast`   | Send broadcast                                  | Admin Only 🌐  |
| `/logs`    | Get logs of the bot                             | Admin Only 🌐  |
| `/restart` | Restart the bot                                 | Admin Only 🌐  |
| `/reload`  | Restart the bot                                 | Admin Only 🌐  |
| `/reboot`  | Restart the bot                                 | Admin Only 🌐  |
| `/stats`   | View total bot users                            | Admin Only 🌐  |
| `/add`     | Add user to premium                             | Admin Only 🌐  |
| `/rm`      | Remove user from premium                        | Admin Only 🌐  |
| `/set`     | Set BotFather commands                          | Owner Only ⚙️  |

**Note**: The bot owner can customize commands using the `/set` command within the bot. ⚙️

---

## Deployment Options 🌐

### 1. Deploy on Heroku (One-Click) 💥

Deploy the bot to Heroku with a single click using the button below. Ensure you have a Heroku account and configure the environment variables as shown in the `.env` sample. ✅

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/TheSmartDevs/RestrictedContentDL)

#### Heroku CLI Deployment ➕

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/TheSmartDevs/RestrictedContentDL.git
   cd RestrictedContentDL
   ```

2. **Log in to Heroku**:
   ```bash
   heroku login
   ```

3. **Create a Heroku App**:
   ```bash
   heroku create your-app-name
   ```

4. **Set Environment Variables**:
   Configure the required variables from `sample.env`:
   ```bash
   heroku config:set API_ID=your_api_id
   heroku config:set API_HASH=your_api_hash
   heroku config:set BOT_TOKEN=your_bot_token
   heroku config:set DEVELOPER_USER_ID=your_user_id
   heroku config:set MONGO_URL=your_mongo_url
   heroku config:set DATABASE_URL=your_database_url
   heroku config:set DB_URL=your_db_url
   heroku config:set COMMAND_PREFIX="!|.|#|,|/"
   ```

5. **Deploy to Heroku**:
   ```bash
   git push heroku main
   ```

6. **Scale the Dyno**:
   ```bash
   heroku ps:scale worker=1
   ```

---

### 2. Deploy on VPS with Screen 🌐

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/TheSmartDevs/RestrictedContentDL.git
   cd RestrictedContentDL
   ```

2. **Install Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   Copy `sample.env` to `.env` and fill in the required values:
   ```bash
   cp sample.env .env
   nano .env
   ```

4. **Run the Bot with Screen**:
   ```bash
   screen -S restrictedcontentdl
   python3 -m bot
   ```

5. **Detach from Screen**:
   Press `Ctrl+A` followed by `Ctrl+D`.

6. **Stop the Bot**:
   Reattach to the session and stop:
   ```bash
   screen -r restrictedcontentdl
   Ctrl+C
   ```

---

### 3. Deploy with Docker Compose ⚙️

1. **Install Docker and Docker Compose**:
   Ensure Docker and Docker Compose are installed on your system. ✅

2. **Clone the Repository**:
   ```bash
   git clone https://github.com/TheSmartDevs/RestrictedContentDL.git
   cd RestrictedContentDL
   ```

3. **Set Up Environment Variables**:
   Copy `sample.env` to `.env` and configure the required values:
   ```bash
   cp sample.env .env
   nano .env
   ```

4. **Run the Bot**:
   ```bash
   docker compose up --build --remove-orphans
   ```

5. **Stop the Bot**:
   ```bash
   docker compose down
   ```

---

## Configuration ⚙️

The bot uses environment variables for configuration. Copy `sample.env` to `.env` and fill in the required values:

```env
# Telegram API credentials (required)
API_ID=YOUR_API_ID
API_HASH=YOUR_API_HASH
BOT_TOKEN=YOUR_BOT_TOKEN

# Admin and owner IDs
DEVELOPER_USER_ID=YOUR_USER_ID

# Database URLs 
MONGO_URL=YOUR_MONGO_URL
DATABASE_URL=YOUR_DATABASE_URL
DB_URL=YOUR_DB_URL

# Command prefixes for bot commands
COMMAND_PREFIX=!|.|#|,|/
```

For Heroku, set these variables via the Heroku dashboard or CLI as shown above. ✅

---

## Main Author 🧑‍💻

The Main Author is **Abir Arafat Chawdhury**, who led the base development of RestrictedContentDL. 🌟

- **Name**: Abir Arafat Chawdhury 🌟
- **Telegram Contact**: [@ISmartDevs](https://t.me/ISmartDevs) ✅
- **Telegram Channel**: [@TheSmartDev](https://t.me/TheSmartDev) ✅

---

## Special Thanks 💥

A special thanks to [**@TheSmartBisnu**](https://github.com/bisnuray/RestrictedContentDL) for their contributions to [**RestrictedContentDL**](https://github.com/bisnuray/RestrictedContentDL), particularly for the helper functions in [`utils.py`](https://github.com/bisnuray/RestrictedContentDL/blob/main/helpers/utils.py), which were instrumental in building this project. ✅

