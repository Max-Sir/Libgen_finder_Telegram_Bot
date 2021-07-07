# Только не сломай...
# Не суди строго, код - говно, я знаю, но он работает, так что не трогай

# А, да, чуть не забыл - csv-шку можно взять на сайтах libgen.lc или зеркалах, там вообще-то была и просто sql база, но когда я увидел тот раздел - код для миграции с csv на sqlite\fts3 уже был написан
import sqlite3 as sqlite
import csv

ALL_FIELDS = [
"id",
"title",
"volumeinfo",
"series",
"periodical",
"author",
"year",
"edition",
"publisher",
"city",
"pages",
"pages2",
"language",
"topic",
"library",
"issue",
"identifier",
"issn",
"asin",
"udc",
"lbc",
"ddc",
"lcc",
"doi",
"googlebookid",
"openlibraryid",
"commentary",
"dpi",
"color",
"cleaned",
"orientation",
"paginated",
"scanned",
"bookmarked",
"searchable",
"filesize",
"extension",
"md5",
"generic",
"visible",
"locator",
"local",
"timeadded",
"timelastmodified",
"coverurl",
"tags",
"identifierwodash",
"pagesinfile",
"descr",
"toc",
"sha1",
"sha256",
"crc32",
"edonkey",
"aich",
"tth",
"btih",
"torrent"]
PATH_TO_CSV = "libgen_content.csv"

connection = sqlite.connect("lg_db_2.sql")
cursor = connection.cursor()

cursor.execute("""CREATE VIRTUAL TABLE if not exists libgen_book USING fts3
(tags TEXT,
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
#all_text TEXT,
tokenize=unicode61)""") # ЗАПОМНИ ТОКЕНАЙЗЕР, Я ПОЛ ЧАСА ГОНЯЛ ПО МАНАМ ПРЕЖДЕ ЧЕМ ЕГО НАЙТИ!!!

sql = """INSERT INTO libgen_book (rowid, 
        tags, 
        language, 
        title, 
        volumeinfo, 
        edition, 
        series, 
        author, 
        year, 
        identifier, 
        publisher, 
        pages, 
        issn, 
        asin, 
        filesize, 
        extension, 
        md5, 
        local, 
        coverurl, 
        identifierwodash) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
i = 0

with open(PATH_TO_CSV, encoding="utf-8") as file:
    for row in csv.reader(file):
        try:
            book = dict(zip(ALL_FIELDS, row))
            if book["language"] in "Russian" or book["language"] in "English":
                pass
            else:
                continue
            exi = cursor.execute(sql, (book["id"], book["tags"], book["language"].strip(), book["title"], book["volumeinfo"], book["edition"], book["series"], book["author"], book["year"].strip(), book["identifier"], book["publisher"], book["pages"], book["issn"], book["asin"], book["filesize"], book["extension"], book["md5"], book["local"], book["coverurl"], book["identifierwodash"],)) #all,))

            print(str(i) + "  " + str(exi.rowcount) + str(book))
            i = i + 1
        except Exception as e:
            print(e)
            continue
    cursor.execute("COMMIT")
    connection.commit()
    cursor.execute("INSERT INTO libgen_book(libgen_book) VALUES('optimize')")
    connection.commit()

print("=========================================")
print("=================ГОТОВО==================")
print("=========================================")

