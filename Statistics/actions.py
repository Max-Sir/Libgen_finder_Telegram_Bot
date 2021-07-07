import logging
from Statistics import RecordStatisticsDB


class AbsAction(object):
    def __init__(self, action_name):
        self._action_name = action_name

    def __str__(self):
        return self._action_name

    def GetName(self):
        return self._action_name


class StartAction(AbsAction):
    def __init__(self):
        AbsAction.__init__(self, "Команда старт")


class MainMenuAction(AbsAction):
    def __init__(self):
        AbsAction.__init__(self, "Главное меню")


class SearchInChannelAction(AbsAction):
    def __init__(self):
        AbsAction.__init__(self, "Поиск на канале")


class SearchInLibgenAction(AbsAction):
    def __init__(self):
        AbsAction.__init__(self, "Поиск в Libgen")


def StatisticsDecorator(ActionClass:AbsAction):
    from telegram import Update

    def decorator(func):

        def wrapped(*args, **kwargs):
            func(*args, **kwargs)  # Дергаем задекорированную функцию

            user_id = None  # Идем писать отчеты
            for arg in args:  # Бегаем по параметрам
                if isinstance(arg, Update):  # в поисках объекта Update
                    if arg.effective_user:  # если нашли - смотрим на юзера
                        user_id = arg.effective_user.id
                        break
                    elif arg.callback_query:  # если нет юзера - смотрим на коллбеки кнопки от телеги
                        user_id = arg.callback_query.from_user.id
                        break
                    else:  # не нашли - плачем
                        logging.error("user_id not found")

            if user_id:
                with RecordStatisticsDB() as _db:  # Пишем в статистику
                    _db.record_action(user_id, ActionClass.GetName())

        return wrapped

    return decorator
