# Homework_bot

## Python telegram bot

### Описание

Даёт возможность:

- Запрашивает статус домашней работы с API Я.Практикума
- Если есть измененияс с прошлого сообщения, присылает в чат владельцу
- Один раз сообщает о том, если изменений нет

### Технологии

Python 3.7

Python_telegram_bot 13.7

Python_dotenv 0.19.0

### Как запустить проект в dev-режиме

Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone https://github.com/sonikk666/homework_bot

cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```bash
python3 -m venv env

source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```bash
python3 -m pip install --upgrade pip

pip install -r requirements.txt
```

Запустить проект:

```bash
python3 homework_bot/manage.py
```

### Автор

Никита Михайлов
