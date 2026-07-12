import os
import logging
import aiohttp
from typing import Dict, Any
import asyncio
from find_nakl_from_base import msg_by_nakl
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("YANDEX_BOT_TOKEN", "")
SEND_MESSAGE_URL = "https://botapi.messenger.yandex.net/bot/v1/messages/sendText/"  # <-- замени на реальный URL из документации


async def send_message_to_chat(chat_id: str, text: str) -> bool:
    """
    Отправляет сообщение в чат через API Яндекс Мессенджера.
    Использует заголовки строго по документации:
      Authorization: OAuth <токен>
      Content-Type: application/json
    """
    if not chat_id or not text:
        logger.warning("Некорректные параметры для отправки: chat_id=%s, text=%s", chat_id, text)
        return False

    if not BOT_TOKEN:
        logger.error("КРИТИЧЕСКАЯ ОШИБКА: YANDEX_BOT_TOKEN не найден! Проверьте .env и наличие load_dotenv() в server.py.")
        return False

    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    # Строго как в curl примере
    headers = {
        "Authorization": f"OAuth {BOT_TOKEN}",
        "Content-Type": "application/json",
    }

    logger.info("Отправка сообщения: chat_id=%s", chat_id)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SEND_MESSAGE_URL, 
                json=payload, 
                headers=headers, 
                timeout=10
            ) as resp:
                
                logger.info("Статус ответа API: %d", resp.status)
                
                if resp.status == 200:
                    logger.info("Сообщение успешно отправлено.")
                    return True
                elif resp.status == 401:
                    logger.error("Ошибка 401: Неверный токен. Проверьте YANDEX_BOT_TOKEN в .env")
                    return False
                elif resp.status == 403:
                    logger.error("Ошибка 403: Доступ запрещён. Возможно, у бота нет прав на отправку.")
                    return False
                else:
                    body = await resp.text()
                    logger.error("Ошибка отправки (status=%d): %s", resp.status, body)
                    return False
                    
    except asyncio.TimeoutError:
        logger.error("Таймаут при отправке сообщения.")
        return False
    except Exception as e:
        logger.exception("Исключение при отправке сообщения: %s", e)
        return False


def parse_update(update: Dict[str, Any]) -> Dict[str, Any] | None:
    """Парсит один update из массива updates."""
    try:
        from_data = update.get("from", {})
        chat_data = update.get("chat", {})

        return {
            "user_id": from_data.get("id"),
            "user_login": from_data.get("login"),
            "user_name": from_data.get("display_name"),
            "chat_id": chat_data.get("id"),
            "chat_type": chat_data.get("type"),
            "text": update.get("text"),
            "timestamp": update.get("timestamp"),
            "message_id": update.get("message_id"),
            "payload_id": update.get("payload_id"),
            "update_id": update.get("update_id"),
        }
    except Exception as e:
        logger.error("Ошибка парсинга update: %s", e)
        return None


async def handle_message_logic(parsed: Dict[str, Any]) -> str:
    """
    Бизнес-логика: превращает текст в верхний регистр и отправляет ответ.
    """
    text = parsed.get("text", "")
    user_name = parsed.get("user_name", "пользователь")
    chat_id = parsed.get("chat_id")

    if not text:
        response_text = f"Привет, {user_name}! В твоём сообщении нет текста."
    else:
        response_text = msg_by_nakl(text) # функция, которая принимает текст пользователя и формирует ответ

    # Отправляем ответ в чат
    if chat_id:
        success = await send_message_to_chat(chat_id, response_text)
        if not success:
            # Даже если отправка не удалась, возвращаем текст как «результат логики»
            logger.warning("Не удалось отправить ответ в чат %s, но логика выполнена", chat_id)
    else:
        logger.warning("chat_id отсутствует, отправка невозможна")

    return response_text
