# Yandex-Practicum Homework Bot

### Описание проекта homework_bot

Homework-bot - это бот в Телеграм для проверки статуса проверки домашней работы в Яндекс-Практикуме. Каждые 10 минут бот делает запрос к API Яндекс-Практикума и, если работа проверена, то присылает результаты проверки в телеграм.


### Как запустить проект:

Создать телеграм-бот:

* добавить в ТГ @BotFather (с галочкой)
* команда /newbot
* указать имя и техническое имя бота (уникальное и должно заканчиваться на bot)
* @BotFather пришлет токен TELEGRAM_TOKEN
* настроить инфу о боте
* добавить своего бота в ТГ (найти по техническому имени)

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/MiladyEmily/homework_bot
```

```
cd hamework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

* Если у вас Linux/macOS

    ```
    source venv/bin/activate
    ```

* Если у вас windows

    ```
    source venv/scripts/activate
    ```

```
python -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Создать файл .env и заполнить в нём следующие :

* PRACTICUM_TOKEN    :    получить токен тут https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a
* TELEGRAM_TOKEN     :    получен при регистрации бота
* TELEGRAM_CHAT_ID   :    добавить в ТГ бота @userinfobot, в ответ пришлет ID

Запустить проект:

```
python homework.py
```
