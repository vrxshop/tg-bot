import logging
import asyncio
import os
import json
import uuid
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web

# --- КОНФИГУРАЦИЯ RollyPay ---
ROLLYPAY_API_KEY = "z39_r_COJdiB7PWeddOYvzT2rx4cjIbS1m4JJcgBTi0"
ROLLYPAY_CALLBACK_URL = "https://t-bot-18jz.onrender.com/webhook"

# --- КОНФИГУРАЦИЯ БОТА ---
BOT_TOKEN = "8843954886:AAEpfaWLm6sTfmq2T-mShBilX8mInCXs3as"
PROJECT_NAME = "VIP"
SUPPORT_CONTACT_RU = "https://t.me/Nastia_sup"
SUPPORT_CONTACT_EN = "https://t.me/Nastia_sup"

DOCS_RU = {
    "offer": "https://telegra.ph/POLZOVATELSKOE-SOGLASHENIE-07-01-29",
    "policy": "https://telegra.ph/Politika-konfidicialnosti-07-01"
}
DOCS_EN = {
    "offer": "https://telegra.ph/POLZOVATELSKOE-SOGLASHENIE-07-01-29",
    "policy": "https://telegra.ph/Politika-konfidicialnosti-07-01"
}

# ==================================================
# ⭐ ССЫЛКИ ДЛЯ КАЖДОГО ТАРИФА (МЕНЯЙ ЗДЕСЬ!) ⭐
# ==================================================
TARIFF_LINKS = {
    "1": "https://t.me/+ваша_ссылка_для_слива_знаменитостей",   # Слив знаменитостей
    "2": "https://t.me/+ваша_ссылка_для_сливов_шкур",          # Сливы шкур
    "3": "https://t.me/+ваша_ссылка_для_mini_det",             # Mini Детск. До 12
    "4": "https://t.me/+ваша_ссылка_для_шкодниц",              # ШкоДнищь
    "5": "https://t.me/+ваша_ссылка_для_premium_det",          # Premium Детск. До 12
    "6": "https://t.me/+ваша_ссылка_для_зоо",                  # Канал Зоо
    "7": "https://t.me/+ваша_ссылка_для_геев",                 # Геи
    "8": "https://t.me/+ваша_ссылка_для_закладчиц",            # Закладчицы
    "9": "https://t.me/+ваша_ссылка_для_все_включено",         # Всё включено 2026
    "10": "https://t.me/velvet_vpn_bot?start=AW3BJ7lz",        # Vpn 7 дней
    "11": "https://t.me/+ваша_ссылка_для_обновления_ссылок",   # Пак - Обновление ссылок
    "test": "https://t.me/+ваша_ссылка_для_тестового_тарифа",  # Тестовый тариф
}
# ==================================================

