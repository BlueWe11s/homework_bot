from dotenv import load_dotenv
import os
import requests
from telebot import TeleBot
import logging
import time
from http import HTTPStatus
import json
from errors import (UndocumentedStatusError, IncorrectStatusRequest,
                    IncorrectAPIRequest, MessageSendError)


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


def check_tokens():
    """Проверка есть ли вся нужная информация."""
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
    """Отправка сообщения."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except requests.RequestException as error:
        logger.error('Message send error')
        raise MessageSendError(f'Ошибка отправки сообщения {error}')
    else:
        logger.debug('Message send')
    finally:
        return


def get_api_answer(timestamp):
    """Получение ответа от YandexP API."""
    try:
        response = requests.get(ENDPOINT, headers=HEADERS,
                                params={'from_date': timestamp})
        if response.status_code != HTTPStatus.OK:
            raise IncorrectStatusRequest('Статус запроса не 200')
    except requests.RequestException as error:
        raise IncorrectAPIRequest(f'Ошибка при выполнении запроса: {error}')
    except json.JSONDecodeError as error:
        raise ValueError(f'Данные не допустимы {error}')
    return response.json()


def check_response(response):
    """Проверка API на правильность."""
    if not isinstance(response, dict):
        raise TypeError('Неверный тип данных,'
                        f'{type(response)}')
    elif 'homeworks' not in response:
        raise KeyError('В ответе API отсутствует ключ homeworks')
    elif not isinstance(response['homeworks'], list):
        raise TypeError('Неверный тип данных по ключу homeworks,'
                        f'{type(response)}')
    elif not isinstance(response['current_date'], int):
        raise TypeError('Неверный тип данных по ключу current_date,'
                        f'{type(response)}')
    return response.get('homeworks')


def parse_status(homework):
    """Анализ изменения."""
    status = homework.get('status')
    homework_name = homework.get('homework_name')
    if status is None:
        code_api = f'Ошибка пустое значение status: {status}'
        logger.error(code_api)
        raise UndocumentedStatusError(code_api)
    elif homework_name is None:
        code_api = f'Ошибка пустое значение homework_name: {homework_name}'
        logger.error(code_api)
        raise UndocumentedStatusError(code_api)
    elif status not in HOMEWORK_VERDICTS:
        code_api = f'Ошибка невозможное значение status: {status}'
        logger.error(code_api)
        raise UndocumentedStatusError(code_api)
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return (f'Изменился статус проверки работы '
            f'"{homework["homework_name"]}". {verdict}')


def main():
    """Основная логика работы бота."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - 500
    check_tokens()
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if response['homeworks'][0] == []:
                logger.debug('Отсутсвует изменение статутса')
            message_text = parse_status(response['homeworks'][0])
            send_message(bot, message_text)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
