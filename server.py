import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from typing import Any, Dict, List
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Путь к файлу логов (будет создан рядом с server.py)
LOG_FILE = "bot_server.log"

# Создаём форматировщик: время, уровень, имя модуля, сообщение
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 1. Обработчик для файла (с ротацией — чтобы файл не рос бесконечно)
# maxBytes=5*1024*1024 = 5 МБ; backupCount=3 = храним 3 старых файла
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)  # В файл пишем INFO и выше (можно DEBUG для отладки)

# 2. Обработчик для консоли (чтобы видеть логи при запуске через run.bat)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Настраиваем корневой логгер
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)  # Минимальный уровень, который будет перехватываться
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger(__name__)
logger.info("Сервер инициализирован. Логирование настроено.")

# Импортируем логику из handlers.py
load_dotenv()
from handlers import parse_update, handle_message_logic

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)


app = FastAPI()

@app.post("/webhook")
async def handle_webhook(request: Request) -> JSONResponse:
    client_host = request.client.host if request.client else "unknown"

    try:
        payload = await request.json()
    except Exception as e:
        logger.error("Invalid JSON: %s", e)
        return JSONResponse(status_code=200, content={"status": "ok", "handled": False, "error": "invalid_json"})

    logger.info("=== ВХОДЯЩИЙ ВЕБХУК ===")
    # logger.info("IP: %s", client_host)
    from_data = payload.get("updates", [{}])[0].get("from", {})
    chat_data = payload.get("updates", [{}])[0].get("chat", {})
    text = payload.get("updates", [{}])[0].get("text")
    user_login = from_data.get("login")
    display_name = from_data.get("display_name")

    logger.info(
        "Получено сообщение: login=%s, name=%s, text='%s'",
        user_login,
        display_name,
        text
    )
    logger.info(payload)

    updates = payload.get("updates", [])
    if not isinstance(updates, list):
        logger.warning("Поле 'updates' не является списком")
        return JSONResponse(status_code=200, content={"status": "ok", "handled": False, "error": "updates_not_list"})

    responses: List[Dict[str, Any]] = []

    for idx, update in enumerate(updates):
        parsed = parse_update(update)
        logger.info(parsed)
        if not parsed:
            logger.warning("Не удалось распарсить update #%d", idx)
            responses.append({"update_index": idx, "status": "skipped", "reason": "parse_error"})
            continue

        if not parsed.get("chat_id") or not parsed.get("user_id"):
            logger.warning("Update #%d: отсутствуют chat_id или user_id", idx)
            responses.append({"update_index": idx, "status": "skipped", "reason": "missing_ids"})
            continue

        logger.info(
            "Обрабатываем update #%d: chat_id=%s user_id=%s text=%s",
            idx, parsed["chat_id"], parsed["user_id"], parsed.get("text")
        )

        try:
            reply_text = await handle_message_logic(parsed)
            responses.append({
                "update_index": idx,
                "status": "handled",
                "chat_id": parsed["chat_id"],
                "reply": reply_text,
            })
        except Exception as e:
            logger.exception("Ошибка при обработке update #%d: %s", idx, e)
            responses.append({
                "update_index": idx,
                "status": "error",
                "reason": str(e),
            })

    result = {
        "status": "ok",
        "handled_count": sum(1 for r in responses if r["status"] == "handled"),
        "errors_count": sum(1 for r in responses if r["status"] == "error"),
        "details": responses,
    }
    # logger.info("result")
    # logger.info(result)

    return JSONResponse(status_code=200, content=result)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)