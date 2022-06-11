import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import ErrorApi, ErrorSendMessage, StatusCodeError

load_dotenv()


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


def get_logger():
    """Задаём параметры логирования."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    fileHandler = logging.FileHandler(
        'bot_logger.log', mode='a', encoding='UTF-8'
    )
    streamHandler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s - %(name)s'
    )
    logger.addHandler(fileHandler)
    logger.addHandler(streamHandler)
    fileHandler.setFormatter(formatter)
    streamHandler.setFormatter(formatter)
    return logger


def send_message(bot, message):
    """Отправка сообщения в телеграмм."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info('Информация отправлена в чат.')
    except Exception as error:
        raise ErrorSendMessage(f'Сбой при отправке сообщения - {error}')


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
        return homework_statuses.json()

    except StatusCodeError as error:
        raise StatusCodeError(f'{error}') from error
    except Exception as error:
        raise ErrorApi(f'Ошибка API - {error}')


def check_response(response):
    """Проверка корректности ответа API."""
    if 'current_date' and 'homeworks' not in response:
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
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    previous_report = {'status': None}
    current_report = {'status': None}

    if not check_tokens():
        logger.critical('Отсутствует одна из переменных окружения')
        logger.debug('Бот не запустился - завершение программы')
        sys.exit(0)

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
                logger.info(message)

                current_report['status'] = message
                if current_report != previous_report:
                    send_message(bot, message)
                    previous_report = current_report.copy()
            else:
                current_report['status'] = 'Нет новых статусов'
                logger.debug('Нет новых статусов')
            current_timestamp = response.get('current_date')

        except ErrorSendMessage as error:
            error_message = f'ErrorSendMessage: {error}'
            logger.error(error_message)

        except Exception as error:
            error_message = f'Сбой в работе программы: {error}'
            logger.error(error_message)

            current_report['status'] = error_message
            if current_report != previous_report:
                send_message(bot, error_message)
                previous_report = current_report.copy()

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logger = get_logger()
    try:
        logger.debug('Запуск программы')
        main()
    except KeyboardInterrupt:
        logger.debug('Выход из программы с клавиатуры')
        sys.exit(0)
