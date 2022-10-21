# NovelVerse    [![Built with Cookiecutter Django](https://img.shields.io/badge/built%20with-Cookiecutter%20Django-ff69b4.svg?logo=cookiecutter)](https://github.com/cookiecutter/cookiecutter-django/)


> Автоматизированное приложение веб-новел.

> Версия: 1.2.0


## Настройки `config/settings`

Moved to [settings](http://cookiecutter-django.readthedocs.io/en/latest/settings.html).

## Жизненный цикл

![image](https://i.postimg.cc/XJMCWvVm/lifecycle.png)

### Изображения

#### Главная страница
![image](https://i.postimg.cc/FRpxhjwB/1.png)

#### Жанры
![image](https://i.postimg.cc/NF7F34VK/3.png)

#### Рейтинг
![image](https://i.postimg.cc/fyWzx4zB/2.png)

#### Теги
![image](https://i.postimg.cc/dQWzBdD6/4.png)

#### Библиотека пользователя
![image](https://i.postimg.cc/KcgHnVSG/5.png)

#### Глава книги
![image](https://i.postimg.cc/HnG3ZYDp/6.png)

### Type checks

Running type checks with mypy:

    $ mypy novel
    
    
### Тестовое покрытие

Команды для запуска тестов, проверки покрытия unit-тестамы, генерация HTML-отчета:

    $ coverage run -m pytest
    $ coverage html
    $ open htmlcov/index.html


### Тестирование

    $ pytest
    $ pytest -s (with i/o logging)

Тест отдельного модуля    

    $ pytest /tests/test_models.py
    
Тест только с декоратором `@pytest.mark.slow`

    $ pytest -v -m slow

Инверсия предыдущей команды - исключить тесты с декоратором `@pytest.mark.slow`)
    
    $ pytest -v -m "not slow" 

### RabbitMQ

    # Default port
    http://localhost:15672/

#### Linux install:

    $ sudo apt-get install -y erlang
    $ sudo apt-get install rabbitmq-server
    
    $ systemctl enable rabbitmq-server
    $ systemctl start rabbitmq-server
    
    $ systemctl status rabbitmq-server


#### Команды:

    # if managment console disabled
    $ rabbitmq-plugins enable rabbitmq_management
  
    # add user
    $ rabbitmqctl add_user user1337 password
    # change password
    $ rabbitmqctl change_password user1337 NEWPASSWORD
    # set role
    $ rabbitmqctl set_user_tags user1337 administrator
    # set permissions
    $ rabbitmqctl set_permissions -p / user1337 ".*" ".*" ".*"
    
    # automaticly starts service on windows
    $ rabbitmq-service stop  
    $ rabbitmq-service install  
    $ rabbitmq-service start  

#### Errors:

    # if node error - run as admin and navigate to rabbitmq/sbin
    $ rabbitmq-service remove
    $ rabbitmq-service install
    $ rabbitmq-service start
    
    # if rabbitmqctl auth error
    # navitage to %userprofile% - delete .erlang.cookie
    # copy .erlang.cookie from C:\Windows\System32\config\systemprofile
    # paste to %userprofile%

### Redis

#### Linux install

        $ sudo apt-get install redis-server
        $ redis-cli -v

#### Команды
    
    # Redis server restart
    $ sudo service redis-server restart
    
    # Redis cli basic use
    $ redis-cli
        set user:1 "admin"
        get user:1
    
    # Start/Stop redis server
    sudo service redis-server stop
    sudo service redis-server start



### Celery

#### Запустить локально beat + 1 worker:

    $ celery -A config.celery_app beat -S django -l info

#### Запустить воркера

    $ celery -A config.celery_app worker --loglevel=DEBUG/INFO

#### Продакшн воркер

    $ celery -A config.celery_app worker -l info -B -E
    
#### Errors

    # if windows ValueError
    $ set FORKED_BY_MULTIPROCESSING=1
