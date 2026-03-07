"""
Telegram-бот для Web3devmaster
================================
Функции:
- Уведомления о новых заявках с сайта
- Кнопки быстрого ответа клиенту
- Статистика заявок
- Напоминание если не ответил на заявку в течение 30 минут
- Команды /start /help /price

Установка:
    pip install pyTelegramBotAPI

Запуск:
    python bot.py
"""

import telebot
from telebot import types
import json
import os
import threading
import time
from datetime import datetime

# =============================================
# НАСТРОЙКИ — замените на свои значения
# =============================================
BOT_TOKEN  = os.getenv('BOT_TOKEN',  '8275219782:AAFoL7kNGLnMG1D23GvhzERlH-bdidHiESc')    # токен от @BotFather
MY_CHAT_ID = os.getenv('MY_CHAT_ID', '5371718405')  # ваш chat_id
REMIND_AFTER_MIN = 30          # напомнить через N минут если нет ответа
# =============================================

bot = telebot.TeleBot(BOT_TOKEN)

# Файл для хранения заявок
STATS_FILE = 'stats.json'

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'total': 0, 'answered': 0, 'pending': [], 'applications': []}

def save_stats(data):
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_application(name, email, message):
    stats = load_stats()
    app_id = stats['total'] + 1
    application = {
        'id': app_id,
        'name': name,
        'email': email,
        'message': message,
        'time': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'answered': False,
        'timestamp': time.time()
    }
    stats['total'] += 1
    stats['pending'].append(app_id)
    stats['applications'].append(application)
    save_stats(stats)
    return app_id

def mark_answered(app_id):
    stats = load_stats()
    for app in stats['applications']:
        if app['id'] == app_id:
            app['answered'] = True
    if app_id in stats['pending']:
        stats['pending'].remove(app_id)
    stats['answered'] += 1
    save_stats(stats)