# --- ТЕКСТЫ ---
LANG = {
    "ru": {
        "start_promo": "🎉 <b>Промокод {code} активирован! Скидка {discount}%!</b>",
        "start_welcome": "👋 Привет, {name}!\n\n<a href=\"{offer}\">Пользовательское соглашение</a>\n<a href=\"{policy}\">Политика конфиденциальности</a>",
        "prices_menu": "📋 <b>Прайс</b>\n\nВыберите тариф, чтобы узнать подробности и оформить покупку.",
        "subs_menu": "⌛️ <b>У Вас нет действующей подписки.</b>\n\nОзнакомьтесь с тарифами, нажав на соответствующую кнопку.",
        "tariff_desc": "📋 <b>{name}</b>\n\n{price_line}\n\n{desc}",
        "enter_promo": "🏷️ <b>Введите код промокода</b>\n\nНапишите промокод в чат.",
        "promo_success": "✅ Промокод <b>{code}</b> активирован! Скидка {discount}% 🔥\n\n📋 <b>{name}</b>\n💰 Цена: <s>{old_rub} RUB</s> → {new_rub} RUB <b>(-{discount}%)</b>\n\nВыберите валюту для оплаты.",
        "promo_fail": "❌ Промокод не найден. Попробуйте еще раз (или нажмите ◀️ Отмена).",
        "choose_pay": "📋 <b>{name}</b>\nСрок доступа: {duration}\n💰 Цена: {price_text}\n\n🔒 Будет получен доступ к:\n• {project} (внешняя ссылка)\n\nВыберите валюту для оплаты тарифа",
        "pay_rub": "📋 <b>{name}</b>\nСрок доступа: {duration}\n{price_line}💳 Способ оплаты: RollyPay\n\n💰 Итоговая стоимость: {final} RUB\n\n🔒 Будет получен доступ к:\n• {project} (внешняя ссылка)\n\n✅ Счет на оплату сформирован! Сразу же после оплаты здесь появятся ссылки с доступами",
        "pay_stars": "📋 <b>{name}</b>\nСрок доступа: {duration}\n{price_line}💳 Способ оплаты: ЗА ЗВЕЗДЫ ⭐\n\n💰 Итоговая стоимость: {final} STARS\n\nℹ️ <b>Информация по оплате</b>\nПодарить звезды или подарки на этот аккаунт - <a href=\"{support}\">@Nastia_sup</a>\n\nкурс:\n1 ⭐ - 1 рубль\n\nОтправьте скриншот или файл подтверждения оплаты - он будет передан продавцу.\n\n⚠️ <b>Внимание:</b> на квитанции должны быть четко видны: дата, время и сумма платежа!\nЗа поддельные скриншоты продавец вас может заблокировать!",
        "refresh_link": "♻️ <i>Ссылка обновлена!</i>",
        "btn_prices": "💵 Тарифы",
        "btn_subs": "⏳ Моя подписка",
        "btn_promo": "🏷️ Ввести промокод",
        "btn_pay": "💳 Способы оплаты",
        "btn_back": "👈 НАЗАД",
        "btn_pay_rub": "{price} RUB",
        "btn_pay_rub_disc": "{price} RUB 🏷️(-{disc}%)",
        "btn_pay_stars": "{price} STARS",
        "btn_pay_stars_disc": "{price} STARS 🏷️(-{disc}%)",
        "btn_goto_pay": "✅ ПЕРЕЙТИ К ОПЛАТЕ",
        "btn_new_link": "🔗 Получить новую ссылку",
        "btn_to_prices": "✅ КУПИТЬ ПОДПИСКУ",
        "btn_cancel": "🚫 ОТМЕНА",
        "btn_stars_go": "⭐ Stars со скидкой до 42%",
        "btn_lang": "🇷🇺 Язык",
        "payment_success": "✅ <b>Оплата прошла!</b>\n\n🔗 <b>Ваша ссылка доступа:</b>\n{link}\n\nСпасибо за покупку! ❤️",
        "payment_success_test": "*Оплата прошла!* 🎉\n\nЭто тестовый тариф. Спасибо за проверку! 🙌"
    },
    "en": {
        "start_promo": "🎉 <b>Promo code {code} activated! {discount}% discount!</b>",
        "start_welcome": "👋 Hello, {name}!\n\n<a href=\"{offer}\">Terms of Service</a>\n<a href=\"{policy}\">Privacy Policy</a>",
        "prices_menu": "📋 <b>Prices</b>\n\nSelect a tariff to view details and make a purchase.",
        "subs_menu": "⌛️ <b>You don't have an active subscription.</b>\n\nCheck out the tariffs by pressing the button below.",
        "tariff_desc": "📋 <b>{name}</b>\n\n{price_line}\n\n{desc}",
        "enter_promo": "🏷️ <b>Enter promo code</b>\n\nType the promo code in the chat.",
        "promo_success": "✅ Promo code <b>{code}</b> activated! {discount}% discount 🔥\n\n📋 <b>{name}</b>\n💰 Price: <s>{old_rub} RUB</s> → {new_rub} RUB <b>(-{discount}%)</b>\n\nChoose a currency for payment.",
        "promo_fail": "❌ Promo code not found. Try again (or press ◀️ Cancel).",
        "choose_pay": "📋 <b>{name}</b>\nAccess duration: {duration}\n💰 Price: {price_text}\n\n🔒 You will get access to:\n• {project} (external link)\n\nChoose a currency for payment",
        "pay_rub": "📋 <b>{name}</b>\nAccess duration: {duration}\n{price_line}💳 Payment method: RollyPay\n\n💰 Total cost: {final} RUB\n\n🔒 You will get access to:\n• {project} (external link)\n\n✅ Invoice created! Right after payment, access links will appear here",
        "pay_stars": "📋 <b>{name}</b>\nAccess duration: {duration}\n{price_line}💳 Payment method: FOR STARS ⭐\n\n💰 Total cost: {final} STARS\n\nℹ️ <b>Payment info</b>\nSend stars or gifts to this account - <a href=\"{support}\">@Nastia_sup</a>\n\nRate:\n1 ⭐ - 1 ruble\n\nSend a screenshot or file confirming payment - it will be forwarded to the seller.\n\n⚠️ <b>Attention:</b> the receipt must clearly show: date, time, and payment amount!\nFor fake screenshots, the seller may block you!",
        "refresh_link": "♻️ <i>Link refreshed!</i>",
        "btn_prices": "💵 Prices",
        "btn_subs": "⏳ My subscription",
        "btn_promo": "🏷️ Enter promo code",
        "btn_pay": "💳 Payment methods",
        "btn_back": "👈 Back",
        "btn_pay_rub": "{price} RUB",
        "btn_pay_rub_disc": "{price} RUB 🏷️(-{disc}%)",
        "btn_pay_stars": "{price} STARS",
        "btn_pay_stars_disc": "{price} STARS 🏷️(-{disc}%)",
        "btn_goto_pay": "✅ GO TO PAYMENT",
        "btn_new_link": "🔗 Get new link",
        "btn_to_prices": "✅ BUY SUBSCRIPTION",
        "btn_cancel": "🚫 CANCEL",
        "btn_stars_go": "⭐ Stars up to 42% off",
        "btn_lang": "🇬🇧 Language",
        "payment_success": "✅ <b>Payment successful!</b>\n\n🔗 <b>Your access link:</b>\n{link}\n\nThank you for your purchase! ❤️",
        "payment_success_test": "*Payment successful!* 🎉\n\nThis is a test tariff. Thanks for testing! 🙌"
    }
}

