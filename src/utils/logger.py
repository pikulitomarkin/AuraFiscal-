"""
Sistema de logging centralizado usando Loguru.
"""
from loguru import logger
from config.settings import settings
import sys


def setup_logger():
    """Configura o sistema de logging da aplicação."""
    
    # Remove handlers padrão
    logger.remove()
    
    # Console output
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # File output
    log_file = settings.base_dir / settings.LOG_FILE
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    logger.info(f"Sistema de logging inicializado - Level: {settings.LOG_LEVEL}")
    
    return logger


# Inicializa o logger
app_logger = setup_logger()