# ─── КОМАНДА /start ───
@bot.message_handler(commands=['start'])
def cmd_start(message):
    text = (
        "👋 *Привет! Я бот Web3devmaster*\n\n"
        "Я уведомляю о новых заявках с сайта и помогаю управлять ими.\n\n"
        "📋 *Доступные команды:*\n"
        "/start — главное меню\n"
        "/help — помощь\n"
        "/price — прайс-лист\n"
        "/stats — статистика заявок\n"
        "/pending — неотвеченные заявки"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ─── КОМАНДА /help ───
@bot.message_handler(commands=['help'])
def cmd_help(message):
    text = (
        "🛠 *Как пользоваться ботом:*\n\n"
        "Когда клиент оставляет заявку на сайте, бот пришлёт уведомление с кнопками:\n\n"
        "✅ *Ответил* — отмечает заявку как обработанную\n"
        "📋 *Скопировать email* — показывает email клиента\n"
        "⏰ *Напомнить позже* — напомнит через 30 минут\n\n"
        "Если не ответить на заявку в течение "
        f"{REMIND_AFTER_MIN} минут — бот пришлёт напоминание автоматически."
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ─── КОМАНДА /price ───
@bot.message_handler(commands=['price'])
def cmd_price(message):
    text = (
        "💰 *Прайс-лист Web3devmaster*\n\n"
        "🔹 *Лендинг* — от 8 000 ₽\n"
        "   Одностраничный сайт, адаптивный дизайн,\n"
        "   форма заявки, сдача за 1 день\n\n"
        "🔹 *Корпоративный сайт* — от 35 000 ₽\n"
        "   Многостраничный, блог, личный кабинет\n\n"
        "🔹 *Интернет-магазин* — от 50 000 ₽\n"
        "   Каталог, корзина, онлайн-оплата\n\n"
        "📩 Все вопросы: @Kasey2008"
    )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ─── КОМАНДА /stats ───
@bot.message_handler(commands=['stats'])
def cmd_stats(message):
    stats = load_stats()
    pending_count = len(stats['pending'])
    text = (
        "📊 *Статистика заявок*\n\n"
        f"📥 Всего заявок: *{stats['total']}*\n"
        f"✅ Обработано: *{stats['answered']}*\n"
        f"⏳ Ожидают ответа: *{pending_count}*\n"
    )
    if stats['applications']:
        last = stats['applications'][-1]
        text += f"\n🕐 Последняя заявка: *{last['time']}*\nОт: {last['name']}"
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ─── КОМАНДА /pending ───
@bot.message_handler(commands=['pending'])
def cmd_pending(message):
    stats = load_stats()
    pending_ids = stats['pending']
    if not pending_ids:
        bot.send_message(message.chat.id, "✅ Все заявки обработаны!")
        return
    text = f"⏳ *Неотвеченных заявок: {len(pending_ids)}*\n\n"
    for app in stats['applications']:
        if app['id'] in pending_ids:
            text += (
                f"#{app['id']} — *{app['name']}*\n"
                f"📧 {app['email']}\n"
                f"🕐 {app['time']}\n\n"
            )
    bot.send_message(message.chat.id, text, parse_mode='Markdown')

# ─── ОБРАБОТКА КНОПОК ───
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    data = call.data

    # Кнопка "Ответил"
    if data.startswith('answered_'):
        app_id = int(data.split('_')[1])
        mark_answered(app_id)
        bot.answer_callback_query(call.id, "✅ Заявка отмечена как обработанная")
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=None
        )
        bot.send_message(call.message.chat.id, f"✅ Заявка #{app_id} обработана.")

    # Кнопка "Скопировать email"
    elif data.startswith('email_'):
        app_id = int(data.split('_')[1])
        stats = load_stats()
        for app in stats['applications']:
            if app['id'] == app_id:
                bot.answer_callback_query(call.id, app['email'], show_alert=True)
                break

    # Кнопка "Напомнить позже"
    elif data.startswith('remind_'):
        app_id = int(data.split('_')[1])
        bot.answer_callback_query(call.id, f"⏰ Напомню через {REMIND_AFTER_MIN} минут")
        threading.Thread(
            target=send_reminder,
            args=(app_id, REMIND_AFTER_MIN * 60),
            daemon=True
        ).start()

def send_reminder(app_id, delay_seconds):
    time.sleep(delay_seconds)
    stats = load_stats()
    for app in stats['applications']:
        if app['id'] == app_id and not app['answered']:
            text = (
                f"⏰ *Напоминание!*\n\n"
                f"Заявка #{app_id} от *{app['name']}* всё ещё ждёт ответа.\n"
                f"📧 {app['email']}\n\n"
                f"💬 {app['message'][:100]}..."
            )
            markup = make_keyboard(app_id, app['email'])
            bot.send_message(MY_CHAT_ID, text, parse_mode='Markdown', reply_markup=markup)

def make_keyboard(app_id, email):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Ответил", callback_data=f"answered_{app_id}"),
        types.InlineKeyboardButton("📋 Email", callback_data=f"email_{app_id}"),
        types.InlineKeyboardButton("⏰ Напомнить позже", callback_data=f"remind_{app_id}")
    )
    return markup

def notify_new_application(name, email, message):
    """
    Вызывайте эту функцию когда приходит новая заявка с сайта.
    Можно интегрировать с вашим бэкендом или webhook.
    """
    app_id = add_application(name, email, message)

    text = (
        f"🔔 *Новая заявка с сайта! #{app_id}*\n\n"
        f"👤 *Имя:* {name}\n"
        f"📧 *Email:* {email}\n\n"
        f"💬 *Сообщение:*\n{message}\n\n"
        f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    markup = make_keyboard(app_id, email)
    bot.send_message(MY_CHAT_ID, text, parse_mode='Markdown', reply_markup=markup)

    # Запускаем автоматическое напоминание
    threading.Thread(
        target=auto_remind,
        args=(app_id, REMIND_AFTER_MIN * 60),
        daemon=True
    ).start()

def auto_remind(app_id, delay_seconds):
    """Автоматически напоминает если заявка не обработана"""
    time.sleep(delay_seconds)
    stats = load_stats()
    for app in stats['applications']:
        if app['id'] == app_id and not app['answered']:
            text = (
                f"⚠️ *Автонапоминание!*\n\n"
                f"Заявка #{app_id} от *{app['name']}* не обработана уже {REMIND_AFTER_MIN} минут!\n"
                f"📧 {app['email']}"
            )
            markup = make_keyboard(app_id, app['email'])
            bot.send_message(MY_CHAT_ID, text, parse_mode='Markdown', reply_markup=markup)

# ─── ЗАПУСК ───
if __name__ == '__main__':
    print("✅ Бот запущен!")
    print(f"⏰ Напоминания через {REMIND_AFTER_MIN} минут")
    print("Нажмите Ctrl+C для остановки\n")
    bot.infinity_polling()
