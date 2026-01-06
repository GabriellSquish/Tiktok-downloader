import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)
import yt_dlp
from deep_translator import GoogleTranslator

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ========== YDL CONFIG ==========
INFO_OPTS = {
    "quiet": True,
    "skip_download": True,
    "extract_flat": True,
    "nocheckcertificate": True,
}

VIDEO_OPTS = {
    "quiet": True,
    "outtmpl": "video.%(ext)s",
    "format": "mp4[ext=mp4]+bestaudio/best",
    "nocheckcertificate": True,
}

# ========== FUNCTIONS ==========
async def extract_caption(url: str) -> str:
    def run():
        with yt_dlp.YoutubeDL(INFO_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("description") or info.get("title") or "❌ Caption tidak ditemukan"
    return await asyncio.to_thread(run)

def translate_id(text: str) -> str:
    try:
        return GoogleTranslator(source="auto", target="id").translate(text)
    except:
        return text

async def download_video(url: str) -> str:
    def run():
        with yt_dlp.YoutubeDL(VIDEO_OPTS) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    return await asyncio.to_thread(run)

# ========== HANDLERS ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.startswith("http"):
        await update.message.reply_text("❌ Kirim link TikTok / YouTube")
        return

    context.user_data["last_url"] = text
    await update.message.reply_text("⚡ Mengambil caption...")
    
    caption = await extract_caption(text)
    translated = translate_id(caption)
    context.user_data["last_caption"] = translated

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📋 Copy Caption", callback_data="copy")],
            [InlineKeyboardButton("⬇️ Download Video", callback_data="download")],
        ]
    )

    await update.message.reply_text(
        f"📝 CAPTION (ID):\n\n{translated[:3500]}",
        reply_markup=keyboard,
    )

async def copy_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    caption = context.user_data.get("last_caption", "❌ Tidak ada caption")
    await query.message.reply_text(caption[:4000])

async def download_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⏳ Downloading video...")

    url = context.user_data.get("last_url")
    if not url:
        await query.message.reply_text("❌ URL tidak ditemukan.")
        return

    try:
        file_path = await download_video(url)
        await query.message.reply_video(video=open(file_path, "rb"))
        os.remove(file_path)
    except Exception as e:
        await query.message.reply_text(f"❌ Gagal download:\n{e}")

# ========== MAIN ==========
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(copy_caption, pattern="copy"))
    app.add_handler(CallbackQueryHandler(download_handler, pattern="download"))

    print("🤖 Bot TikTok + YouTube full video aktif 24 jam...")
    app.run_polling()

if __name__ == "__main__":
    main()
