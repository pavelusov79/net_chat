"""Декораторы"""
from _datetime import datetime
import sys
import logging
import traceback

# os.path.split(sys.argv[0])[1]
if sys.argv[0].find('client') == -1:
    LOGGER = logging.getLogger('server')
else:
    LOGGER = logging.getLogger('client')


# Реализация в виде функции
def log(func):
    """Функция-декоратор"""
    def log_saver(*args, **kwargs):
        """Обертка"""
        res = func(*args, **kwargs)
        LOGGER.debug(f'{datetime.now()} Была вызвана функция {func.__name__} c параметрам'
                     f'и {args}, {kwargs}. '
                     f'Вызов из модуля {func.__module__}. Вызов из'
                     f' функции {traceback.format_stack()[0].strip().split()[-1]}.')
        return res
    return log_saver