# --- ТАРИФЫ ---
TARIFFS = {
    "1": {
        "name_ru": "🎁 Слив знаменитостей 🌟",
        "name_en": "🎁 Celebrity Leaks 🌟",
        "price_rub": 99,
        "price_stars": 90,
        "duration_ru": "1 месяц",
        "duration_en": "1 month",
        "category": "main",
        "desc_ru": "Вы получите доступ к следующим ресурсам:\n• Знаменитости VBlinse💝 (канал)\n\n❗️Что есть в привате?\n\nСливы Аринян, Маряны Ро, Эммы Гловер, RocksyLight, Генсухи, Инстасамки, Леи Горной, Чио Ям, Оляши, yuuiechka, Клубнички Лизы и др."
    },
    "2": {
        "name_ru": "🖤 Сливы шkyp 🖤",
        "name_en": "🖤 Skin Leaks 🖤",
        "price_rub": 349,
        "price_stars": 300,
        "duration_ru": "1 месяц",
        "duration_en": "1 month",
        "category": "main",
        "desc_ru": "Вы получите доступ к следующим ресурсам:\n• H2 (канал)\n\n❗️ После покупки вы попадете в приватный канал со сливом девушек\n\n✅ Что в канале? П0pнo девок 13-19, а так-же слив и их разводом на фото, видео и \"беседы\" в скайпе, иногда ссылками на соц сети и Некоторых особых шкур есть номера и страницы вк\n\n❓Уровень? В основном 14-20, но встречаются и до 14 Вo3pacT\n\n✅ Помимо канала прилагается еще немного архивов с шкурками"
    },
    "3": {
        "name_ru": "❕Mini Deтск. До 12 🌐-Хит",
        "name_en": "❕Mini Child. Up to 12 🌐-Hit",
        "price_rub": 499,
        "price_stars": 450,
        "duration_ru": "1 месяц",
        "duration_en": "1 month",
        "category": "main",
        "desc_ru": "Это мини пак с огромным количеством небольших видео\n\n❗️ После покyпки вы попадете в привaтный kaнал с de**ским пopno довольно таки жectkиm.\n\n✅ Уровень? i1-i12 вo3PacT, ceks, изnocuловаnие, инцceT, ласкает себя и т.д.\n\n✅ Помимо видео прилагается еще архивы с множеством гб"
    },
    "4": {
        "name_ru": "🔥💙ШкоDницЫ👧🏼🔥 (13-17 Jleт)",
        "name_en": "🔥💙Schoolgirls👧🏼🔥 (13-17 Years)",
        "price_rub": 799,
        "price_stars": 700,
        "duration_ru": "1 месяц",
        "duration_en": "1 month",
        "category": "main",
        "desc_ru": "❗️ После покупки вы попадете в приватный канал с цe**льным пpоцe**poм пopno\n\n✅ Большой сборник из мега подборки пopно ваших любимых шкoльниц возрастом от 12 до 17 🔥 , есть изnocuлование, инцceT, много сливов с впиcoк и просто cлив шkyp, скрытые камеры шkoльниц/стyдeнток и ceксoм, ласкает себя и т.д.\n\n✅ Помимо видео прилагается еще архивы с множеством гб этой категории.\n\nКонтента очень много"
    },
    "5": {
        "name_ru": "❗️Premium Deтск. До 12 ✅",
        "name_en": "❗️Premium Child. Up to 12 ✅",
        "price_rub": 899,
        "price_stars": 800,
        "duration_ru": "1 месяц",
        "duration_en": "1 month",
        "category": "main",
        "desc_ru": "❗️ После покyпки вы попадете в привaтный kaнал с de**ским пopno довольно таки жectkиm.\n\n✅ Уровень? i1-i12 вo3PacT, ceks, изnocuловаnие, инцceT, ласкает себя и т.д.\n\n✅ Помимо видео прилагается еще архивы с множеством гб\n\nКонтента очень много"
    },
    "6": {
        "name_ru": "Канал 3оo🐕",
        "name_en": "Zoo Channel🐕",
        "price_rub": 239,
        "price_stars": 200,
        "duration_ru": "2 месяца",
        "duration_en": "2 months",
        "category": "main",
        "desc_ru": "Канал с зоо контентом"
    },
    "7": {
        "name_ru": "Гeи",
        "name_en": "Gay",
        "price_rub": 299,
        "price_stars": 250,
        "duration_ru": "1 месяц",
        "duration_en": "1 month",
        "category": "main",
        "desc_ru": "Вы получите доступ к следующим ресурсам:\n• Gg (канал)\n\n❗️ После покупки вы попадете в приватный канал с м+м\n\n✅ Уровень? Есть до 12, но в основном видео 12-17, есть немного изnocuлование, инцceT, скрытые камеры шkoльнов/стyдeнтов и конечно основное же ceкс и минет\n\n✅ Помимо видео прилагается еще дополнительный архив."
    },
    "8": {
        "name_ru": "❤️‍🔥3αkладчu̸цы",
        "name_en": "❤️‍🔥Stashers",
        "price_rub": 499,
        "price_stars": 450,
        "duration_ru": "1 месяц",
        "duration_en": "1 month",
        "category": "paki",
        "desc_ru": "Чтo тебя ждeт в нaшu̸х прu̸вαтαх\n\nЖестκu̸e uu̸знαсu̸лвaнu̸я 3αkладчu̸ц\n0тсосы, е6ля зαкладчu̸ц в пoсαдкαх\nПолные вu̸део с зαкладчu̸цамu̸"
    },
    "9": {
        "name_ru": "🩵Всё включено 2026💚",
        "name_en": "🩵All inclusive 2026💚",
        "price_rub": 3999,
        "price_stars": 3500,
        "duration_ru": "Бессрочно",
        "duration_en": "Forever",
        "category": "main",
        "desc_ru": "❗️Вы получите доступ сразу в 10 наших каналов при этом их подписка останется у вас НАВСЕГДА! А выйдет гораздо дешевле чем покупать по отдельности.\n\n🔥 Кoнтeнтa у вас выйдет очень МНОГО\n\n+ Бонусные каналы к тарифу"
    },
    "10": {
        "name_ru": "Vpn 7 дней",
        "name_en": "Vpn 7 days",
        "price_rub": 10000,
        "price_stars": 9000,
        "duration_ru": "1 день",
        "duration_en": "1 day",
        "category": "main",
        "desc_ru": "Не покупать, читайте описание.\n\n✅ Хороший VPN для обхода белых списков.\n\nПереходим по ссылке:\nhttps://t.me/velvet_vpn_bot?start=AW3BJ7lz\n\nВам дают 2 дня бесплатного доступа, а также вводим ещё 2 секретных промокода на 7 дней:\n\nWELCOME_BACK\nJUSTTRY"
    },
    "11": {
        "name_ru": "✅Пак - Обновление ссылок",
        "name_en": "✅Pack - Link Update",
        "price_rub": 699,
        "price_stars": 600,
        "duration_ru": "21 дней",
        "duration_en": "21 days",
        "category": "paki",
        "desc_ru": "Cливaeм ccлыки дpyгиx кaнaлoв, peкoмeндyeм пoкyпaть пocлe пpocмoтpa дpyгиx тapифoв\n\nЕдинственный пак который не входит во всё включено"
    },
    # --- ТЕСТОВЫЙ ТАРИФ ---
    "test": {
        "name_ru": "🧪 ТЕСТОВЫЙ тариф (2 руб)",
        "name_en": "🧪 TEST tariff (2 rub)",
        "price_rub": 2,
        "price_stars": 2,
        "duration_ru": "Тестовый",
        "duration_en": "Test",
        "category": "main",
        "desc_ru": "🧪 Это тестовый тариф для проверки оплаты.\n\nПосле оплаты вы получите ссылку."
    }
}

