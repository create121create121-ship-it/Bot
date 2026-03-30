import logging
import google.generativeai as genai
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
import asyncio
import random
import sqlite3
from datetime import datetime
import sys

# Configure logging to both file and console
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
  ]
)
logger = logging.getLogger(__name__)

# API Keys
TELEGRAM_TOKEN = "8609711640:AAEUAf56tu6zUboDcpgvcsa7q2kD2vjDFKE"
GEMINI_API_KEY = "AIzaSyCx158bADJcj3Csl6LfidyUsR_jejBbowg"

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
PRIMARY_MODEL = 'gemini-flash-latest'
SECONDARY_MODEL = 'gemini-2.0-flash'

# Database Setup
DB_PATH = "bot_history.db

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            username TEXT,
            category TEXT,
            tone TEXT,
            audience TEXT,
            topic TEXT,
            duration REAL,
            word_count INTEGER,
            script TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_to_history(user_id, username, category, tone, audience, topic, duration, word_count, script):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO history (user_id, username, category, tone, audience, topic, duration, word_count, script)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, category, tone, audience, topic, duration, word_count, script))
        conn.commit()
        conn.close()
        logger.info(f"Saved history for user {user_id} (@{username})")
    except Exception as e:
        logger.error(f"Error saving to history: {e}")

# Conversation states
CATEGORY, TONE, AUDIENCE, TOPIC, DURATION = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"User {user.id} (@{user.username}) started the bot.")
    context.user_data.clear()
    reply_keyboard = [['Kids', 'Story', 'Motivation', 'Educational', 'Tech', 'Other']]
    await update.message.reply_text(
        "नमस्ते! मैं आपका वीडियो स्क्रिप्ट जनरेटर बॉट हूँ।\n\n"
        "शुरू करने के लिए, कृपया वीडियो की **Category** चुनें:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CATEGORY

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text
    logger.info(f"User {update.effective_user.id} chose category: {update.message.text}")
    reply_keyboard = [['Funny', 'Emotional', 'Serious', 'Professional', 'Exciting']]
    await update.message.reply_text(
        "बहुत अच्छा! अब वीडियो की **Tone** चुनें:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return TONE

async def get_tone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tone'] = update.message.text
    logger.info(f"User {update.effective_user.id} chose tone: {update.message.text}")
    reply_keyboard = [['Kids', 'Teens', 'Adults', 'General Audience']]
    await update.message.reply_text(
        "वीडियो किसके लिए है? (**Target Audience** चुनें):",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return AUDIENCE

async def get_audience(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['audience'] = update.message.text
    logger.info(f"User {update.effective_user.id} chose audience: {update.message.text}")
    await update.message.reply_text(
        "वीडियो का **Topic** क्या है? (जैसे: 'How to stay healthy' या 'A story about a brave cat'):",
        reply_markup=ReplyKeyboardRemove(),
    )
    return TOPIC

async def get_topic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['topic'] = update.message.text
    logger.info(f"User {update.effective_user.id} chose topic: {update.message.text}")
    await update.message.reply_text(
        "वीडियो कितने मिनट का होना चाहिए? (**Duration in minutes**):",
    )
    return DURATION

async def generate_script_with_retry(prompt, retries=3):
    models_to_try = [PRIMARY_MODEL, SECONDARY_MODEL]
    for model_name in models_to_try:
        logger.info(f"Trying model: {model_name}")
        model = genai.GenerativeModel(model_name)
        for attempt in range(retries):
            try:
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text
            except Exception as e:
                logger.error(f"Error with model {model_name} (attempt {attempt+1}): {e}")
                if "429" in str(e) and attempt < retries - 1:
                    wait_time = (attempt + 1) * 15
                    logger.info(f"Quota limit hit. Waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                break
    return None

async def get_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        duration_text = update.message.text
        logger.info(f"User {update.effective_user.id} entered duration: {duration_text}")
        duration = float(duration_text)
        word_count = int(duration * 130)
        await update.message.reply_text(f"धन्यवाद! मैं आपके लिए लगभग {word_count} शब्दों की स्क्रिप्ट तैयार कर रहा हूँ। कृपया प्रतीक्षा करें...")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        prompt = (
            f"Write a COMPLETE video script. Category: {context.user_data['category']}, "
            f"Tone: {context.user_data['tone']}, Audience: {context.user_data['audience']}, "
            f"Topic: {context.user_data['topic']}, Duration: {duration} min. "
            f"Target length: {word_count} words. Structure: Hook, Beginning, Middle, Ending. "
            f"Language: Hindi/English mix."
        )
        
        script = await generate_script_with_retry(prompt)
        
        if script:
            username = update.effective_user.username or update.effective_user.first_name
            save_to_history(
                str(update.effective_user.id),
                username,
                context.user_data['category'],
                context.user_data['tone'],
                context.user_data['audience'],
                context.user_data['topic'],
                duration,
                word_count,
                script
            )
            
            if len(script) > 4000:
                for i in range(0, len(script), 4000):
                    await update.message.reply_text(script[i:i+4000])
            else:
                await update.message.reply_text(script)
            await update.message.reply_text("\n\n✅ स्क्रिप्ट तैयार है! नई स्क्रिप्ट के लिए /start दबाएं।")
        else:
            await update.message.reply_text("क्षमा करें, Google AI अभी जवाब नहीं दे पा रहा है। कृपया 1-2 मिनट बाद फिर से कोशिश करें।")
            
    except ValueError:
        await update.message.reply_text("कृपया केवल नंबर लिखें (जैसे: 1.5):")
        return DURATION
    except Exception as e:
        logger.error(f"Error in get_duration: {e}")
        await update.message.reply_text("क्षमा करें, कुछ तकनीकी समस्या आई।")
    
    return ConversationHandler.END

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} reset the bot.")
    context.user_data.clear()
    await update.message.reply_text("बॉट रीसेट हो गया है। /start दबाएं।", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update: {context.error}")

if __name__ == '__main__':
    init_db()
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            TONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tone)],
            AUDIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_audience)],
            TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_topic)],
            DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_duration)],
        },
        fallbacks=[CommandHandler('reset', reset)],
        allow_reentry=True
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('reset', reset))
    application.add_error_handler(error_handler)
    
    logger.info("Bot starting with database support and enhanced logging...")
    application.run_polling(drop_pending_updates=True)
