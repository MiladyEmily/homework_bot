import telegram
import requests
import time
import os
import sys
from dotenv import load_dotenv
import logging
from logging import StreamHandler
from http import HTTPStatus

from exceptions import NoEnvVariable, StatusNot200


load_dotenv()
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD = 600
POLLING_INTERVAL_SECONDS = 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def error_level_log(context, log_text):
    """Обрабатывает лог уровня Error.
    Создаёт лог уровня error и
    отправляет сообщение об этой ошибке в чат ТГ
    """
    logging.error(log_text)
    send_message_and_log(context.bot, log_text)


def type_check(text, variable, type):
    """Вызывает исключение, если значение переменной не того типа."""
    if not isinstance(variable, type):
        raise TypeError(text)


def value_check(item, list):
    """Вызывает исключение, если нет нужного ключа."""
    if item not in list:
        text = f'Ключа {item} нет в {list}'
        raise KeyError(text)


def send_message_and_log(context, text, log_text):
    """Отправляет сообщение в чат."""
    try:
        if context.bot_data['last_message'] != text:
            context.bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
            context.bot_data['last_message'] = text
            logging.debug(f'{log_text}: {text}')
    except Exception as error:
        logging.error(f'Сбой при отправке сообщения в ТГ: {error}')


def check_tokens():
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


def send_message(bot, message):
    """Отправляет сообщение в чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'Отправлено сообщение: {message}')
        return True
    except Exception as error:
        logging.error(f'Не смог отправить сообщение {message} в чат: {error}')


def get_api_answer(timestamp):
    """Получает ответ от API Яндекс.Домашки."""
    try:
        payload = {'from_date': timestamp}
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params=payload)
        status = homework_statuses.status_code
        if status != HTTPStatus.OK:
            raise StatusNot200('Статус-код ответа API не 200')
        return homework_statuses.json()
    except requests.RequestException:
        logging.error('Нет ответа от API')


def check_response(response):
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
    homework_keys = ['status',
                     'homework_name']
    for item in homework_keys:
        value_check(item, current_homework.keys())
    return current_homework


def parse_status(homework):
    """Проверяет статус и формирует текст сообщения."""
    homework_keys = ['status',
                     'homework_name']
    for item in homework_keys:
        value_check(item, homework.keys())
    status = homework['status']
    if status not in HOMEWORK_VERDICTS.keys():
        text = f'Недопустимый статус {status}'
        raise ValueError(text)
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = ['']
    send_message(bot, ('Привет! Я Homework_Bot и буду отслеживать '
                       'статус твоей домашки на Практикуме :)'))
    while True:
        try:
            check_tokens()
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework)
                send_message(bot, message)
                last_message[0] = message
            timestamp = int(time.time())
        except NoEnvVariable:
            raise NoEnvVariable('Отсутствуют обязательные '
                                'переменные окружения')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if send_message(bot, message):
                last_message[0] = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
