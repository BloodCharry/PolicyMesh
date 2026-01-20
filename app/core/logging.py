import logging
import sys
from typing import Any

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """
    Настройка перехвата стандартных логов и вывода их в JSON формате через structlog.
    """

    # Конфигурация shared processors для structlog и stdlib logging
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    # Настройка structlog
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Настройка стандартного logging
    handler = logging.StreamHandler(sys.stdout)

    # structlog для форматирования стандартных логов
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=shared_processors,
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Настройка логгеров Uvicorn и FastAPI, чтобы они не дублировали логи
    for _log in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        logging.getLogger(_log).handlers = []
        logging.getLogger(_log).propagate = True
