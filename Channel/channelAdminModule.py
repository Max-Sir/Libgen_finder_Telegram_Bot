import config
import telegram
import telegram.ext
from classes import BotModule
import Channel.channelDB as channelDB


class ChannelModuleAdmin(BotModule):

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

        # Диалог добавления постов
        add_posts_conv = conversation(
            entry_points=[
                message(filters.regex(config.add_post_button) & filters.private & filters.user(config.admin), self.add_book_dialog)
            ],
            states={
                0: [
                    # При получении кнопки "назад" - заканчиваем диалог
                    message(filters.regex(config.back_button) & filters.private & filters.user(config.admin), end_conversation),
                    # Для сохранения документов
                    message(filters.document & filters.private & filters.user(config.admin) & filters.forwarded, self.add_document_post),
                    # Для фоток
                    message(filters.photo & filters.private & filters.user(config.admin) & filters.forwarded, self.add_document_post),
                    # Для видео
                    message(filters.video & filters.private & filters.user(config.admin) & filters.forwarded, self.add_document_post),
                    # Для текста
                    message(filters.text & filters.private & filters.user(config.admin) & filters.forwarded, self.add_text_post),
                    # Для всего остального - пропускаем и кидаем в админа первый экран
                    message(filters.all & filters.private & filters.user(config.admin), self.add_book_dialog)
                ]
            },
            fallbacks=[message(filters.regex(config.back_button), end_conversation)],
            allow_reentry=True
            )

        self.dispatcher.add_handler(add_posts_conv)

        delete_posts_conv = conversation(
            entry_points=[
                message(filters.regex(config.delete_post_button) & filters.private & filters.user(config.admin), self.delete_post_dialog)
            ],
            states={
                0: [
                    # При получении кнопки "назад" - заканчиваем диалог
                    message(filters.regex(config.back_button) & filters.private & filters.user(config.admin), end_conversation),
                    # Для удаления документов
                    message(filters.document & filters.private & filters.user(config.admin) & filters.forwarded, self.delete_by_post),
                    # Для фоток
                    message(filters.photo & filters.private & filters.user(config.admin) & filters.forwarded, self.delete_by_post),
                    # Для видео
                    message(filters.video & filters.private & filters.user(config.admin) & filters.forwarded, self.delete_by_post),
                    # Для текста
                    message(filters.text & filters.private & filters.user(config.admin) & filters.forwarded, self.delete_by_post),
                    # Для текста формата channel_id/post_id
                    message(filters.text & filters.private & filters.user(config.admin), self.delete_by_id),
                    # Для всего остального - пропускаем и кидаем в админа первый экран
                    message(filters.all & filters.private & filters.user(config.admin), self.add_book_dialog)
                ]
            },
            fallbacks = [message(filters.regex(config.back_button), end_conversation)],
            allow_reentry = True
        )

        self.dispatcher.add_handler(delete_posts_conv)

    def add_book_dialog(self, update, context):
        keyb = [[config.back_button]]
        reply_markup = self.tg.ReplyKeyboardMarkup(keyb, resize_keyboard=True, one_time_keyboard=True)
        context.bot.send_message(update.effective_chat.id, config.add_book_message, reply_markup=reply_markup)
        return 0

    def add_document_post(self, update, context):
        """
        Добавление документа в базу, требует описание к файлу
        :param update:
        :param context:
        :return:
        """
        post_id = update.message.forward_from_message_id
        channel_id = update.message.forward_from_chat.id
        text = update.message.caption
        if not text:
            context.bot.send_message(update.effective_chat.id, "Нет описания файла")
            return 0

        if len(text) == 0:
            context.bot.send_message(update.effective_chat.id, "Нет описания файла")
            return 0

        with channelDB.Update() as _db:
            data = _db.add_post(post_id, channel_id, text)

        if data.ok():
            context.bot.send_message(update.effective_chat.id, "Файл добавлен", reply_to_message_id=update.message.message_id)
            return 0
        else:
            context.bot.send_message(update.effective_chat.id, "Ошибка: {}".format(data.value()), reply_to_message_id=update.message.message_id)
            return 0

    def add_text_post(self, update, context):
        post_id = update.message.forward_from_message_id
        channel_id = update.message.forward_from_chat.id
        text = update.message.text

        if len(text) == 0:
            context.bot.send_message(update.effective_chat.id, "А где текст то?", reply_to_message_id=update.message.message_id)
            return 0

        with channelDB.Update() as _db:
            data = _db.add_post(post_id, channel_id, text)

        if data.ok():
            context.bot.send_message(update.effective_chat.id, "Текст добавлен", reply_to_message_id=update.message.message_id)
            return 0
        else:
            context.bot.send_message(update.effective_chat.id, "Ошибка: {}".format(data.value()), reply_to_message_id=update.message.message_id)
            return 0

    def delete_post_dialog(self, update, context):
        keyb = [[config.back_button]]
        reply_markup = self.tg.ReplyKeyboardMarkup(keyb, resize_keyboard=True, one_time_keyboard=True)
        context.bot.send_message(update.effective_chat.id, config.delete_post_message, reply_markup=reply_markup)
        return 0

    def delete_by_post(self, update, context):
        post_id = update.message.forward_from_message_id
        channel_id = update.message.forward_from_chat.id

        message_id = update.message.message_id
        chat_id = update.effective_chat.id

        self.do_search_and_delete_by_id(context, chat_id, message_id, channel_id, post_id)

        return 0

    def delete_by_id(self, update, context):
        chat_id = update.effective_chat.id
        message_id = update.message.message_id

        text = update.message.text
        splited_text = text.split("/")

        if not (len(splited_text) == 2):
            context.bot.send_message(chat_id, "Неправильный формат. Формат - channel_id / post_id", reply_to_message_id=message_id)
            return 0

        channel_id = splited_text[0].strip()
        post_id = splited_text[1].strip()

        # Т.к. id каналов идет с минусом, а isdigit у нас не хочет признавать число с минусом - костылим
        try:
            int(channel_id)
            int(post_id)
        except:
            context.bot.send_message(chat_id, "Неправильный формат. Некоторые символы не число. Формат - channel_id / post_id", reply_to_message_id=message_id)
            return 0

        self.do_search_and_delete_by_id(context, chat_id, message_id, channel_id, post_id)

        return 0

    def do_search_and_delete_by_id(self, context, chat_id, message_id, channel_id, post_id):
        with channelDB.Search() as _db:
            data = _db.by_channel_and_post_id(channel_id, post_id)

        if not data.ok():
            context.bot.send_message(chat_id, "Запись не найдена", reply_to_message_id=message_id)
            return 0

        for post in data.value():
            try:
                context.bot.forward_message(chat_id, post["channel_id"], post["post_id"])
            except telegram.error.BadRequest as e:
                context.bot.send_message(chat_id, "Мы нашли эту запись, но переслать не смогли, вот всё, что нам известно :)\nt.me/c/{}/{}\n\n{}".format(str(post["channel_id"]).replace("-100", ""), post["post_id"], post["text"]))

        with channelDB.Update() as _db:
            data = _db.delete_post_by_post_and_channel_id(channel_id, post_id)

        if data.ok():
            context.bot.send_message(chat_id, "Файл удален", reply_to_message_id=message_id)
        else:
            context.bot.send_message(chat_id, "Ошибка удаления файла - {}".format(data.value()), reply_to_message_id=message_id)

        return 0