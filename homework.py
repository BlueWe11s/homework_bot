from dotenv import load_dotenv
import os
import requests
from telebot import TeleBot
import logging
import time
from datetime import datetime


load_dotenv()


logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log', 
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
)
logger = logging.getLogger(__name__)
logger.addHandler(
    logging.StreamHandler()
)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class EmptyDictionaryError(Exception):
    """Пустой словарь"""


class UndocumentedStatusError(Exception):
    """Недокументированный статус"""


class ApiWrongFormat(Exception):
    """Полученный API неверного формата"""


def check_tokens():
    """Проверка есть ли вся нужная информация"""
    no_tokens = (
        'Программа принудительно остановлена. '
        'Отсутствует обязательная переменная окружения:')
    if PRACTICUM_TOKEN is None:
        logger.critical(
            f'{no_tokens} PRACTICUM_TOKEN')
        exit()
    elif TELEGRAM_TOKEN is None:
        logger.critical(
            f'{no_tokens} TELEGRAM_TOKEN')
        exit()
    elif TELEGRAM_CHAT_ID is None:
        logger.critical(
            f'{no_tokens} CHAT_ID')
        exit()
    else:
        return True


def send_message(bot, message):
    """Отправка сообщения"""
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(timestamp):
    """Получение ответа от YandexP API"""
    try:
        homework_statuses = requests.get(ENDPOINT, headers=HEADERS,
                                         params={'from_date': 0})
    except Exception as error:
        raise error

    return homework_statuses.json()


def check_response(response):
    if 'homeworks' not in response or 'current_date' not in response:
        raise ApiWrongFormat('Полученный API неверного формата')


def parse_status(homework):
    """Анализ изменения"""
    # status = homework.get('status')
    # homework_name = homework.get('homework_name')
    # if status is None:
    #     code_api = f'Ошибка пустое значение status: {status}'
    #     logger.error(code_api)
    #     raise UndocumentedStatusError(code_api)
    # elif homework_name is None:
    #     code_api = f'Ошибка пустое значение homework_name: {homework_name}'
    #     logger.error(code_api)
    #     raise UndocumentedStatusError(code_api)
    # verdict = HOMEWORK_VERDICTS[status]
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return (f'Изменился статус проверки работы '
            f'"{homework["homework_name"]}". {verdict}')
    # return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = 0
    check_tokens()
    response = get_api_answer(timestamp)
    # check_response(response)
    message_text = parse_status(response['homeworks'][0])
    send_message(bot, message_text)


if __name__ == '__main__':
    main()
