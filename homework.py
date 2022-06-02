import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import ErrorApi, MyErrorSendMessage, StatusCodeError

load_dotenv()

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
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
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


def send_message_error(bot, message):
    """Отправка сообщения об ошибке в телеграмм."""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    while True:
        logger.error(message)
        time.sleep(RETRY_TIME)


def send_message(bot, message):
    """Отправка сообщения в телеграмм."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Сообщение отправлено в чат.')
    except Exception as error:
        raise MyErrorSendMessage(f'Сбой при отправке сообщения - {error}')


def get_api_answer(current_timestamp):
    """Проверка респонса."""
    try:
        timestamp = current_timestamp or int(time.time())
        params = {'from_date': timestamp}
        homework_statuses = requests.get(
            url=ENDPOINT, headers=HEADERS, params=params
        )
        if homework_statuses.status_code != HTTPStatus.OK:
            raise StatusCodeError(
                'Ошибка при запросе к основному API - '
                f'ERROR {homework_statuses.status_code}'
            )
    except StatusCodeError as error:
        raise StatusCodeError(f'{error}') from error
    except Exception as error:
        raise ErrorApi(f'Ошибка API - {error}')

    return homework_statuses.json()


def check_response(response):
    """Проверка корректности ответа API."""
    if list(response) != ['homeworks', 'current_date']:
        raise TypeError(f'Неверный формат данных {type(response)}')
    if not isinstance(response, dict):
        raise TypeError(f'Неверный формат данных {type(response)}')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError(f'Неверный формат данных {type(homeworks)}')

    return homeworks


def parse_status(homework):
    """Проверка статуса работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка доступности переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    return False


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Отсутсвует одна из переменных окружения')
        sys.exit(logger.debug('Бот не запустился - завершение программы'))

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logger.debug('Бот запущен успешно')
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                message = parse_status(homework)
                send_message(bot, message)

            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)

        except StatusCodeError as error:
            message = f'StatusCodeError: {error}'
            send_message_error(bot, message)

        except ErrorApi as error:
            message = f'ErrorApi: {error}'
            send_message_error(bot, message)

        except MyErrorSendMessage as error:
            message = f'MyErrorSendMessage: {error}'
            send_message_error(bot, message)

        except TypeError as error:
            message = f'TypeError: {error}'
            send_message_error(bot, message)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message_error(bot, message)
        else:
            logger.debug('Нет новых статусов')


if __name__ == '__main__':
    try:
        logger.debug('Запуск программы')
        main()
    except KeyboardInterrupt:
        logger.debug('Выход из программы с клавиатуры')
        sys.exit(0)
