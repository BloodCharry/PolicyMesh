import multiprocessing
import os

# Настройки для Docker
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# Количество воркеров
workers_per_core = 1
cores = multiprocessing.cpu_count()
default_web_concurrency = workers_per_core * cores + 1
workers = int(os.getenv("WEB_CONCURRENCY", default_web_concurrency))

# Класс воркера - для FastAPI
worker_class = "uvicorn.workers.UvicornWorker"

# Логирование
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"
errorlog = "-"

# Таймауты
timeout = 120
keepalive = 5