PROMO_CODES = {
    "VIP10": 10, "SUPER25": 25, "HOMAKE40": 40, "BANK50": 50
}

# --- ИНИЦИАЛИЗАЦИЯ ---
storage = MemoryStorage()
session = AiohttpSession()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML), session=session)
dp = Dispatcher(storage=storage)

class PromoStates(StatesGroup):
    waiting_for_promo = State()

# --- ФУНКЦИЯ ДЛЯ RollyPay ---
async def create_rollypay_payment(amount: int, user_id: int, tariff_key: str, tariff_name: str) -> str:
    url = "https://rollypay.io/api/v1/payments"
    headers = {
        "X-API-Key": ROLLYPAY_API_KEY,
        "Content-Type": "application/json",
        "X-Nonce": str(uuid.uuid4())
    }
    payload = {
        "amount": str(amount),
        "payment_currency": "RUB",
        "order_id": f"order_{user_id}_{tariff_key}_{int(asyncio.get_event_loop().time())}",
        "description": f"Оплата доступа #{user_id}_{tariff_key}",
        "callback_url": ROLLYPAY_CALLBACK_URL,
        "success_url": "https://t.me/blogprivatbot",
        "fail_url": "https://t.me/blogprivatbot",
        "merchant_fee": "true"
    }
    
    async with aiohttp.ClientSession() as client:
        async with client.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("pay_url")
            else:
                error_text = await response.text()
                logging.error(f"Ошибка RollyPay: {response.status} - {error_text}")
                print(f"Ошибка RollyPay: {response.status} - {error_text}")
                return None

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
async def get_lang(state: FSMContext):
    data = await state.get_data()
    return data.get("lang", "ru")

