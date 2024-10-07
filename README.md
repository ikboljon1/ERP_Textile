# Название вашего проекта

[![Python version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![Django version](https://img.shields.io/badge/django-4.1-green.svg)](https://www.djangoproject.com/download/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Установка
   ```bash
   python3 -m venv venv
   source venv/Scripts/activate
   pip install -r requirements.txt
   python manage.py makemigrations APP
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
