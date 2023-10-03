import json
import telebot
import script
from threading import Thread
import asyncio

class BaseBot():
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
                BaseBot.single_bot_instance =telebot.TeleBot(self.token)
            except Exception:
                file_path="config.json"
                with open(file_path) as json_data_file:
                    self.data = json.load(json_data_file)

                self.data["telegram_enable"]=False
                with open(file_path, 'w') as json_file:
                    json.dump(self.data, json_file, indent=4)

                    return None
    

        return BaseBot.single_bot_instance       
    
    def read_config(self):
        """
        read the config file
        """
        file_path="config.json"
        with open(file_path) as json_data_file:
            self.data = json.load(json_data_file)
            
        self.token = self.data["token"]
        self.chat_id = self.data["chat_id"]
       
        
   
        
  
class TelegramController(BaseBot):
    
    """_summary_
    this class is used to listen to the user and control the system
   
    """
    
    def __init__(self):
        
        super().__init__()  
        self.commands=[]
        
        
    def listener_start(self): 
         
        """
        listen to the user and control the system
        """
        @self.bot.message_handler(func=lambda message: True)
        def handle_start(message):
            print(message.text)  
            script.commands.append(message.text)
            asyncio.run(script.handle_input())

    def run(self):
        self.listener_start()
        self.bot.infinity_polling()

if __name__ == "__main__":

    TelegramBotcontroller = TelegramController()
    TelegramBotcontroller.run()
    
    
    
    
                           