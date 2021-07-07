import config
import telegram
import telegram.ext
import Statistics.statisticsDB as StatisticsDB
from classes import BotModule

class StatisticsModule(BotModule):
    def __init__(self, updater: telegram.ext.Updater, dispatcher: telegram.ext.dispatcher):
        self.updater = updater
        self.dispatcher = dispatcher
        self.tge = telegram.ext  # Алиас для telegram.ext
        self.tg = telegram  # Алиас для telegram

    def install_handlers(self, end_conversation):
        # Алиасы
        filters = self.tge.Filters
        message = self.tge.MessageHandler

        get_all_statistics_handl = message(filters.regex(config.get_all_statistics_button), self.sendAllStatistics)

        self.dispatcher.add_handler(get_all_statistics_handl)

    def sendAllStatistics(self, update, context):
        date_section = "Дата: {} - Запр.: {}\n"
        action_section = " {action} - Запр.: {action_count} - Уник.: {user_count}\n"
        end_section = "•••\n"

        with StatisticsDB.GetStatisticsDB() as _db:
            data = _db.getAllStatistics()

        if data.ok():

            # Статистика группируется по дням {"20202020": [
            # {date: 20202020, action: "Действие 1", action_count: 1, user_count: 1},
            # {date: 20202020, action: "Действие 2", action_count: 2, user_count: 2} ...]}
            stat_group_by_days = {}
            for row in data.value():
                if stat_group_by_days.get(str(row["date"])):
                    stat_group_by_days[str(row["date"])].append(row)
                else:
                    stat_group_by_days[str(row["date"])] = [row]

            msg_stat = "Бот не хранит текст ваших запросов, только сам факт их наличия\n\n" + end_section  # Сообщение для отправки
            for day in stat_group_by_days:
                msg_stat_for_day = ""
                action_count = 0  # Подсчет общего количества действий за день
                for action in stat_group_by_days[day]:
                    action_count += action["action_count"]
                    msg_stat_for_day += action_section.format(**action)

                # Последним прикручиваем шапку статистики с датой и подсчитанным числом действий за день
                msg_stat_for_day = date_section.format(day, action_count) + msg_stat_for_day
                # Оборачиваем в code для красивого отображения в чате
                msg_stat_for_day = "<code>{}</code>".format(msg_stat_for_day)
                # Пишем до кучи в одно сообщение и докидываем туда последнюю секцию
                msg_stat += msg_stat_for_day
                msg_stat += end_section

            context.bot.send_message(update.effective_chat.id, msg_stat, parse_mode=self.tg.ParseMode.HTML)
            return
        else:
            context.bot.send_message(update.effective_chat.id, data.value())
            return
