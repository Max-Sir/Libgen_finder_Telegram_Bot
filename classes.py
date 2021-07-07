from abc import ABC, abstractmethod

class ReturnValue(object):
    """
    Класс занимается возвратом значений от баз данных
    """
    def __init__(self, ok, value, error=None):
        """
        :param ok: Успешен ли запрос? True, False
        :param value: Значение которое возвращается (любой объект), если есть ошибка - то просто ее легкое,
        человеческое, текстовое описание, внутреннее описание ошибки класть в error
        :param error: Если есть ошибка - тогда ее внутреннее описание положить сюда
        """
        self._ok = ok
        self._value = value
        self._error = error

    def ok(self):
        return self._ok

    def value(self):
        return self._value

    def error(self):
        return self._error

class BotModule(ABC):
    """
    Абстрактный класс для всех модулей бота, модулями считаю любой самостоятельный раздел бота, будь то поиск где либо
    или предложку
    """
    @abstractmethod
    def install_handlers(self, end_conversation):
        """
        Абстрактный метод модуля, устанавливает хендлеры необходимое модулю для работы, будь то отрабатывание на кнопку
        или слово
        :param end_conversation: Метод который должен вызываться при окончании работы с модулем, в основном нужен для
        закрытия разговорных хендлеров, поэтому так и назван
        :return:
        """
        pass