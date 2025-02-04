import os
import logging
from bot.telegram_bot import TelegramBot

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    # Get Telegram bot token from environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError(
            "Please set the TELEGRAM_BOT_TOKEN environment variable. "
            "You can get a token from @BotFather on Telegram."
        )
    
    # Initialize and run the bot
    try:
        bot = TelegramBot(token)
        logging.info("Bot initialized successfully")
        logging.info("Starting bot...")
        bot.run()
    except Exception as e:
        logging.error(f"Error running bot: {e}")
        raise

if __name__ == '__main__':
    main()