# --- ФУНКЦИЯ СБРОСА ---
async def full_reset():
    print("🔄 Выполняю полный сброс...")
    try:
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            print(f"   📍 Найден вебхук: {webhook_info.url}")
            await bot.delete_webhook(drop_pending_updates=True)
            print("   ✅ Вебхук удалён")
        else:
            print("   ℹ️ Вебхук не был установлен")
        
        await bot.session.close()
        print("   ✅ Старая сессия закрыта")
        
        new_session = AiohttpSession()
        bot.session = new_session
        print("   ✅ Новая сессия создана")
        
        return True
    except Exception as e:
        print(f"   ❌ Ошибка при сбросе: {e}")
        return False

# --- ФУНКЦИЯ ДЛЯ ВЫДАЧИ ССЫЛКИ ---
async def send_access_link(message: Message, tariff_key: str, lang: str):
    """Отправляет ссылку доступа для тарифа"""
    link = TARIFF_LINKS.get(tariff_key)
    
    if tariff_key == "test":
        # Для тестового тарифа - специальное сообщение
        text = LANG[lang]["payment_success_test"]
    elif link:
        # Для обычных тарифов - ссылка
        text = LANG[lang]["payment_success"].format(link=link)
    else:
        # Если ссылка не найдена
        text = "❌ Ссылка для этого тарифа пока не настроена. Обратитесь к администратору."
    
    await message.answer(text, disable_web_page_preview=False)

# --- КЛАВИАТУРЫ ---
def get_main_keyboard(lang):
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text=LANG[lang]["btn_prices"]), KeyboardButton(text=LANG[lang]["btn_subs"])]
    ], resize_keyboard=True)

def get_tariff_keyboard(lang):
    buttons = []
    for key, data in TARIFFS.items():
        if data.get("category") == "main":
            name = data['name_ru'] if lang == 'ru' else data['name_en']
            buttons.append([InlineKeyboardButton(text=f"{name} • {data['price_rub']} 🇷🇺RUB", callback_data=f"tariff_{key}")])
    buttons.append([InlineKeyboardButton(text="👈🏻 Паки", callback_data="show_paki")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_paki_keyboard(lang):
    buttons = []
    for key, data in TARIFFS.items():
        if data.get("category") == "paki":
            name = data['name_ru'] if lang == 'ru' else data['name_en']
            buttons.append([InlineKeyboardButton(text=f"{name} • {data['price_rub']} 🇷🇺RUB", callback_data=f"tariff_{key}")])
    buttons.append([InlineKeyboardButton(text="👈 НАЗАД", callback_data="back_to_prices")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_payment_method_keyboard(tariff_key, discount_percent=0, lang="ru"):
    tariff = TARIFFS[tariff_key]
    
    if discount_percent > 0:
        rub_price = int(tariff['price_rub'] * (1 - discount_percent / 100))
        stars_price = int(tariff['price_stars'] * (1 - discount_percent / 100))
        btn_rub = LANG[lang]["btn_pay_rub_disc"].format(price=rub_price, disc=discount_percent)
        btn_stars = LANG[lang]["btn_pay_stars_disc"].format(price=stars_price, disc=discount_percent)
    else:
        rub_price = tariff['price_rub']
        stars_price = tariff['price_stars']
        btn_rub = LANG[lang]["btn_pay_rub"].format(price=rub_price)
        btn_stars = LANG[lang]["btn_pay_stars"].format(price=stars_price)

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=btn_rub, callback_data=f"pay_rub_{tariff_key}")],
        [InlineKeyboardButton(text=btn_stars, callback_data=f"pay_stars_{tariff_key}")],
        [InlineKeyboardButton(text=LANG[lang]["btn_back"], callback_data="back_to_prices")]
    ])

def get_payment_action_keyboard(payment_url, tariff_key, lang="ru"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANG[lang]["btn_goto_pay"], url=payment_url)],
        [InlineKeyboardButton(text=LANG[lang]["btn_new_link"], callback_data=f"refresh_link_{tariff_key}")],
        [InlineKeyboardButton(text=LANG[lang]["btn_back"], callback_data="back_to_prices")]
    ])

def get_back_to_prices_keyboard(lang="ru"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANG[lang]["btn_to_prices"], callback_data="back_to_prices")]
    ])

# --- НАСТРОЙКА МЕНЮ КОМАНД ---
async def set_bot_commands():
    commands = [
        BotCommand(command="start", description="Запустить бота / Start bot"),
        BotCommand(command="language", description="Сменить язык / Change language"),
        BotCommand(command="reset", description="Сбросить бота (админ)")
    ]
    await bot.set_my_commands(commands)
    print("✅ Команды установлены в меню!")

