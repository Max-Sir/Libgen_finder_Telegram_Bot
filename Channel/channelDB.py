import sqlite3
import config
import classes


class DBConnect(object):

    def __enter__(self):
        self._cursor.execute("PRAGMA foreign_keys=on")
        return self

    def __exit__(self, exec_type, exc_value, exc_trace):
        self._cursor.close()
        self._connection.commit()
        self._connection.close()

    def __init__(self, path_to_db = None):
        if path_to_db:
            self.__path = path_to_db
        else:
            self.__path = config.path_to_db

        self._connection = sqlite3.connect(self.__path)
        self._connection.row_factory = sqlite3.Row
        self._cursor = self._connection.cursor()

    def create_table(self):
        try:
            # Основная таблица с данными по постам
            sql = """CREATE TABLE if not exists posts(
                post_id INTEGER,
                channel_id INTEGER,
                text TEXT,
                CONSTRAINT unique_post UNIQUE (post_id, channel_id)
            )"""

            # Полнотекстовый поиск на fts4 с использование данных основной таблицы posts
            sql_fts = """CREATE VIRTUAL TABLE if not exists fts_posts USING fts4(content="posts", tokenize=unicode61)"""

            # Триггеры для обновления полнотекстового поиска
            sql_trigger = """CREATE TRIGGER IF NOT EXISTS posts_before_update BEFORE UPDATE ON posts BEGIN
                                DELETE FROM fts_posts WHERE docid=old.rowid;
                            END;
                            CREATE TRIGGER IF NOT EXISTS posts_before_delete BEFORE DELETE ON posts BEGIN
                                DELETE FROM fts_posts WHERE docid=old.rowid;
                            END;
                            
                            CREATE TRIGGER IF NOT EXISTS posts_after_update AFTER UPDATE ON posts BEGIN
                                INSERT INTO fts_posts(docid, post_id, channel_id, text) VALUES(new.rowid, new.post_id, new.channel_id, new.text);
                            END;
                            CREATE TRIGGER IF NOT EXISTS posts_after_inserts AFTER INSERT ON posts BEGIN
                                INSERT INTO fts_posts(docid, post_id, channel_id, text) VALUES(new.rowid, new.post_id, new.channel_id, new.text);
                            END;"""

            self._cursor.execute(sql)
            self._cursor.execute(sql_fts)
            self._cursor.executescript(sql_trigger)

            return classes.ReturnValue(True, "Базы данных канала созданы")

        except Exception as e:
            return classes.ReturnValue(False, "Ошибка создания баз данных канала", error=e)


class Search(DBConnect):
    def in_text(self, text, limit, offset):
        sql = """SELECT * FROM fts_posts WHERE fts_posts MATCH :text LIMIT :limit OFFSET :offset"""

        try:
            # Выполняем выборку с текстом, экранирование текста нам обеспечивает execute
            execute = self._cursor.execute(sql, {"text": text, "limit": limit, "offset": offset})

            # Выборка всех полученных результатов (возвращает list())
            rows = execute.fetchall()

            # Проверка на наличие хоть чего нибудь
            if len(rows) == 0:
                return classes.ReturnValue(False, "Ничего не найдено")

            return classes.ReturnValue(True, rows)

        except Exception as e:
            return classes.ReturnValue(False, "Ошибка при поиске", error=e)

    def by_channel_and_post_id(self, channel_id, post_id):
        sql = """SELECT * FROM posts WHERE channel_id = :channel_id AND post_id = :post_id"""

        try:
            execute = self._cursor.execute(sql, {"channel_id": channel_id, "post_id": post_id})

            rows = execute.fetchall()

            if len(rows) == 0:
                return classes.ReturnValue(False, "Ничего не найдено")

            return classes.ReturnValue(True, rows)

        except Exception as e:
            return classes.ReturnValue(False, "Ошибка при поиске", error=e)


class Update(DBConnect):
    def add_post(self, post_id, channel_id, text):
        sql = """INSERT INTO posts(post_id, channel_id, text) VALUES(:post_id, :channel_id, :text)"""

        try:
            self._cursor.execute(sql, {"post_id": post_id, "channel_id": channel_id, "text": text})
            self._connection.commit()
            return classes.ReturnValue(True, "Пост добавлен")

        except sqlite3.IntegrityError as e:
            return classes.ReturnValue(False, "Ошибка, такая запись уже есть", error=e)
        except Exception as e:
            return classes.ReturnValue(False, "Ошибка добавления поста", error=e)

    def delete_post_by_post_and_channel_id(self, channel_id, post_id):
        sql = """DELETE FROM posts WHERE channel_id = :channel_id AND post_id = :post_id"""

        try:
            execute = self._cursor.execute(sql, {"channel_id": channel_id, "post_id": post_id})

            if execute.rowcount > 0:
                return classes.ReturnValue(True, "Пост {}|{} удален".format(channel_id, post_id))

            return classes.ReturnValue(False, "Пост {}|{} не найден".format(channel_id, post_id))
        except Exception as e:
            return classes.ReturnValue(False, "Ошибка удаления поста {}|{}".format(channel_id, post_id), error=e)

    def delete_post_by_rowid(self, rowid):
        sql = """DELETE FROM posts WHERE rowid = :rowid"""

        try:
            execute = self._cursor.execute(sql, {"rowid": rowid})

            if execute.rowcount > 0:
                return classes.ReturnValue(True, "Пост {} удален".format(rowid))

            return classes.ReturnValue(False, "Пост {} не найден".format(rowid))

        except Exception as e:
            return classes.ReturnValue(False, "Ошибка удаления поста {}".format(rowid), error=e)
