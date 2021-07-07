import sqlite3
import config
import datetime
import classes

class DBConnect(object):

    def __enter__(self):
        # self._cursor.execute("PRAGMA foreign_keys=on;")
        return self

    def __exit__(self, exec_type, exc_value, exc_trace):
        self._cursor.close()
        self._connection.commit()
        self._connection.close()

    def __init__(self):
        self.__path = config.path_to_statistics
        self._connection = sqlite3.connect(self.__path)
        self._connection.row_factory = sqlite3.Row
        self._cursor = self._connection.cursor()


    def create_table(self):
        sql = """CREATE TABLE if not exists statistics
        (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 
        user_id INTEGER, 
        action TEXT,
        datetime INTEGER)"""

        try:
            self._cursor.execute(sql)
            self._connection.commit()
            return classes.ReturnValue(True, "Создание базы статистики")
        except Exception as e:
            return classes.ReturnValue(False, "Ошибка создания базы статистики", error=e)


class RecordStatisticsDB(DBConnect):
    def record_action(self, user_id: int, action: str):
        if user_id == None or action == None:
            return classes.ReturnValue(False, "Неправильно переданы параметры в write_request")

        sql = """INSERT INTO statistics (user_id, action, datetime) VALUES (?, ?, ?)"""

        try:
            self._cursor.execute(sql, (user_id, action, datetime.datetime.now().strftime("%Y%m%d"),))
            self._connection.commit()
            return classes.ReturnValue(True, "Действие записано")
        except Exception as e:
            return classes.ReturnValue(False, "Ошибка добавления действия", error=e)


class GetStatisticsDB(DBConnect):
    def getAllStatistics(self):
        sql = """SELECT datetime as date, action as action, count(*) as action_count, count(DISTINCT user_id) as user_count FROM statistics GROUP BY datetime, action ORDER BY datetime DESC LIMIT 24"""

        try:
            data = self._cursor.execute(sql).fetchall()
        except Exception as e:
            return classes.ReturnValue(False, "Ошибка поиска статистики", error=e)

        if len(data) == 0:
            return classes.ReturnValue(False, "Стастистики не найдено")

        return classes.ReturnValue(True, data)






