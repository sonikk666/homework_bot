import logging
import os
import sys
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
import telegram

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler(
    'bot_logger.log', encoding='UTF-8', maxBytes=50000000, backupCount=5
)
formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s - %(name)s'
)
logger.addHandler(handler)
handler.setFormatter(formatter)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения в телеграмм."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Сообщение отправлено в чат.')
    except Exception as error:
        logger.error(f'Сбой при отправке сообщения: {error}')


def get_api_answer(current_timestamp):
    """Проверка респонса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    homework_statuses = requests.get(
        url=ENDPOINT, headers=HEADERS, params=params
    )

    if homework_statuses.status_code != HTTPStatus.OK:
        logger.error(
            'Ошибка при запросе к основному API:'
            + f'{homework_statuses.status_code}'
        )
        raise requests.ConnectionError(
            f'Ошибка {homework_statuses.status_code}'
        )

    return homework_statuses.json()


def check_response(response):
    """Проверка корректности ответа API."""
    if type(response) is not dict:
        logger.error(f'Неверный формат данных {type(response)}')
        raise TypeError('Неверный формат данных')
    homeworks = response.get('homeworks')
    if type(homeworks) is not list:
        logger.error(f'Неверный формат данных {type(homeworks)}')
        raise TypeError('Неверный формат данных')
    if list(response) != ['homeworks', 'current_date']:
        logger.error('Неожиданный ответ от API')

    return homeworks


def parse_status(homework):
    """Проверка статуса работы."""
    try:
        homework_name = homework.get('homework_name')
        homework_status = homework.get('status')
    except LookupError:
        logger.debug('Отсутствие в ответе новых статусов')

    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    logger.critical('Отсутсвует одна из переменных окружения')
    return False


def main():
    """Основная логика работы бота."""
    print('Запуск программы')
    logger.debug('Запуск программы')
    if check_tokens() is True:
        logger.debug('Бот запущен успешно')
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        current_timestamp = int(time.time())

        while True:
            try:
                response = get_api_answer(current_timestamp)
                homeworks = check_response(response)
                if len(homeworks):
                    homework = homeworks[0]
                    message = parse_status(homework)
                    send_message(bot, message)

                current_timestamp = response.get('current_date')
                time.sleep(RETRY_TIME)

            except KeyboardInterrupt:
                print('Выход из программы с клавиатуры')
                logger.debug('Выход из программы с клавиатуры')
                sys.exit(0)
            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                logger.error(message)
                time.sleep(RETRY_TIME)
            else:
                logger.debug('В ответе новых статусов нет')
    else:
        print('Бот не запустился - завершение программы')
        logger.debug('Бот не запустился - завершение программы')
        exit()


if __name__ == '__main__':
    main()