MAIN_MENU_TEXT = """После выбора и оплаты тарифа бот автоматически тебе выдаст доступ на вход в группу. На случай потери ссылки на нашу випку, ты сможешь всегда её запросить повторно у бота, это бесплатно.

Нажми на тариф чтобы прочесть описание.

Каждый канал отличается"""

# --- ХЭНДЛЕРЫ ---

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    lang = await get_lang(state)
    user_name = message.from_user.first_name
    
    # ИСПРАВЛЕННЫЙ ТЕКСТ ПРИВЕТСТВИЯ
    text = f"""👋 Привет, {user_name}!
Ты попал в наш бот✅

Нажимая на каждый тариф ты видишь краткое описание.

Если бот не доступен пиши мне

Тех.поддержка: @Nastia_sup"""
    
    await message.answer(text, disable_web_page_preview=True)
    await message.answer(MAIN_MENU_TEXT, reply_markup=get_tariff_keyboard(lang))

@dp.message(Command("reset"))
async def cmd_reset(message: Message):
    ADMIN_ID = 8559381302  # ЗАМЕНИ НА СВОЙ ID!
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ У вас нет прав для этой команды!")
        return
    await message.answer("🔄 Выполняю сброс...")
    await full_reset()
    await message.answer("✅ Бот сброшен!")

@dp.message(Command("language"))
async def cmd_language(message: Message, state: FSMContext):
    current_lang = await get_lang(state)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru")],
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")]
    ])
    await message.answer("🌍 Выберите язык:", reply_markup=kb)

@dp.callback_query(F.data.startswith("set_lang_"))
async def process_lang_change(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.replace("set_lang_", "")
    await state.update_data(lang=lang)
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(f"✅ Язык установлен на {'Русский' if lang == 'ru' else 'English'}! Нажмите /start")

@dp.message(F.text.in_([LANG["ru"]["btn_prices"], LANG["en"]["btn_prices"]]))
async def show_prices(message: Message, state: FSMContext):
    lang = await get_lang(state)
    await message.answer(MAIN_MENU_TEXT, reply_markup=get_tariff_keyboard(lang))

@dp.message(F.text.in_([LANG["ru"]["btn_subs"], LANG["en"]["btn_subs"]]))
async def show_subscriptions(message: Message, state: FSMContext):
    lang = await get_lang(state)
    await message.answer(LANG[lang]["subs_menu"], reply_markup=get_back_to_prices_keyboard(lang))

@dp.callback_query(F.data == "back_to_prices")
async def back_to_prices(callback: CallbackQuery, state: FSMContext):
    lang = await get_lang(state)
    await callback.answer()
    await callback.message.edit_text(MAIN_MENU_TEXT, reply_markup=get_tariff_keyboard(lang))

@dp.callback_query(F.data == "show_paki")
async def show_paki(callback: CallbackQuery, state: FSMContext):
    lang = await get_lang(state)
    await callback.answer()
    await callback.message.edit_text(MAIN_MENU_TEXT, reply_markup=get_paki_keyboard(lang))

# --- ГЛАВНЫЙ ОБРАБОТЧИК ТАРИФОВ ---
@dp.callback_query(F.data.startswith("tariff_"))
async def show_tariff_details(callback: CallbackQuery, state: FSMContext):
    tariff_key = callback.data.replace("tariff_", "")
    
    if tariff_key not in TARIFFS:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return
    
    tariff = TARIFFS[tariff_key]
    lang = await get_lang(state)
    data = await state.get_data()
    discount = data.get("discount", 0)
    
    name = tariff['name_ru'] if lang == "ru" else tariff['name_en']
    duration = tariff['duration_ru'] if lang == "ru" else tariff['duration_en']
    desc = tariff['desc_ru'] if lang == "ru" else tariff['desc_en']
    
    if discount > 0:
        new_price = int(tariff['price_rub'] * (1 - discount / 100))
        price_line = f"💰 Цена: <s>{tariff['price_rub']} 🇷🇺RUB</s> → {new_price} 🇷🇺RUB <b>(-{discount}%)</b>"
    else:
        price_line = f"💰 Цена: {tariff['price_rub']} 🇷🇺RUB"
    
    text = f"📋 <b>{name}</b>\n\n{price_line}\nСрок доступа: {duration}\n\n{desc}"
    
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANG[lang]["btn_promo"], callback_data=f"enter_promo_{tariff_key}")],
        [InlineKeyboardButton(text=LANG[lang]["btn_pay"], callback_data=f"choose_pay_{tariff_key}")],
        [InlineKeyboardButton(text=LANG[lang]["btn_back"], callback_data="back_to_prices")]
    ]))

