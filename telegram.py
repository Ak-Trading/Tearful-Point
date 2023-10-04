import json
import threading
import asyncio
import tracemalloc
import telebot
from script import commands,handle_input
# tracemalloc.start()
# asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

class BaseBot:
    """
    super class for telegram bot

    attributes:
        symbols: a list of symbols to be monitored
        bot: a telebot object
    """

    single_bot_instance = None

    def __init__(self):
        """
        initialize the class, read the config file and connect to the bot
        """
        self.read_config()
        self.bot

    @property
    def bot(self):
        """
        apply the singleton pattern to the bot object
        """
        if BaseBot.single_bot_instance is None:
            try:
                BaseBot.single_bot_instance = telebot.TeleBot(self.token)
            except Exception:
                print("telegram bot is not enabled")

        return BaseBot.single_bot_instance

    def read_config(self):
        """
        read the config file
        """
        file_path = "config.json"
        with open(file_path) as json_data_file:
            self.data = json.load(json_data_file)

        self.token = self.data["token"]
        self.chat_id = self.data["chat_id"]


class TelegramController(BaseBot):
    """
    this class is used to listen to the user and control the system
    """

    def __init__(self):
        super().__init__()
        
    def listener_start(self):
        """
        listen to the user and control the system
        """
        @self.bot.message_handler(func=lambda message: True)
        def handle_start(message):
            global commands
            commands.append(message.text) 
        
                   
    def run(self):
        self.listener_start()
        self.bot.infinity_polling()


if __name__ == "__main__":
    TelegramBotcontroller = TelegramController()
    thread_1 = threading.Thread(target=handle_input,daemon=True)
    thread_2 = threading.Thread(target=TelegramBotcontroller.run,daemon=True)
    thread_2.start()
    thread_1.start()
    thread_1.join()
    thread_2.join()
 
