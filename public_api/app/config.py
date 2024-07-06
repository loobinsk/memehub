import logging
from logging.handlers import TimedRotatingFileHandler
import os

def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "app.log")

    # Создание обработчика для ротации логов по времени
    handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1)
    handler.suffix = "%Y-%m-%d"
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    # Конфигурация корневого логгера
    logging.basicConfig(level=logging.INFO, handlers=[handler])

    # Возвращаем корневой логгер
    return logging.getLogger("memehub")

