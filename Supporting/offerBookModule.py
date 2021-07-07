import config
import telegram
import telegram.ext
from classes import BotModule


class OfferBookModule(BotModule):

    def __init__(self, updater: telegram.ext.Updater, dispatcher: telegram.ext.dispatcher):
        self.updater = updater
        self.dispatcher = dispatcher
        self.tge = telegram.ext  # Алиас для telegram.ext
        self.tg = telegram  # Алиас для telegram

    def install_handlers(self, end_conversation):
        filters = self.tge.Filters
        conversation = self.tge.ConversationHandler
        message = self.tge.MessageHandler
        command = self.tge.CommandHandler

        offer_book_conv = conversation(
            entry_points=[
                            command(config.offer_book_command, self.send_start_keyb, filters=filters.private),
                            message(filters.regex(config.prefix_offer_book) & filters.private, self.send_start_keyb),
                            message(filters.regex(config.offer_book_button) & filters.private, self.send_start_keyb)
                         ],
            states={
                0: [message(filters.regex(config.back_button) & filters.private, end_conversation),  # Кнопка назад
                    message(filters.document & filters.private, self.check_and_forward),
                    message(filters.text & filters.private, self.send_start_keyb)]  # Поиск
            },
            fallbacks=[message(filters.regex(config.back_button) & filters.private, end_conversation)], allow_reentry=True)

        self.dispatcher.add_handler(offer_book_conv)

    def send_start_keyb(self, update, context):
        """
        Отправляет кнопки предложки
        :param update:
        :param context:
        :return:
        """
        keyb = [[config.back_button]]
        reply_markup = self.tg.ReplyKeyboardMarkup(keyb, resize_keyboard=True, one_time_keyboard=True)
        update.message.reply_text(config.start_in_offer_book_msg, reply_markup=reply_markup, parse_mode=self.tg.ParseMode.HTML)
        return 0

    def check_and_forward(self, update, context):
        if update.message == None:
            update.message.reply_text("Нужен файл")
            return 0

        if update.message.document == None:
            update.message.reply_text("Нужен файл")
            return 0

        document = update.message.document
        if document.mime_type == None:
            update.message.reply_text("У файла нет mime type")
            return 0

        if document.mime_type not in config.offer_book_mime_type:
            update.message.reply_text("У файла не подходящий mime type, если тут какая-то ошибка - напиши админу :)")
            return 0

        file_extension = ""
        position_ext = document.file_name.rfind(".")
        if position_ext != -1:
            file_extension = document.file_name[position_ext:]
        else:
            update.message.reply_text("У файла нет расширения")
            return 0

        if file_extension not in config.offer_book_extension:
            update.message.reply_text("Файл с таким расширением не подходит")
            return 0

        context.bot.send_document(config.offer_book_channel_chat_id, document.file_id, disable_notification=True)
        update.message.reply_text("Большое тебе спасибо :)")
        return 0
