import os
import django
import logging
from django.db.models import F
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sklad_project.settings')
django.setup()

from inventory.models import Product
from inventory.services import apply_inventory_operation
from inventory.notifications import send_low_stock_alert

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ADMIN_CHAT_ID = os.getenv('TELEGRAM_ADMIN_CHAT_ID')

if not BOT_TOKEN:
    raise RuntimeError('TELEGRAM_BOT_TOKEN muhim. .env faylga qo‘shing.')

bot = Bot(token=BOT_TOKEN, parse_mode='HTML')
dp = Dispatcher()

keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='/stock'), KeyboardButton(text='/low_stock')],
    [KeyboardButton(text='/in'), KeyboardButton(text='/out')],
], resize_keyboard=True)


def send_bot_message(chat_id, text):
    try:
        bot.send_message(chat_id, text, parse_mode='HTML')
    except Exception:
        logging.exception('Telegram yuborishda xatolik yuz berdi')


@dp.message(Command(commands=['start']))
async def cmd_start(message: types.Message):
    await message.reply(
        'Salom! Ombor boshqaruv botiga xush kelibsiz.\n\n'
        'Tezkor buyruqlar:\n'
        '/stock - barcha mahsulotlar qoldig‘i\n'
        '/low_stock - kam qolgan mahsulotlar\n'
        '/in <product_id> <amount> - kirim\n'
        '/out <product_id> <amount> - chiqim',
        reply_markup=keyboard,
    )


@dp.message(Command(commands=['stock']))
async def cmd_stock(message: types.Message):
    products = Product.objects.select_related('category').order_by('name')[:20]
    if not products:
        return await message.reply('Hozircha mahsulotlar mavjud emas.')

    lines = ['<b>Ombordagi mahsulotlar</b>']
    for product in products:
        lines.append(f'{product.id}. {product.name} - {product.quantity} ({product.category.name})')
    await message.reply('\n'.join(lines))


@dp.message(Command(commands=['low_stock']))
async def cmd_low_stock(message: types.Message):
    products = Product.objects.filter(quantity__lte=F('threshold')).select_related('category')
    if not products:
        return await message.reply('Hozircha kam qolgan mahsulot yo‘q.')

    lines = ['<b>Kam qolgan mahsulotlar</b>']
    for product in products:
        lines.append(f'{product.id}. {product.name} - {product.quantity} (threshold {product.threshold})')
    await message.reply('\n'.join(lines))


def parse_operation_args(text: str):
    parts = text.split()
    if len(parts) < 3:
        return None, None
    try:
        product_id = int(parts[1])
        quantity = int(parts[2])
        return product_id, quantity
    except ValueError:
        return None, None


@dp.message(Command(commands=['in']))
async def cmd_in(message: types.Message):
    product_id, quantity = parse_operation_args(message.text)
    if not product_id or not quantity:
        return await message.reply('Foydalanish: /in <product_id> <quantity>')

    try:
        product = Product.objects.get(pk=product_id)
        operation = apply_inventory_operation(product=product, user=None, quantity=quantity, operation_type='in', note='Telegram orqali kirim')
        if product.low_stock():
            send_low_stock_alert(product)
        await message.reply(f'Kirim muvaffaqiyatli: {product.name} +{quantity}. Yangi qoldiq: {product.quantity}')
    except Product.DoesNotExist:
        await message.reply('Mahsulot topilmadi.')
    except Exception as exc:
        await message.reply(f'Xato: {exc}')


@dp.message(Command(commands=['out']))
async def cmd_out(message: types.Message):
    product_id, quantity = parse_operation_args(message.text)
    if not product_id or not quantity:
        return await message.reply('Foydalanish: /out <product_id> <quantity>')

    try:
        product = Product.objects.get(pk=product_id)
        operation = apply_inventory_operation(product=product, user=None, quantity=quantity, operation_type='out', note='Telegram orqali chiqim')
        if product.low_stock():
            send_low_stock_alert(product)
        await message.reply(f'Chiqim muvaffaqiyatli: {product.name} -{quantity}. Yangi qoldiq: {product.quantity}')
    except Product.DoesNotExist:
        await message.reply('Mahsulot topilmadi.')
    except Exception as exc:
        await message.reply(f'Xato: {exc}')


async def main():
    logging.info('Bot ishga tushmoqda...')
    await dp.start_polling(bot)


if __name__ == '__main__':
    import asyncio
    from django.db.models import F
    asyncio.run(main())
