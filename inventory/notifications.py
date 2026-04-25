import os
import requests


def send_low_stock_alert(product):
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_ADMIN_CHAT_ID')
    if not token or not chat_id:
        return

    text = (
        f'⚠️ *Kam qolgan mahsulot*: {product.name}\n'
        f'*Qoldiq*: {product.quantity}\n'
        f'*Minimal limit*: {product.threshold}\n'
        f'*Kategoriya*: {product.category.name}'
    )

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown'}
    try:
        requests.post(url, json=payload, timeout=10)
    except requests.RequestException:
        pass
