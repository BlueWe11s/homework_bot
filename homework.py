from dotenv import load_dotenv
from http import HTTPStatus
import pyramid.httpexceptions as exc
import json
import logging
import os
import requests
from telebot import TeleBot
import time


from errors import (
    MessageSendError,
)
from text_errors import NO_TOKENS, MESSAGE_SEND_ERROR


load_dotenv()


logging.basicConfig(
    level=logging.DEBUG,
    filename="main.log",
    format="%(asctime)s, %(levelname)s, %(message)s, %(name)s",
)
logger = logging.getLogger(__name__)


PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("CHAT_ID")
const_tokens = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
TOKENS = [
    PRACTICUM_TOKEN,
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID
]

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def check_tokens():
    """Проверка есть ли вся нужная информация."""
    for token_name in const_tokens:
        if globals()[token_name] is None:
            logger.critical(NO_TOKENS.format(token=token_name))
            exit()


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logger.error(MESSAGE_SEND_ERROR.format(error=error))
        raise MessageSendError(MESSAGE_SEND_ERROR.format(error=error))
    else:
        logger.debug("Message send")
    finally:
        return


def get_api_answer(timestamp):
    """Получение ответа от YandexP API."""
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={"from_date": timestamp}
        )
    except requests.RequestException as error:
        raise exc.HTTPClientError(f"Ошибка при выполнении запроса: {error}")
    try:
        request = response.json()
    except json.JSONDecodeError as error:
        raise ValueError(f"Данные не допустимы {error}")
    if response.status_code != HTTPStatus.OK:
        raise ValueError("Статус запроса не 200")
    return request


def check_response(response):
    """Проверка API на правильность."""
    if not isinstance(response, dict):
        raise TypeError("Неверный тип данных," f"{type(response)}")
    if "homeworks" not in response:
        raise KeyError("В ответе API отсутствует ключ homeworks")
    if not isinstance(response["homeworks"], list):
        raise TypeError("Неверный тип данных по ключу homeworks,"
                        f"{type(response)}")
    return response.get("homeworks")


def parse_status(homework):
    """Анализ изменения."""
    status = homework.get("status")
    homework_name = homework.get("homework_name")
    if status is None:
        code_api = f"Ошибка пустое значение status: {status}"
        raise ValueError(code_api)
    elif homework_name is None:
        code_api = f"Ошибка пустое значение homework_name: {homework_name}"
        raise ValueError(code_api)
    elif status not in HOMEWORK_VERDICTS:
        code_api = f"Ошибка невозможное значение status: {status}"
        raise ValueError(code_api)
    verdict = HOMEWORK_VERDICTS[homework["status"]]
    return (
        "Изменился статус проверки работы "
        f'"{homework["homework_name"]}". {verdict}'
    )


def main():
    """Основная логика работы бота."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - 500
    last_message = None
    check_tokens()
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if response["homeworks"][0] == [last_message]:
                logger.debug("Отсутсвует изменение статутса")
            message_text = parse_status(response["homeworks"][0])
            last_message = message_text
            send_message(bot, message_text)
        except Exception as error:
            send_message(bot, f"{error}")
            logger.error(f"{error}")
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    main()