@dp.callback_query(F.data.startswith("enter_promo_"))
async def enter_promo(callback: CallbackQuery, state: FSMContext):
    tariff_key = callback.data.replace("enter_promo_", "")
    
    if tariff_key not in TARIFFS:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return
    
    lang = await get_lang(state)
    await state.update_data(current_tariff=tariff_key)
    await callback.message.edit_text(
        LANG[lang]["enter_promo"],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=LANG[lang]["btn_cancel"], callback_data=f"cancel_promo_{tariff_key}")]])
    )
    await state.set_state(PromoStates.waiting_for_promo)

@dp.callback_query(F.data.startswith("cancel_promo_"))
async def cancel_promo(callback: CallbackQuery, state: FSMContext):
    tariff_key = callback.data.replace("cancel_promo_", "")
    
    if tariff_key not in TARIFFS:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return
    
    lang = await get_lang(state)
    await state.clear()
    await callback.message.delete()
    tariff = TARIFFS[tariff_key]
    data = await state.get_data()
    discount = data.get("discount", 0)
    
    name = tariff['name_ru'] if lang == "ru" else tariff['name_en']
    duration = tariff['duration_ru'] if lang == "ru" else tariff['duration_en']
    desc = tariff['desc_ru'] if lang == "ru" else tariff['desc_en']

    if discount > 0:
        price_line = f"💰 Цена: <s>{tariff['price_rub']} RUB</s> -> {int(tariff['price_rub'] * (1 - discount/100))} RUB <b>(-{discount}%)</b>"
    else:
        price_line = f"💰 Цена: {tariff['price_rub']} RUB"

    text = f"📋 <b>{name}</b>\n\n{price_line}\nСрок доступа: {duration}\n\n{desc}"
    await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANG[lang]["btn_promo"], callback_data=f"enter_promo_{tariff_key}")],
        [InlineKeyboardButton(text=LANG[lang]["btn_pay"], callback_data=f"choose_pay_{tariff_key}")],
        [InlineKeyboardButton(text=LANG[lang]["btn_back"], callback_data="back_to_prices")]
    ]))

@dp.message(PromoStates.waiting_for_promo)
async def process_promo(message: Message, state: FSMContext):
    promo_code = message.text.strip()
    data = await state.get_data()
    tariff_key = data.get("current_tariff")
    lang = await get_lang(state)
    
    if not tariff_key or tariff_key not in TARIFFS:
        await state.clear()
        await message.answer("❌ Ошибка. Попробуйте выбрать тариф заново.")
        return

    if promo_code in PROMO_CODES:
        discount = PROMO_CODES[promo_code]
        await state.update_data(discount=discount)
        await state.clear()
        
        tariff = TARIFFS[tariff_key]
        name = tariff['name_ru'] if lang == "ru" else tariff['name_en']
        new_rub = int(tariff['price_rub'] * (1 - discount / 100))
        
        text = LANG[lang]["promo_success"].format(code=promo_code, discount=discount, name=name, old_rub=tariff['price_rub'], new_rub=new_rub)
        await message.answer(text, reply_markup=get_payment_method_keyboard(tariff_key, discount, lang))
    else:
        await message.answer(LANG[lang]["promo_fail"])

@dp.callback_query(F.data.startswith("choose_pay_"))
async def choose_payment(callback: CallbackQuery, state: FSMContext):
    tariff_key = callback.data.replace("choose_pay_", "")
    
    if tariff_key not in TARIFFS:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return
    
    lang = await get_lang(state)
    data = await state.get_data()
    discount = data.get("discount", 0)
    
    tariff = TARIFFS[tariff_key]
    name = tariff['name_ru'] if lang == "ru" else tariff['name_en']
    duration = tariff['duration_ru'] if lang == "ru" else tariff['duration_en']
    
    if discount > 0:
        show_rub = int(tariff['price_rub'] * (1 - discount / 100))
        price_text = f"<s>{tariff['price_rub']} RUB</s> → {show_rub} RUB (-{discount}%)"
    else:
        show_rub = tariff['price_rub']
        price_text = f"{show_rub} RUB"
    
    text = LANG[lang]["choose_pay"].format(name=name, duration=duration, price_text=price_text, project=PROJECT_NAME)
    await callback.message.edit_text(text, reply_markup=get_payment_method_keyboard(tariff_key, discount, lang))

