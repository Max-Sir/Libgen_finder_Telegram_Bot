"""CREATE TABLE if not exists libgen_book
(id INTEGER PRIMARY KEY NOT NULL,
tags TEXT,
language TEXT,
title TEXT,
volumeinfo TEXT,
edition TEXT,
series TEXT,
author TEXT,
year TEXT,
identifier TEXT,
publisher TEXT,
pages TEXT,
issn TEXT,
asin TEXT,
filesize TEXT,
extension TEXT,
md5 TEXT,
local TEXT,
coverurl TEXT,
identifierwodash TEXT,
all_text TEXT)"""

import config
import sqlite3
import classes
# TODO Тут какой то дурдом, надо исправить
ALL_FIELD = ("tags",
        "language",
        "title",
        "volumeinfo",
        "edition",
        "series",
        "author",
        "year",
        "identifier",
        "publisher",
        "pages",
        "issn",
        "asin",
        "filesize",
        "extension",
        "md5",
        "local",
        "coverurl",
        "identifierwodash",)


class DBConnect(object):

    def __enter__(self):
        #self._cursor.execute("PRAGMA foreign_keys=on;")
        return self
    
    def __exit__(self, exec_type, exc_value, exc_trace):
        self._cursor.close()
        self._connection.commit()
        self._connection.close()

    def __init__(self):
        self.__path = config.path_to_lgdb
        self._connection = sqlite3.connect(self.__path)
        self._cursor = self._connection.cursor()


class BookSearch(DBConnect):
    def search(self, text, limit, offset):
        _text = text #("%" + "%".join(list(filter(None, text.split(' ')))) + "%").upper()
        sql = "SELECT * FROM libgen_book WHERE libgen_book MATCH :text ORDER BY language DESC, year DESC LIMIT :limit OFFSET :offset"
        try:
            data = {"text": _text, "limit": limit, "offset": offset}
            execute = self._cursor.execute(sql, data)
            rows = execute.fetchall()
            if len(rows) == 0:
                return classes.ReturnValue(False, "Ничего не найдено")
            book_list = []
            for row in rows:
                print(row)
                book_list.append(dict(zip(ALL_FIELD, row)))

            return classes.ReturnValue(True, book_list)
        except Exception as e:
            return classes.ReturnValue(False, "Ошибка при поиске", error=e)
