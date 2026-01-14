import asyncio
import random
import json
import time
import re
from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.types.chat_member import ChatMemberAdministrator, ChatMemberOwner
import os

if not os.path.exists("quotes_data.json"):
    with open("quotes_data.json", "w", encoding="utf-8") as f:
        f.write("{}")
        
TOKEN = "8402954126:AAFtyY-cbxhK_tiYkOxgcuMf3JryLK8mN0I"
DATA_FILE = "quotes_data.json"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ======================
# НАСТРОЙКИ
# ======================

TIME_INTERVALS = [600, 1200, 1800, 3600]
MAX_MESSAGES = 1000

MENTION_CHANCE = 3
MENTION_WORDS = ["историк", "бот"]
MENTION_REPLIES = [
    "👀 Я тут",
    "🤖 На месте",
    "📜 Историк слушает",
    "😌 Я никуда не уходил",
    "✍️ Записываю…",
]

# ======================
# ХРАНИЛИЩА
# ======================

messages_store = {}
current_quote = {}
next_change_time = {}

# ======================
# УТИЛИТЫ
# ======================

def get_next_interval():
    return random.choice(TIME_INTERVALS)


def normalize_command(text: str) -> str:
    text = text.lower().strip()
    if not text.startswith(("!", "/")):
        return ""
    prefix = text[0]
    body = re.sub(r"[^a-zа-яё]", "", text[1:])
    return prefix + body


def format_quote(quote: dict) -> str:
    return f"💭 «{quote['text']}»\n— {quote['author']}"


async def is_admin(chat_id: int, user_id: int) -> bool:
    member = await bot.get_chat_member(chat_id, user_id)
    return isinstance(member, (ChatMemberAdministrator, ChatMemberOwner))


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "messages_store": messages_store,
                "current_quote": current_quote,
                "next_change_time": next_change_time,
            },
            f,
            ensure_ascii=False,
        )


def load_data():
    global messages_store, current_quote, next_change_time
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            messages_store = {int(k): v for k, v in data.get("messages_store", {}).items()}
            current_quote = {int(k): v for k, v in data.get("current_quote", {}).items()}
            next_change_time = {int(k): v for k, v in data.get("next_change_time", {}).items()}
    except FileNotFoundError:
        pass

# ======================
# ТАЙМЕР
# ======================

async def quote_timer():
    while True:
        now = time.time()

        for chat_id in list(messages_store.keys()):
            if not messages_store.get(chat_id):
                continue

            if chat_id not in next_change_time or now >= next_change_time[chat_id]:
                quote = random.choice(messages_store[chat_id])
                current_quote[chat_id] = quote
                next_change_time[chat_id] = now + get_next_interval()

                try:
                    chat = await bot.get_chat(chat_id)
                    if chat.type in ("group", "supergroup"):
                        await bot.send_message(chat_id, format_quote(quote))
                except Exception:
                    pass

                save_data()

        await asyncio.sleep(30)

# ======================
# АДМИН-ПАНЕЛЬ
# ======================

@dp.message(lambda m: normalize_command(m.text) in ("!admin", "/admin"))
async def admin_panel(message: Message):
    if message.chat.type == "private":
        return

    if not await is_admin(message.chat.id, message.from_user.id):
        await message.reply("❌ Только для администраторов")
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏱ Интервалы", callback_data="admin_intervals")],
        [InlineKeyboardButton(text="🧹 Очистить цитаты", callback_data="admin_clear")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
    ])

    await message.reply("⚙ Админ-панель", reply_markup=kb)


@dp.callback_query(lambda c: c.data.startswith("admin_"))
async def admin_callbacks(call: CallbackQuery):
    chat_id = call.message.chat.id

    if not await is_admin(chat_id, call.from_user.id):
        await call.answer("Нет прав", show_alert=True)
        return

    if call.data == "admin_intervals":
        mins = [str(i // 60) for i in TIME_INTERVALS]
        await call.message.answer(f"⏱ Интервалы: {', '.join(mins)} мин")

    elif call.data == "admin_clear":
        messages_store[chat_id] = []
        current_quote.pop(chat_id, None)
        save_data()
        await call.message.answer("🧹 Все цитаты очищены")

    elif call.data == "admin_stats":
        count = len(messages_store.get(chat_id, []))
        await call.message.answer(f"📊 Сохранённых сообщений: {count}")

    await call.answer()

# ======================
# СООБЩЕНИЯ
# ======================

@dp.message()
async def handle_message(message: Message):
    if message.chat.type == "private":
        return
    if message.from_user.is_bot or not message.text:
        return

    chat_id = message.chat.id
    text = message.text
    cmd = normalize_command(text)

    if any(w in text.lower() for w in MENTION_WORDS):
        if random.randint(1, MENTION_CHANCE) == 1:
            await message.reply(random.choice(MENTION_REPLIES))

    if cmd in ("!цитата", "/цитата", "!quote", "/quote"):
        quote = current_quote.get(chat_id)
        if quote:
            await message.reply(format_quote(quote))
        else:
            await message.reply("📭 Цитата ещё не выбрана")
        return

    if cmd in ("!взятьцитату", "/взятьцитату", "!takequote", "/takequote"):
        if not messages_store.get(chat_id):
            await message.reply("📭 Недостаточно сообщений")
            return
        quote = random.choice(messages_store[chat_id])
        current_quote[chat_id] = quote
        next_change_time[chat_id] = time.time() + get_next_interval()
        save_data()
        await message.reply(format_quote(quote))
        return

    if not text.startswith(("!", "/")):
        messages_store.setdefault(chat_id, []).append({
            "text": text,
            "author": message.from_user.full_name
        })
        if len(messages_store[chat_id]) > MAX_MESSAGES:
            messages_store[chat_id].pop(0)
        next_change_time.setdefault(chat_id, time.time() + get_next_interval())
        save_data()

# ======================
# ЗАПУСК
# ======================

async def main():
    load_data()
    asyncio.create_task(quote_timer())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
