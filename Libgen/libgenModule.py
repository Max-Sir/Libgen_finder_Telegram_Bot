import config
import telegram
import telegram.ext
import logging
import Libgen.searchInDB as LgSearch
from Statistics import StatisticsDecorator
from Statistics import SearchInLibgenAction
from classes import BotModule


class LibgenModule(BotModule):
    def __init__(self, updater: telegram.ext.Updater, dispatcher: telegram.ext.dispatcher):
        self.updater = updater
        self.dispatcher = dispatcher
        self.tge = telegram.ext  # Алиас для telegram.ext
        self.tg = telegram  # Алиас для telegram

    def install_handlers(self, end_conversation):
        # Алиасы
        filters = self.tge.Filters
        message = self.tge.MessageHandler
        conversation = self.tge.ConversationHandler
        callbackQuery = self.tge.CallbackQueryHandler

        # Диалог поиска по Libgen
        search_in_libgen_conv = conversation(
            entry_points=[
                           message(filters.regex(config.search_in_lg_button) & filters.private, self.send_keyb_for_libgen),
                           message(filters.regex(config.prefix_start_in_lg) & filters.private, self.send_keyb_for_libgen)
                         ],
            states={
                0: [
                    message(filters.regex(config.back_button) & filters.private, end_conversation),  # Кнопка назад
                    message(filters.regex(config.help_in_fts3_button) & filters.private, self.send_fts3_help),
                    message(filters.text & filters.private, self.search_in_libgen)
                    ]  # Поиск
            },
            fallbacks=[message(filters.regex(config.back_button) & filters.private, end_conversation)], allow_reentry=True)

        # Отрабатывание на кнопку "Да" в вопросе про продолжение поиска по libgen
        continue_srch_libgen_btn = callbackQuery(self.query_continue_search_libgen, pattern="continue_libgen")

        self.dispatcher.add_handler(search_in_libgen_conv)
        self.dispatcher.add_handler(continue_srch_libgen_btn)

    # Колбеки для поиска на либгене
    def send_keyb_for_libgen(self, update, context):
        """
        Отправляет клавиатуру для поиска на libgen
        :param update:
        :param context:
        :return:
        """
        keyb = config.into_lg_search_reply_markup
        reply_markup = self.tg.ReplyKeyboardMarkup(keyb, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(config.start_in_libgen_msg, reply_markup=reply_markup, parse_mode=self.tg.ParseMode.HTML)
        return 0

    @StatisticsDecorator(SearchInLibgenAction())
    def search_in_libgen(self, update, context):
        """
        Отрабатывает на любой текст для поиска в libgen
        :param update: update от python-telegram-bot
        :param context: контекст от python-telegram-bot
        :return: None
        """
        if len(update.effective_message.text) > 100 or len(update.effective_message.text) < 3:
            update.message.reply_text("От 3-х до 100 символов")
            return

        self.do_search_lg(context, update.effective_chat.id, update.effective_message.text)

    def query_continue_search_libgen(self, update, context):
        """
        Отрабатывает на нажатие кнопки "продолжить"
        :param update: update от python-telegram-bot
        :param context: контекст от python-telegram-bot
        :return: None
        """
        query = update.callback_query
        context.bot.delete_message(query.message.chat_id, query.message.message_id)

        self.do_search_lg(context, query.message.chat_id)

    @telegram.ext.run_async
    def do_search_lg(self, context, chat_id, text=None, offset_lg=None, limit=config.send_libgen_limit):
        """
        Поиск по libgen
        Если text не None и offset_ch равен None - Выполняем поиск по тексту со стандартным offset_ch (= 0)
        Если text не None и offset_ch не None - Выполняем поиск по тексту с заданным смещением (offset_ch)
        Если text равен None - Ищем текст в пользовательских данных и выполняем поиск с ним, если не нашли текст - отправляем ошибку
        :param context: Контекст от python-telegram-bot
        :param chat_id: это понятно
        :param text: текст для поиска
        :param offset_lg: смещение того самого поиска
        :param limit: лимит выдачи
        :return: None
        """

        if text:
            if not offset_lg:
                offset_lg = 0
        else:
            text = context.user_data.get("last_search_lg", None)
            offset_lg = context.user_data.get("offset_lg", 0)

            if text == None:
                context.bot.send_message(chat_id, "Мы не можем найти твой последний запрос, попробуй еще раз :)")
                return

        with LgSearch.BookSearch() as _db:
            data = _db.search(text, limit, offset_lg)

        if not data.ok():
            context.bot.send_message(chat_id, data.value())
            return

        for book in data.value():
            keyb = [[self.tg.InlineKeyboardButton("Download", url="http://libgen.lc/ads.php?md5={}".format(book["md5"]))],
                    [self.tg.InlineKeyboardButton("Mirrors", url="http://libgen.lc/item/index.php?md5={}".format(book["md5"]))]]

            reply_markup = self.tg.InlineKeyboardMarkup(keyb)
            context.bot.send_message(chat_id, self.__get_descr_libgen(book), parse_mode=self.tg.ParseMode.HTML, reply_markup=reply_markup)

        if len(data.value()) >= limit:
            keyb = [[self.tg.InlineKeyboardButton("Да", callback_data="continue_libgen")]]
            reply_markup = self.tg.InlineKeyboardMarkup(keyb)
            context.bot.send_message(chat_id, "Продолжаем поиск в LibGen?", reply_markup=reply_markup)
            context.user_data["last_search_lg"] = text

        # Так, эта штука снесена сюда по одной причине - если найдется постов меньше лимита - смещение все равно
        # прибавится и после случайного повторного нажатия кнопки далее - бот пошлет юзера нахрен (сказав, что ни черта
        # не нашел)
        context.user_data["offset_lg"] = offset_lg + limit

    def send_fts3_help(self, update, context):
        """
        Отправляет сообщение с описанием возможностей поиска по libgen
        :param update:
        :param context:
        :return:
        """
        update.message.reply_text(config.help_in_fts3, parse_mode=self.tg.ParseMode.HTML)
        return

    @staticmethod
    def __get_descr_libgen(dict_book):
        """
        Получает описание в человеческом виде, весь смысл телодвижений с if - генерация описания на ходу, дабы не
        забивать выдачу пустыми строками
        :param dict_book:
        :return:
        """
        db = dict_book

        blank = "".join(
            (  # Кортеж, это работает, не вини себя 😭
                ("Title: <b>" + db["title"] + "</b>") if db["title"] else "", "\n",
                ("<a href='http://libgen.lc/covers/{}'> </a>".format(db["coverurl"])) if db["coverurl"] else "",
                "\n",
                ("Language: <code>" + db["language"] + "</code>\n") if db["language"] else "",
                ("Author: <code>" + db["author"] + "</code>\n") if db["author"] else "",
                ("Year: <code>" + db["year"] + "</code>\n") if db["year"] else "",
                ("Pages: <code>" + db["pages"] + "</code>\n") if db["pages"] else "",
                ("ISBN: <code>" + db["identifier"] + "</code>\n") if db["identifier"] else "",
                ("Publisher: <code>" + db["publisher"] + "</code>\n") if db["publisher"] else "",
                ("Volume info: <code>" + db["volumeinfo"] + "</code>\n") if db["volumeinfo"] else "",
                ("Edition: <code>" + db["edition"] + "</code>\n") if db["edition"] else "",
                ("Series: <code>" + db["series"] + "</code>\n") if db["series"] else "",
                ("Extension: <code>" + db["extension"] + "</code>\n") if db["extension"] else "",
                ("MD5: <code>" + db["md5"] + "</code>\n") if db["md5"] else "",
                ("Filesize: <code>" + db["filesize"] + "</code>\n") if db["filesize"] else "",
                "\n",
                ("Tags: <code>" + db["tags"] + "</code>\n\n") if db["tags"] else "",
                "Download: <a href='http://libgen.lc/ads.php?md5={}'>---LINK---</a>\n".format(db["md5"]),
                "Mirrors: <a href='http://libgen.lc/item/index.php?md5={}'>---LINK---</a>\n".format(db["md5"]),
                "\n",
                "@bzd_channel ",
            )  # Конец кортежа
        )

        return blank
