from ib_insync import *
import asyncio
import time
commands=[]

ib=IB()
ib.connect('127.0.0.1',7497,0)    

class Strategy():

    def __init__(self) -> None:
      
        self.string=None
        
        self.list_of_args = []
        self.dict_of_args = {}
    
    def get_list_args(self):
        self.list_of_args = self.string.split(' ')

    def update_quantity(self,contract):
        if self.dict_of_args["quantity"] == "ALL":
            account_details = IB.ib.accountSummary()
            cash_balance = None

            for item in account_details:
                if item.tag == 'TotalCashValue':
                    cash_balance = float(item.value)
                    break

            ib.qualifyContracts(contract)
            market_data = ib.reqMktData(contract)
            start_time = time.time()
            while market_data == None:
                continue
            end_time = time.time()
            print(f"Time taken: {end_time - start_time}")

            quantity = int(cash_balance / market_data.close)
            self.dict_of_args["quantity"]=quantity
        else:
            self.dict_of_args["quantity"]=int(self.dict_of_args["quantity"])



    def update_price(self,contract):
        if "price" in self.dict_of_args.keys():
            try:
                print(self.dict_of_args["price"])
                if self.dict_of_args["price"][3] == '+':
                    ib.qualifyContracts(contract)
                    market_data = ib.reqMktData(contract)
                    import math
                    while math.isnan(market_data.bid) or math.isnan(market_data.ask):
                        ib.sleep(0.1)
                        continue
                    lst=self.dict_of_args["price"].split('+')
                    if lst[0] == "MID":
                        self.dict_of_args["price"]=(market_data.bid+market_data.ask)/2
                    elif lst[0] == "BID":
                        self.dict_of_args["price"]=market_data.bid
                    elif lst[0] == "ASK":
                        self.dict_of_args["price"]=market_data.ask

                    self.dict_of_args["price"]+=float(lst[1])
                
                elif(self.dict_of_args["price"][3] == '-'):
                    ib.qualifyContracts(contract)
                    market_data = ib.reqMktData(contract)
                    import math

                    while math.isnan(market_data.bid) or math.isnan(market_data.ask):
                        ib.sleep(0.1)
                        continue
                    lst=self.dict_of_args["price"].split('-')
                    if lst[0] == "MID":
                        self.dict_of_args["price"]=(market_data.bid+market_data.ask)/2
                    elif lst[0] == "BID":
                        self.dict_of_args["price"]=market_data.bid
                    elif lst[0] == "ASK":
                        self.dict_of_args["price"]=market_data.ask
                    self.dict_of_args["price"]-=float(lst[1])
                else:
                    self.dict_of_args["price"]=float(self.dict_of_args["price"])
            except Exception as e:
                self.dict_of_args["price"]=float(self.dict_of_args["price"])

            print(self.dict_of_args)
        

    def set_dict_args(self):

        if len(self.list_of_args) < 4:
            raise ValueError("Not enough arguments")
        
        
        self.dict_of_args["action"] = self.list_of_args[0]
        self.dict_of_args["quantity"] = self.list_of_args[1]
        self.dict_of_args["symbol"] = self.list_of_args[2]
        self.dict_of_args["order_type"] = self.list_of_args[3]

        self.dict_of_args["symbol"]=self.dict_of_args["symbol"].upper()
        self.dict_of_args["action"] = self.dict_of_args["action"].upper()
        self.dict_of_args["order_type"] =self.dict_of_args["order_type"].upper()
        self.dict_of_args["quantity"] =self.dict_of_args["quantity"].upper()

        if len(self.list_of_args) > 4:

            if self.dict_of_args["order_type"] == "TWAP":
                self.dict_of_args["price"]=self.list_of_args[4]

                if self.dict_of_args["price"] in ["MID","BID","ASK"]:
                    if self.list_of_args[5][0] == "+" or self.list_of_args[5][0] == "-":
                        self.dict_of_args["price"]+=self.list_of_args[5]

                        if self.list_of_args[6] != "catch" and self.list_of_args[7] != "catch-up":
                            self.dict_of_args["time"]=self.list_of_args[6]

                            self.dict_of_args["catch"]=self.list_of_args[7]
                        else:
                            self.dict_of_args["catch"]=self.list_of_args[6]
                    else:
                        self.dict_of_args["catch"]=self.list_of_args[5]

                else:
                    if self.list_of_args[5] != "catch" and self.list_of_args[5] != "catch-up":
                            self.dict_of_args["time"]=self.list_of_args[5]

                            self.dict_of_args["catch"]=self.list_of_args[6]
                    else:
                        self.dict_of_args["catch"]=self.list_of_args[5]
                        


              
            elif self.dict_of_args["order_type"] =="LMT":
                self.dict_of_args["price"]=self.list_of_args[4]
                
                if self.dict_of_args["price"] in ["MID","BID","ASK"]:
                    if self.list_of_args[5][0] == "+" or self.list_of_args[5][0] == "-":
                        self.dict_of_args["price"]+=self.list_of_args[5]
                        

            else:
                self.dict_of_args["price"]=self.list_of_args[4]

        

        print(self.dict_of_args)

            

    def make_order(self):
        contract = Contract()
        contract.symbol = self.dict_of_args["symbol"]
        contract.secType = "STK"
        contract.currency = "USD"
        if len(self.dict_of_args["symbol"].split(':')) > 1:
            contract.symbol = self.dict_of_args["symbol"].split(':')[1]
            contract.exchange = self.dict_of_args["symbol"].split(':')[0]
            contract.currency = "EUR"
        else:
            contract.symbol = self.dict_of_args["symbol"]
            contract.exchange = "SMART"
        
        self.update_price(contract)
        self.update_quantity(contract)

        order=Order()
        order.action = self.dict_of_args["action"]
        order.orderType = self.dict_of_args["order_type"]
        order.totalQuantity = int(self.dict_of_args["quantity"])
        if order.orderType == "LMT" or order.orderType == "TWAP":
            order.lmtPrice = self.dict_of_args["price"]

            import datetime

            # Get the current date and time
            current_datetime = datetime.datetime.now()

            # Format the date and time as 'YYYYMMDD-HH:mm:ss'
            formatted_datetime = current_datetime.strftime('%Y%m%d-%H:%M:%S')
            print(formatted_datetime)

            # Format the combined date and time
            new_formatted_datetime = formatted_datetime.split('-')[0] + '-' + self.dict_of_args['time']
            print(new_formatted_datetime)
            if order.orderType == "TWAP":
                order.algoStrategy='Twap'
                order.orderType='LMT'
                if self.dict_of_args["catch"] != '':
                    flag="True"
                else:
                    flag="False"
                order.algoParams=[  TagValue(tag='endTime',value=self.dict_of_args['time']),
                                    TagValue(tag='catchUp',value=flag)]
                
        print(order)
        try:
            x=ib.placeOrder(contract,order)
            print(x)
        except Exception as e:
            print(e)
        

    def run(self,command):
        self.string=command
        self.get_list_args()
        self.set_dict_args()
        self.make_order()

async def handle_input():
    strategy=Strategy()
    if len(commands) > 0:
        for i in range(len(commands)):
            strategy.run(commands[i])
            commands.pop(0)
    

async def some_async_function():
    await handle_input()

        
    
if __name__ == "__main__":

    while True:
        command=input("Enter command: ")
        commands.append(command)
        asyncio.run(some_async_function())
        print("Done")
