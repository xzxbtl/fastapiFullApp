import copy
import logging
import os

from colorama import Fore, Style

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '')
os.makedirs(LOG_DIR, exist_ok=True)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN + Style.BRIGHT,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        record_copy = copy.copy(record)
        if record_copy.levelno in self.COLORS:
            record_copy.levelname = (f"{self.COLORS[record_copy.levelno]}"
                                     f"{record_copy.levelname}{Style.RESET_ALL}")
            record_copy.msg = (f"{self.COLORS[record_copy.levelno]}"
                               f"{record_copy.msg}{Style.RESET_ALL}")
        return super().format(record_copy)


# Выввод в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
))

# Выввод в файл только уровень INFO
file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'app.log'))


class InfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno < logging.WARNING


file_handler.addFilter(InfoFilter())

file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - "
    "%(message)s - %(pathname)s:%(lineno)d"
))

# Выввод в файл только ошибок

error_handler = logging.FileHandler(os.path.join(LOG_DIR, 'errors.log'))
error_handler.setLevel(logging.WARNING)
error_handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - "
    "%(message)s - %(pathname)s:%(lineno)d"
))


class SensitiveFilter(logging.Filter):
    def filter(self, record):
        return not any(word in record.getMessage().lower()
                       for word in ['password', 'token', 'secret'])


logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)

# Обработчики
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.addHandler(error_handler)

logger.addFilter(SensitiveFilter())
