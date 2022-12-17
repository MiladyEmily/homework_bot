import time
import sys
import logging
from logging import StreamHandler
from http import HTTPStatus
from typing import Any, List, Union

import telegram
import requests

from exceptions import NoEnvVariable, StatusNot200
from settings import (RETRY_PERIOD, ENDPOINT, PRACTICUM_TOKEN,
                      TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, HEADERS,
                      HOMEWORKS_NUMBER)


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
HOMEWORK_KEYS = ['status',
                 'homework_name']


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def type_check(text: str, variable: Any, type_: type) -> None:
    """Вызывает исключение, если значение переменной не того типа."""
    if not isinstance(variable, type_):
        raise TypeError(text)


def value_check(item: str, list_: List[str]) -> None:
    """Вызывает исключение, если нет нужного ключа."""
    if item not in list_:
        text = f'Ключа {item} нет в {list_}'
        raise KeyError(text)


def check_tokens() -> None:
    """Проверяет наличие всех переменных окружения."""
    invisible_vars = ''
    env_vars = {
        'PRACTICUM_TOKEN ': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN ': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID ': TELEGRAM_CHAT_ID,
    }
    for key, var in env_vars.items():
        if not var:
            invisible_vars += key
    if invisible_vars != '':
        logging.critical(('Отсутствует обязательная переменная окружения:'
                          f' {invisible_vars}. '
                          'Работа бота принудительно остановлена.'))
        raise NoEnvVariable(('Отсутствует обязательная'
                            f' переменная окружения: {invisible_vars}'))


def send_message(bot: telegram.bot.Bot, message: str) -> Union[bool, None]:
    """Отправляет сообщение в чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'Отправлено сообщение: {message}')
        return True
    except Exception as error:
        logging.error(f'Не смог отправить сообщение {message} в чат: {error}')


def get_api_answer(timestamp: float) -> Union[None, dict]:
    """Получает ответ от API Яндекс.Домашки."""
    try:
        payload = {'from_date': timestamp}
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params=payload)
        status = homework_statuses.status_code
        if status != HTTPStatus.OK:
            raise StatusNot200(f'Статус-код ответа API не 200, a {status}')
        return homework_statuses.json()
    except requests.RequestException:
        logging.error('Нет ответа от API')


def check_response(response: dict) -> Union[dict, None]:
    """Проверяет ответ на соответствие документации."""
    type_check('объект ответа - не словарь', response, dict)
    value_check('current_date', response.keys())
    value_check('homeworks', response.keys())
    type_check('current_date - не целое число',
               response['current_date'],
               int)
    type_check('homeworks - не список', response['homeworks'], list)
    if not response['homeworks']:
        logging.debug('Обновлений нет')
        return None
    homeworks = response['homeworks']
    current_homework = homeworks[0]
    type_check('элемент homeworks - не словарь', current_homework, dict)
    return current_homework


def parse_status(homework: dict) -> str:
    """Проверяет статус и формирует текст сообщения."""
    for item in HOMEWORK_KEYS:
        value_check(item, homework.keys())
    status = homework['status']
    if status not in HOMEWORK_VERDICTS.keys():
        text = f'Недопустимый статус {status}'
        raise ValueError(text)
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_in_process(bot: telegram.bot.Bot) -> bool:
    """Проверяет, не является ли этот проект последним в курсе."""
    response = get_api_answer(0)
    if len(response['homeworks']) == HOMEWORKS_NUMBER:
        send_message(bot, '🎉🥂Поздравляю! Ты завершил курс!😍🎊')
        return False
    return True


def main() -> None:
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = ['']
    send_message(bot, ('Привет! Я Homework_Bot и буду отслеживать '
                       'статус твоей домашки на Практикуме :)'))
    bot_working = True
    while bot_working:
        check_tokens()
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework)
                send_message(bot, message)
                last_message[0] = message
                if homework['status'] == 'approved':
                    bot_working = check_in_process(bot)
            timestamp = response['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if send_message(bot, message):
                last_message[0] = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filename='main.log',
        filemode='w',
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    try:
        main()
    except KeyboardInterrupt:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        send_message(bot, 'Я выключаюсь. Но скоро снова буду с тобой!')
