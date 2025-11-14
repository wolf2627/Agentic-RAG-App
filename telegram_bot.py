"""
Telegram Bot Wrapper
Handles both text and voice messages from users
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional
import tempfile

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from dotenv import load_dotenv
from openai import OpenAI

# medical AI system
from src.main import process_patient_query
from src.models.model import PatientQuery


load_dotenv()

# Import patient mapper
from patient_mapper import get_patient_mapper

# logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class MedicalTelegramBot:
    """Telegram bot wrapper for the medical AI system"""
    
    def __init__(self, telegram_token: str, openai_api_key: str, mapper_mode: str = "json"):
        """
        Initialize the Telegram bot
        
        Args:
            telegram_token: Telegram Bot API token from BotFather
            openai_api_key: OpenAI API key for Whisper transcription
            mapper_mode: Patient ID mapping mode ('json', 'memory', 'env', 'phone')
        """
        self.telegram_token = telegram_token
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.patient_mapper = get_patient_mapper(mapper_mode)
        self.whisper_model = os.getenv("WHISPER_MODEL", "whisper-1")
        self.app = None
        
    def build_application(self) -> Application:
        """Build and configure the Telegram application"""
        # Create the Application
        self.app = Application.builder().token(self.telegram_token).build()
        
        # Register handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("reset", self.reset_command))
        self.app.add_handler(CommandHandler("myid", self.my_id_command))
        self.app.add_handler(CommandHandler("register", self.register_command))
        
        # Handle text messages
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_text_message
        ))
        
        # Handle voice messages
        self.app.add_handler(MessageHandler(
            filters.VOICE, 
            self.handle_voice_message
        ))
        
        # Handle audio files
        self.app.add_handler(MessageHandler(
            filters.AUDIO,
            self.handle_audio_message
        ))
        
        return self.app
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command"""
        user = update.effective_user
        welcome_message = (
            f"Hello {user.first_name}!\n\n"
            "I'm your Medical AI Assistant. I can help you with:\n"
            "• General health questions\n"
            "• Symptom analysis\n"
            "• Medical guidance\n\n"
            "You can:\n"
            "Send me a text message\n"
            "Send me a voice message\n"
            "Send me an audio file\n\n"
            "I support multiple languages and will respond in your preferred language.\n\n"
            "**Important**: I'm an AI assistant, not a replacement for professional medical care. "
            "For emergencies, always call your local emergency number!\n\n"
            "Type /help for more information."
        )
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command"""
        help_message = (
            "**How to use this bot:**\n\n"
            "**Text Messages**: Just type your medical question in any language\n"
            "**Voice Messages**: Tap and hold the microphone to record\n"
            "**Audio Files**: Send audio files for transcription\n\n"
            "**Commands:**\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/reset - Reset your session\n\n"
            "**Privacy:**\n"
            "Your Telegram user ID is used as your patient ID for context.\n\n"
            "**Languages:**\n"
            "I support multiple languages including English, Tamil and more!\n\n"
            "**Emergency Warning:**\n"
            "For medical emergencies, call 108 (TN IND) or your local emergency number immediately!"
        )
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def reset_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /reset command"""
        # Clear user context if any
        context.user_data.clear()
        await update.message.reply_text(
            "Your session has been reset. You can start a new conversation now."
        )
    
    async def my_id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /myid command - show user their IDs"""
        user = update.effective_user
        patient_id = self.patient_mapper.get_patient_id(user.id)
        
        message = (
            f"**Your Information:**\n\n"
            f"Telegram User ID: `{user.id}`\n"
            f"Patient ID: `{patient_id}`\n"
            f"Username: @{user.username or 'Not set'}\n"
            f"Name: {user.full_name}\n\n"
            f"_Your Telegram User ID is automatically mapped to your Patient ID._"
        )
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /register command - admin can map custom patient IDs"""
        user = update.effective_user
        
        # Check if patient ID was provided
        if not context.args:
            await update.message.reply_text(
                "Usage: `/register PATIENT_ID`\n\n"
                "Example: `/register PATIENT_12345`\n\n"
                "This will map your Telegram account to the specified Patient ID.",
                parse_mode='Markdown'
            )
            return
        
        new_patient_id = context.args[0]
        
        # Validate patient ID format (alphanumeric and underscores only)
        if not new_patient_id.replace('_', '').isalnum():
            await update.message.reply_text(
                "Invalid Patient ID format. Use only letters, numbers, and underscores."
            )
            return
        
        # Register the mapping
        self.patient_mapper.add_mapping(user.id, new_patient_id)
        
        await update.message.reply_text(
            f"Successfully registered!\n\n"
            f"Your Telegram ID `{user.id}` is now mapped to Patient ID `{new_patient_id}`",
            parse_mode='Markdown'
        )
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages"""
        user = update.effective_user
        user_message = update.message.text
        
        logger.info(f"Received text from user {user.id}: {user_message[:50]}...")
        
        # Send "typing" action
        await update.message.chat.send_action("typing")
        
        try:
            # Process the query using your existing system
            # Get patient ID from mapper
            patient_id = self.patient_mapper.get_patient_id(user.id)
            
            response = await self._process_medical_query(
                text=user_message,
                patient_id=patient_id
            )
            
            # Send response back to user
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Error processing text message: {e}", exc_info=True)
            await update.message.reply_text(
                "Sorry, I encountered an error processing your message. "
                "Please try again or contact support if the issue persists."
            )
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming voice messages"""
        user = update.effective_user
        voice = update.message.voice
        
        logger.info(f"Received voice message from user {user.id}")
        
        # Send "typing" action
        await update.message.chat.send_action("typing")
        
        try:
            # Download voice file
            voice_file = await voice.get_file()
            
            # Create temporary file for voice data
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                temp_path = temp_file.name
                await voice_file.download_to_drive(temp_path)
            
            try:
                # Transcribe voice to text using Whisper
                transcribed_text = await self._transcribe_audio(temp_path)
                
                if not transcribed_text:
                    await update.message.reply_text(
                        "Sorry, I couldn't transcribe your voice message. "
                        "Please try again or send a text message instead."
                    )
                    return
                
                logger.info(f"Transcribed text: {transcribed_text[:50]}...")
                
                # Get patient ID from mapper
                patient_id = self.patient_mapper.get_patient_id(user.id)
                
                # Show user what was transcribed
                # await update.message.reply_text(
                #     f"*Transcribed:* {transcribed_text}\n\n"
                #     "Processing your query...",
                #     parse_mode='Markdown'
                # )
                
                # Process the transcribed query
                response = await self._process_medical_query(
                    text=transcribed_text,
                    patient_id=patient_id
                )
                
                # Send response
                await update.message.reply_text(response)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Error processing voice message: {e}", exc_info=True)
            await update.message.reply_text(
                "Sorry, I encountered an error processing your voice message. "
                "Please try again or send a text message instead."
            )
    
    async def handle_audio_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming audio files"""
        user = update.effective_user
        audio = update.message.audio
        
        logger.info(f"Received audio file from user {user.id}")
        
        await update.message.chat.send_action("typing")
        
        try:
            # Download audio file
            audio_file = await audio.get_file()
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
                await audio_file.download_to_drive(temp_path)
            
            try:
                # Transcribe audio
                transcribed_text = await self._transcribe_audio(temp_path)
                
                if not transcribed_text:
                    await update.message.reply_text(
                        "Sorry, I couldn't transcribe your audio. Please try again."
                    )
                    return
                
                logger.info(f"Transcribed audio: {transcribed_text[:50]}...")
                
                # Get patient ID from mapper
                patient_id = self.patient_mapper.get_patient_id(user.id)
                
                # Show transcription
                # await update.message.reply_text(
                #     f"*Transcribed:* {transcribed_text}\n\n"
                #     "Processing your query...",
                #     parse_mode='Markdown'
                # )
                
                # Process query
                response = await self._process_medical_query(
                    text=transcribed_text,
                    patient_id=patient_id
                )
                
                await update.message.reply_text(response)
                
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            await update.message.reply_text(
                "Sorry, I encountered an error processing your audio. "
                "Please try again."
            )
    
    async def _transcribe_audio(self, audio_path: str) -> Optional[str]:
        """
        Transcribe audio file to text using OpenAI Whisper
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcribed text or None if transcription fails
        """
        try:
            with open(audio_path, 'rb') as audio_file:
                # Use OpenAI Whisper API for transcription
                transcript = self.openai_client.audio.transcriptions.create(
                    model=self.whisper_model,
                    file=audio_file,
                    response_format="text"
                )
                
                # Handle different response formats
                if isinstance(transcript, str):
                    return transcript.strip()
                elif hasattr(transcript, 'text'):
                    return transcript.text.strip()
                else:
                    logger.error(f"Unexpected transcript format: {type(transcript)}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}", exc_info=True)
            return None
    
    async def _process_medical_query(self, text: str, patient_id: str) -> str:
        """
        Process medical query using your existing system
        
        Args:
            text: The user's query text
            patient_id: The patient/user identifier
            
        Returns:
            The AI's response text
        """
        try:
            # Create PatientQuery object
            query = PatientQuery(
                text=text,
                patient_id=patient_id
            )
            
            # Process with existing system
            result = await process_patient_query(query)
            
            # Extract the response
            response_text = result.get('response', 'Sorry, I could not generate a response.')
            
            # Add metadata if available
            detected_lang = result.get('detected_language')
            classification = result.get('classification')
            
            # Format response with metadata
            formatted_response = response_text
            
            # Add urgency warning if needed
            if classification and hasattr(classification, 'urgency_level'):
                if classification.urgency_level == 'emergency':
                    formatted_response = (
                        "**EMERGENCY DETECTED**\n"
                        "**CALL 108 OR YOUR LOCAL EMERGENCY NUMBER IMMEDIATELY!**\n\n"
                        f"{formatted_response}"
                    )
                elif classification.urgency_level == 'high':
                    formatted_response = (
                        "**High Urgency**\n"
                        "Please seek medical attention soon.\n\n"
                        f"{formatted_response}"
                    )
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error in _process_medical_query: {e}", exc_info=True)
            raise
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Medical AI Telegram Bot...")
        self.build_application()
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point"""
    # Get tokens from environment
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    mapper_mode = os.getenv('PATIENT_MAPPER_MODE', 'json')  # default to JSON
    
    if not telegram_token:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN not found in environment variables. "
            "Please set it in your .env file."
        )
    
    if not openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please set it in your .env file."
        )
    
    logger.info(f"Using patient mapper mode: {mapper_mode}")
    
    # Create and run bot
    bot = MedicalTelegramBot(
        telegram_token=telegram_token,
        openai_api_key=openai_api_key,
        mapper_mode=mapper_mode
    )
    
    bot.run()


if __name__ == "__main__":
    main()