@dp.callback_query(F.data.startswith("pay_rub_"))
async def process_rub_payment(callback: CallbackQuery, state: FSMContext):
    tariff_key = callback.data.replace("pay_rub_", "")
    
    if tariff_key not in TARIFFS:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return
    
    lang = await get_lang(state)
    data = await state.get_data()
    discount = data.get("discount", 0)
    tariff = TARIFFS[tariff_key]
    
    final_price = int(tariff['price_rub'] * (1 - discount / 100))
    user_id = callback.from_user.id
    
    await state.update_data(pending_tariff=tariff_key)
    
    payment_url = await create_rollypay_payment(final_price, user_id, tariff_key, tariff['name_ru'])
    
    if payment_url:
        name = tariff['name_ru'] if lang == "ru" else tariff['name_en']
        duration = tariff['duration_ru'] if lang == "ru" else tariff['duration_en']
        
        if discount > 0:
            price_line = f"💰 Цена: <s>{tariff['price_rub']} RUB</s> → {final_price} RUB (-{discount}%)\n"
        else:
            price_line = f"💰 Цена: {final_price} RUB\n"
        
        text = LANG[lang]["pay_rub"].format(name=name, duration=duration, price_line=price_line, final=final_price, project=PROJECT_NAME)
        await callback.message.edit_text(text, reply_markup=get_payment_action_keyboard(payment_url, tariff_key, lang))
    else:
        await callback.answer("❌ Ошибка создания платежа. Попробуйте позже или выберите другой способ оплаты.", show_alert=True)

# --- ОБРАБОТЧИК УСПЕШНОЙ ОПЛАТЫ (ВЫДАЁТ ССЫЛКУ) ---
@dp.callback_query(F.data.startswith("payment_success_"))
async def payment_success(callback: CallbackQuery, state: FSMContext):
    tariff_key = callback.data.replace("payment_success_", "")
    lang = await get_lang(state)
    
    await callback.message.delete()
    
    await send_access_link(callback.message, tariff_key, lang)
    await callback.answer("✅ Оплата успешно завершена!")

@dp.callback_query(F.data.startswith("pay_stars_"))
async def process_stars_payment(callback: CallbackQuery, state: FSMContext):
    tariff_key = callback.data.replace("pay_stars_", "")
    
    if tariff_key not in TARIFFS:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return
    
    lang = await get_lang(state)
    data = await state.get_data()
    discount = data.get("discount", 0)
    tariff = TARIFFS[tariff_key]
    name = tariff['name_ru'] if lang == "ru" else tariff['name_en']
    duration = tariff['duration_ru'] if lang == "ru" else tariff['duration_en']
    
    final_price = int(tariff['price_stars'] * (1 - discount / 100))
    demo_stars_url = f"https://t.me/TweetlyStarsBot?start=demo_stars_{tariff_key}"
    
    if discount > 0:
        price_line = f"💰 Цена: <s>{tariff['price_stars']} STARS</s> → {final_price} STARS (-{discount}%)\n"
    else:
        price_line = f"💰 Цена: {final_price} STARS\n"
    
    support = SUPPORT_CONTACT_RU if lang == "ru" else SUPPORT_CONTACT_EN
    text = LANG[lang]["pay_stars"].format(name=name, duration=duration, price_line=price_line, final=final_price, project=PROJECT_NAME, support=support)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LANG[lang]["btn_stars_go"], url=demo_stars_url)],
        [InlineKeyboardButton(text=LANG[lang]["btn_back"], callback_data=f"choose_pay_{tariff_key}")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)

@dp.callback_query(F.data.startswith("refresh_link_"))
async def refresh_link(callback: CallbackQuery, state: FSMContext):
    tariff_key = callback.data.replace("refresh_link_", "")
    
    if tariff_key not in TARIFFS:
        await callback.answer("❌ Тариф не найден", show_alert=True)
        return
    
    tariff = TARIFFS[tariff_key]
    user_id = callback.from_user.id
    final_price = tariff['price_rub']

    payment_url = await create_rollypay_payment(final_price, user_id, tariff_key, tariff['name_ru'])

    if payment_url:
        await callback.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_url)],
                [InlineKeyboardButton(text="🔗 Получить новую ссылку", callback_data=f"refresh_link_{tariff_key}")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_prices")]
            ])
        )
        await callback.answer("✅ Новая ссылка сгенерирована!", show_alert=True)
    else:
        await callback.answer("❌ Ошибка создания новой ссылки. Попробуйте позже.", show_alert=True)

# --- ВЕБ-СЕРВЕР ДЛЯ UPTIMEROBOT ---
async def handle_uptime_check(request):
    """Быстрый ответ для UptimeRobot"""
    return web.Response(text="OK", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_uptime_check)
    app.router.add_get('/health', handle_uptime_check)
    app.router.add_get('/ping', handle_uptime_check)
    
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=port)
    await site.start()
    print(f"✅ Веб-сервер запущен на порту {port}")
    return runner
# --- ЗАПУСК ---
async def main():
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 ЗАПУСК БОТА")
    print("=" * 40)
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Вебхук удалён!")
        await bot.session.close()
        print("✅ Старая сессия закрыта!")
        new_session = AiohttpSession()
        bot.session = new_session
        print("✅ Новая сессия создана!")
    except Exception as e:
        print(f"❌ Ошибка сброса: {e}")
    
    print("=" * 40)
    
    await start_web_server()
    await set_bot_commands()
    
    print("=" * 40)
    print("🤖 Бот полностью готов!")
    print("📱 Команды: /start, /language, /reset")
    print("🧪 Тестовый тариф: 2 рубля")
    print("=" * 40)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
