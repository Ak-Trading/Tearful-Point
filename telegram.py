import asyncio
import json
import telebot

symbols = {}

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
        self.enable_telegram = self.data["telegram_enable"]
        
   
        
  
class TelegramController(BaseBot):
    
    """_summary_
    this class is used to listen to the user and control the system
   
    """
    
    def __init__(self):
        
        super().__init__()  
        
    def listener_start(self): 
         
        """
        listen to the user and control the system
        """
        @self.bot.message_handler(lambda message: True)
        def handle_start(message):
            
            print(message)  
            
   

    def run(self):
        try:
            self.listener_start()
            self.bot.polling()
        except:
            return None
        
if __name__ == "__main__":
    TelegramController().run()
                           