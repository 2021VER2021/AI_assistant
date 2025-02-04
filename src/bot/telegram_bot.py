import os
import tempfile
from typing import BinaryIO
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from database.db import get_db, init_db
from database.models import User, Chat
from ai_agent.agent import AIAgent

# Password for authentication
AUTH_PASSWORD = "12345"

class TelegramBot:
    def __init__(self, token: str):
        self.application = Application.builder().token(token).build()
        self.ai_agent = AIAgent()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("delete", self.delete_history))
        self.application.add_handler(MessageHandler(filters.Document.PDF, self.handle_pdf))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Initialize database
        init_db()

    def _get_or_create_user(self, telegram_id: int) -> User:
        """Get existing user or create new one."""
        with get_db() as db:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                user = User(telegram_id=telegram_id)
                db.add(user)
                db.commit()
            return user

    def _save_chat_message(self, user_id: int, message: str, is_bot: bool):
        """Save chat message to database."""
        with get_db() as db:
            chat = Chat(user_id=user_id, message=message, is_bot=is_bot)
            db.add(chat)
            db.commit()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command and authentication."""
        if not update.message or not update.message.text:
            return
        
        # Check if password is provided
        parts = update.message.text.split()
        if len(parts) != 2 or parts[1] != AUTH_PASSWORD:
            await update.message.reply_text(
                "Please authenticate with: /start PASSWORD"
            )
            return
        
        # Authenticate user
        user = self._get_or_create_user(update.message.from_user.id)
        with get_db() as db:
            db_user = db.query(User).filter(User.id == user.id).first()
            db_user.authenticated = True
            db.commit()
        
        await update.message.reply_text(
            "Authentication successful! You can now:\n"
            "1. Send me any question\n"
            "2. Send PDF documents for future reference"
        )

    async def handle_pdf(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle PDF document uploads."""
        if not update.message or not update.message.document:
            return
        
        user = self._get_or_create_user(update.message.from_user.id)
        
        # Check authentication
        if not user.authenticated:
            await update.message.reply_text(
                "Please authenticate first with: /start PASSWORD"
            )
            return
        
        # Download and process PDF
        doc = update.message.document
        if doc.file_size > 11 * 1024 * 1024:  # 10MB limit
            await update.message.reply_text(
                "File too large. Please send PDFs smaller than 10MB."
            )
            return
        
        await update.message.reply_text("Processing PDF...")
        
        try:
            # Download file
            file = await context.bot.get_file(doc.file_id)
            
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                await file.download_to_drive(temp_file.name)
                
                # Process PDF
                with open(temp_file.name, 'rb') as pdf_file:
                    success = await self.ai_agent.process_pdf(
                        pdf_file,
                        doc.file_name or "unnamed.pdf",
                        user.id
                    )
            
            # Clean up temp file
            os.unlink(temp_file.name)
            
            if success:
                await update.message.reply_text(
                    "PDF processed successfully! You can now ask questions about its content."
                )
            else:
                await update.message.reply_text(
                    "Error processing PDF. Please make sure it's a valid PDF file."
                )
                
        except Exception as e:
            await update.message.reply_text(f"Error processing PDF: {str(e)}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages/questions."""
        if not update.message or not update.message.text:
            return
        
        user = self._get_or_create_user(update.message.from_user.id)
        
        # Check authentication
        if not user.authenticated:
            await update.message.reply_text(
                "Please authenticate first with: /start PASSWORD"
            )
            return
        
        # Save user message
        self._save_chat_message(user.id, update.message.text, is_bot=False)
        
        # Process query
        try:
            response = await self.ai_agent.process_query(update.message.text, user.id)
            
            # Save bot response
            self._save_chat_message(user.id, response, is_bot=True)
            
            await update.message.reply_text(response)
            
        except Exception as e:
            error_message = f"Error processing your request: {str(e)}"
            await update.message.reply_text(error_message)
            self._save_chat_message(user.id, error_message, is_bot=True)

    async def delete_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete user's chat history."""
        if not update.message:
            return
        
        user = self._get_or_create_user(update.message.from_user.id)
        
        # Check authentication
        if not user.authenticated:
            await update.message.reply_text(
                "Please authenticate first with: /start PASSWORD"
            )
            return
        
        try:
            # Delete chat history
            with get_db() as db:
                deleted = db.query(Chat).filter(Chat.user_id == user.id).delete()
                db.commit()
            
            await update.message.reply_text(
                f"Successfully deleted {deleted} messages from your chat history."
            )
            
        except Exception as e:
            error_message = f"Error deleting chat history: {str(e)}"
            await update.message.reply_text(error_message)

    def run(self):
        """Run the bot."""
        self.application.run_polling()
