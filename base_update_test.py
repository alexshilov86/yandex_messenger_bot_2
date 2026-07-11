import asyncio
import os, json
import logging
from dotenv import load_dotenv

# 1. Сначала загружаем переменные окружения (до любых импортов, где они могут использоваться)
load_dotenv()

# Настройка логгера специально для теста (чтобы видеть всё чётко)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_base")

# 2. Импортируем функции из твоего основного файла (где они определены)
# Если функции лежат в server.py — так:
from data_from_base_update import update_data_from_base, need_update
# Если в handlers.py или другом файле — поменяй на from handlers import ...


async def test_update_data_from_base():
    """
    Минимальный тест: запускает обновление базы и выводит результат в лог.
    Адаптирован под структуру: { sheet_name: { headers: [...], rows: [[...]] } }
    """
    logger.info("=== ЗАПУСК ТЕСТА update_data_from_base ===")
    success = await update_data_from_base()

    if success:
        logger.info("✅ Тест пройден: база успешно обновлена.")

        local_file = os.getenv("LOCAL_DATA_FILE", "base_data.json")
        info_file = os.getenv("UPDATE_INFO_FILE", "update_base_info.json")

        for fname in [local_file, info_file]:
            exists = os.path.exists(fname)
            size = os.path.getsize(fname) if exists else 0
            logger.info("Файл %s: %s, размер %d байт", fname, "есть" if exists else "нет", size)

        # --- ПРАВИЛЬНЫЙ ПРЕВЬЮ ДАННЫХ ---
        try:
            with open(local_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.info("--- Превью данных по листам ---")
            for sheet_name, sheet_data in data.items():
                headers = sheet_data.get("headers", [])
                rows = sheet_data.get("rows", [])

                logger.info("Лист: '%s' | колонок: %d | строк: %d",
                            sheet_name, len(headers), len(rows))
                logger.info("  Заголовки: %s", headers)

                # Безопасный вывод первых 3 строк (если есть)
                for i, row in enumerate(rows[:3]):
                    logger.info("  Строка %d: %s", i, row)

                if len(rows) > 3:
                    logger.info("  ... и ещё %d строк", len(rows) - 3)
        except Exception as e:
            logger.error("Не удалось прочитать локальную базу для превью: %s", e)
    else:
        logger.error("❌ Тест не пройден: ошибка при обновлении базы.")

    return success

async def main():
    await test_update_data_from_base()

if __name__ == "__main__":
    asyncio.run(main())

