# Telegram Integration Guide

## Overview
This project includes Telegram integration for the Approval Workflow, allowing you to receive instant notifications when new draft responses are generated and approve/reject them directly from Telegram.

## Features
- 📬 Instant notifications when new drafts are created
- ✅ Inline buttons for Approve/Reject actions
- 📊 Status updates (Approved, Rejected, Published)
- 🎯 Platform-specific emojis (Instagram 📸, YouTube 🎬, TikTok 🎵)
- 🤖 AI-generated reply previews

## Setup

### 1. Create a Telegram Bot
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the instructions
3. Choose a name for your bot (e.g., "Social Media Approvals Bot")
4. Choose a username (must end with 'bot', e.g., "social_media_approvals_bot")
5. Copy the **Bot Token** provided by BotFather

### 2. Get Your Chat ID
1. Search for `@userinfobot` on Telegram
2. Start a chat with the bot
3. Your Chat ID will be displayed (e.g., `123456789`)

### 3. Configure Environment Variables
Add the following to your `.env` file:
```bash
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
TELEGRAM_ADMIN_CHAT_ID=your-chat-id-from-userinfobot
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### Automatic Notifications
When a new draft is created via the API (`POST /api/v1/approval/drafts`), the system will:
1. Save the draft to the database
2. Send a Telegram notification with:
   - Platform emoji (📸 Instagram, 🎬 YouTube, 🎵 TikTok)
   - Tenant ID
   - Original comment (truncated to 100 chars)
   - NPS category with emoji (🌟 Promoter, 😐 Neutral, 😠 Detractor)
   - AI-generated suggested reply
   - **Approve** and **Reject** buttons

### Approving/Rejecting from Telegram
1. Receive notification with inline buttons
2. Click **✅ Approve** or **❌ Reject**
3. The draft status is updated in the database
4. You receive a confirmation message

### Manual API Endpoints
You can still use the API directly:
- `POST /api/v1/approval/drafts/approve` - Approve a draft
- `POST /api/v1/approval/drafts/reject` - Reject a draft
- `POST /api/v1/approval/drafts/{draft_id}/publish` - Publish an approved draft

## Message Format Example

```
📸 New Draft Response Ready for Approval

🏢 Tenant ID: abc123-def456
💬 Comment: "This product is amazing! Best purchase ever..."
📊 NPS Category: 🌟 Promoter
🤖 Suggested Reply:
_Thank you so much for your wonderful feedback! We're thrilled that you love our product. Your support means the world to us!_

[✅ Approve] [❌ Reject]
```

## Architecture

### Components
- `api/services/telegram_notifier.py` - Main Telegram service
- `api/routers/approval.py` - Updated to include Telegram notifications
- `requirements.txt` - Added `aiogram` and `aiohttp` dependencies

### Flow
```
1. Draft created via API
2. TelegramNotifier.send_draft_notification() called
3. Message sent with inline keyboard
4. User clicks button → CallbackQuery handler
5. Draft status updated in database
6. Confirmation message sent
```

## Troubleshooting

### Bot doesn't send messages
- Check if `TELEGRAM_BOT_TOKEN` is correct
- Ensure bot has been added to the chat (if group chat)
- Verify `TELEGRAM_ADMIN_CHAT_ID` is correct

### Buttons don't work
- Check bot token permissions
- Ensure callback data format is correct
- Review logs for errors

### Messages not appearing
- Check if bot is running
- Verify network connectivity
- Check Telegram API rate limits

## Security Notes
- Never share your bot token publicly
- Use service role key for database operations
- Validate tenant IDs in all requests
- Implement rate limiting for production use

## Future Enhancements
- [ ] Support for multiple admin users
- [ ] Reply with custom notes from Telegram
- [ ] Batch approval/rejection
- [ ] Statistics and analytics in Telegram
- [ ] Support for voice messages in replies
