import Channel.channelDB as channelDB
import os

path_to_db = "test_channel_db"


def create_table_test():
    remove_db()

    data = create_db_and_table()

    if os.path.exists(path_to_db):
        print("[+] Существование файла базы данных")
    else:
        print("[ - ] Файл базы данных не создан")

    if data.ok():
        print("[+] Создание таблиц")
    else:
        print("[ - ] Ошибка создания таблиц: {} | {}".format(data.value(), data.error()))

    remove_db()


def insert_data_test():
    remove_db()

    create_db_and_table()

    with channelDB.Update(path_to_db) as db:
        data = db.add_post(10, 1000, "test text #@$!*$&@*(&*' or 1=1 -- -")

    if data.ok():
        print("[+] Добавление записи")
    else:
        print("[ - ] Ошибка добавления записи: {} | {}".format(data.value(), data.error()))

    remove_db()

def insert_eql_data_test():
    remove_db()

    create_db_and_table()

    with channelDB.Update(path_to_db) as db:
        db.add_post(10, 1000, "data 1")
        data = db.add_post(10, 1000, "data 2")

    if data.ok():
        print("[ - ] Добавлены одинаковые записи")
    else:
        print("[+] Одинаковые записи не добавляются (не должны)")

    remove_db()

def search_in_table_test():
    remove_db()

    create_db_and_table()

    with channelDB.Update(path_to_db) as db:
        db.add_post(10, 1000, "test text #@$!*$&@*(&*' or 1=1 -- -")

    with channelDB.Search(path_to_db) as db:
        data = db.in_text("test", 1, 0)

    if data.ok():
        if len(data.value()) == 1:
            print("[+] Поиск одной строки")
        else:
            print("[ - ] Ошибка при поиске, не найдено строк: {} | {}".format(data.value(), data.error()))
    else:
        print("[ - ] Ошибка при поиске, поиск завершился с ошибкой: {} | {}".format(data.value(), data.error()))

    remove_db()


def search_many_rows_test():
    remove_db()

    create_db_and_table()

    with channelDB.Update(path_to_db) as db:
        db.add_post(1, 1, "row 1")
        db.add_post(2, 1, "row 2")
        db.add_post(3, 1, "row 3")
        db.add_post(4, 1, "row 4")
        db.add_post(5, 1, "row 5")
        db.add_post(1, 2, "row 6 in ch 2")

    def print_res(ok, descr):
        if ok:
            print("[+] {}".format(descr))
        else:
            print("[ - ] {}".format(descr))

    with channelDB.Search(path_to_db) as db:
        data = db.in_text("row", 3, 0)
        if data.ok():
            if len(data.value()) == 3:
                print_res(True, "Поиск с лимитом 3")
            else:
                print_res(False, "Поиск с лимитом 3 - мало записей на выходе")
        else:
            print_res(False, "Поиск с лимитом 3 {} | {}".format(data.value(), data.error()))

        data = db.in_text("1 OR 3 OR 4", 3, 0)
        if data.ok():
            if len(data.value()) == 3:
                print_res(True, "Поиск через OR")
            else:
                print_res(False, "Поиск через OR - мало записей на выходе")
        else:
            print_res(False, "Поиск через OR {} | {}".format(data.value(), data.error()))

        data = db.in_text("channel_id:1", 10, 0)
        if data.ok():
            if len(data.value()) >= 5:
                print_res(True, "Поиск с указанием столбца channel_id:1")
            else:
                print_res(False, "Поиск с указанием столбца channel_id:1 - мало записей на выходе")
        else:
            print_res(False, "Поиск с указанием столбца channel_id:1 {} | {}".format(data.value(), data.error()))

    remove_db()


def delete_rows_by_rowid_test():
    remove_db()

    create_db_and_table()

    with channelDB.Update(path_to_db) as db:
        db.add_post(1, 1, "row 1")
        db.add_post(2, 1, "row 2")
        db.add_post(3, 1, "row 3")
        db.add_post(4, 1, "row 4")
        db.add_post(5, 1, "row 5")
        db.add_post(1, 2, "row 6 in ch 2")

    with channelDB.Update(path_to_db) as db:
        data = db.delete_post_by_rowid(1)

    if data.ok():
        print("[+] Удаление строки по rowid")
    else:
        print("[ - ] Удаление строки по rowid/ {} | {}".format(data.value(), data.error()))

    remove_db()

def delete_rows_by_post_and_channel_id():
    remove_db()

    create_db_and_table()

    with channelDB.Update(path_to_db) as db:
        db.add_post(1, 1, "row 1")
        db.add_post(2, 1, "row 2")
        db.add_post(3, 1, "row 3")
        db.add_post(4, 1, "row 4")
        db.add_post(5, 1, "row 5")
        db.add_post(1, 2, "row 6 in ch 2")

    with channelDB.Update(path_to_db) as db:
        data = db.delete_post_by_post_and_channel_id(1, 5)

    if data.ok():
        print("[+] Удаление строки по channel и post id")
    else:
        print("[ - ] Удаление строки по channel и post id / {} | {}".format(data.value(), data.error()))

    remove_db()


def create_db_and_table():
    with channelDB.DBConnect(path_to_db) as db:
        data = db.create_table()
    return data

def remove_db():
    try:
        os.remove(path_to_db)
    except:
        pass

print("\n[=] Тестирование базы канала\n")
create_table_test()
insert_data_test()
insert_eql_data_test()
search_in_table_test()
search_many_rows_test()
delete_rows_by_rowid_test()
delete_rows_by_post_and_channel_id()
print("\n[=] Тестирование базы канала завершено\n")