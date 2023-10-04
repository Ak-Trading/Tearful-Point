from ib_insync import *
import asyncio
import time
import nest_asyncio
nest_asyncio.apply()
import threading
util.patchAsyncio()

commands = []

class Strategy(threading.Thread):
    def __init__(self,*args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.string = None
        self.list_of_args = []
        self.dict_of_args = {}
        self.market_data = None
        self.ib = IB()
        self.ib.connect("127.0.0.1", 7497, 0)
        

    def get_market_data(self,contract):
        
        market_data = self.ib.reqMktData(contract)
        import math
        while math.isnan(market_data.bid) or math.isnan(market_data.ask):
            self.ib.sleep(0.1)
            continue
        self.market_data = market_data
        self.ib.cancelMktData(contract)
    
    def get_list_args(self):
        self.list_of_args = self.string.split(" ")
        self.list_of_args = list(map(lambda x: x.upper(), self.list_of_args))

    def update_quantity(self, contract):
        self.get_market_data(contract)
        
        if self.dict_of_args["quantity"] == "ALL":
            try:
                account_details = self.ib.accountSummary()
                cash_balance = 1000
                for item in account_details:
                    if item.tag == "TotalCashValue":
                        cash_balance = float(item.value)
                        break
                quantity = int(cash_balance / self.market_data.close)
                self.dict_of_args["quantity"] = quantity
                
            except Exception as e:
                print(e)

        else:
            self.dict_of_args["quantity"] = int(self.dict_of_args["quantity"])

    def update_price(self, contract):
        if "price" in self.dict_of_args.keys():
            try:
                if self.dict_of_args["price"][3] == "+":
                    lst = self.dict_of_args["price"].split("+")
                    if lst[0] == "MID":
                        self.dict_of_args["price"] = (
                            self.market_data.bid + self.market_data.ask
                        ) / 2
                    elif lst[0] == "BID":
                        self.dict_of_args["price"] = self.market_data.bid
                    elif lst[0] == "ASK":
                        self.dict_of_args["price"] = self.market_data.ask

                    self.dict_of_args["price"] += float(lst[1])

                elif self.dict_of_args["price"][3] == "-":
                    
                    lst = self.dict_of_args["price"].split("-")
                    if lst[0] == "MID":
                        self.dict_of_args["price"] = (
                            self.market_data.bid + self.market_data.ask
                        ) / 2
                    elif lst[0] == "BID":
                        self.dict_of_args["price"] = self.market_data.bid
                    elif lst[0] == "ASK":
                        self.dict_of_args["price"] = self.market_data.ask
                    self.dict_of_args["price"] -= float(lst[1])
                else:
                    self.dict_of_args["price"] = float(self.dict_of_args["price"])
            except Exception as e:
                self.dict_of_args["price"] = float(self.dict_of_args["price"])
                pass

    def set_dict_args(self):
        if len(self.list_of_args) < 4:
            raise ValueError("Not enough arguments")

        self.dict_of_args["action"] = self.list_of_args[0].upper()
        self.dict_of_args["quantity"] = self.list_of_args[1].upper()
        self.dict_of_args["symbol"] = self.list_of_args[2].upper()
        self.dict_of_args["order_type"] = self.list_of_args[3].upper()
        
        if len(self.list_of_args) > 4:
            if self.dict_of_args["order_type"] == "TWAP":
                self.dict_of_args["price"] = self.list_of_args[4]

                if self.dict_of_args["price"] in ["MID", "BID", "ASK"]:
                    if self.list_of_args[5][0] == "+" or self.list_of_args[5][0] == "-":
                        self.dict_of_args["price"] += self.list_of_args[5]

                        if (
                            self.list_of_args[6] != "catch"
                            and self.list_of_args[7] != "catch-up"
                        ):
                            self.dict_of_args["time"] = self.list_of_args[6]

                            self.dict_of_args["catch"] = self.list_of_args[7]
                        else:
                            self.dict_of_args["catch"] = self.list_of_args[6]
                    else:
                        self.dict_of_args["catch"] = self.list_of_args[5]

                else:
                    if len(self.list_of_args) > 5:
                        if (
                            self.list_of_args[5] != "catch"
                            and self.list_of_args[5] != "catch-up"
                        ):
                            self.dict_of_args["time"] = self.list_of_args[5]
                            self.dict_of_args["catch"] = ""
                            if len(self.list_of_args) == 7:
                                self.dict_of_args["catch"] = self.list_of_args[6]
                        else:
                            self.dict_of_args["catch"] = self.list_of_args[5]
                            self.dict_of_args["time"] = ""

                    else:
                        self.dict_of_args["catch"] = ""
                        self.dict_of_args["time"] = ""

            elif self.dict_of_args["order_type"] == "LMT":
                self.dict_of_args["price"] = self.list_of_args[4]

                if self.dict_of_args["price"] in ["MID", "BID", "ASK"]:
                    if self.list_of_args[5][0] == "+" or self.list_of_args[5][0] == "-":
                        self.dict_of_args["price"] += self.list_of_args[5]

            else:
                self.dict_of_args["price"] = self.list_of_args[4]


    def make_order(self):
        contract = Contract()
        contract.symbol = self.dict_of_args["symbol"]
        contract.secType = "STK"
        contract.currency = "USD"

        if len(self.dict_of_args["symbol"].split(":")) > 1:
            contract.symbol = self.dict_of_args["symbol"].split(":")[1]
            contract.exchange = self.dict_of_args["symbol"].split(":")[0]
            contract.currency = "EUR"
        else:
            contract.symbol = self.dict_of_args["symbol"]
            contract.exchange = "SMART"

        self.update_quantity(contract)

        order = Order()
        order.action = self.dict_of_args["action"]
        order.orderType = self.dict_of_args["order_type"]
        order.totalQuantity = int(self.dict_of_args["quantity"])
        if order.orderType == "LMT" or order.orderType == "TWAP":
            self.update_price(contract)
            order.lmtPrice = round(self.dict_of_args["price"],2)
            if order.orderType == "TWAP":
                order.algoStrategy = "Twap"
                order.orderType = "LMT"
                order.algoParams = []
                if self.dict_of_args["catch"] != "":
                    order.algoParams.append(TagValue(tag="catchUp", value="True"))
                else:
                    order.algoParams.append(TagValue(tag="catchUp", value="False"))

                if self.dict_of_args["time"] != "":
                    from datetime import datetime

                    order.algoParams.append(
                        TagValue(
                            tag="startTime", value=datetime.now().strftime("%H:%M:%S")
                        )
                    )
                    order.algoParams.append(
                        TagValue(tag="endTime", value=self.dict_of_args["time"])
                    )

                else:
                    from datetime import datetime

                    order.algoParams.append(
                        TagValue(
                            tag="startTime", value=datetime.now().strftime("%H:%M:%S")
                        )
                    )
                    order.algoParams.append(TagValue(tag="endTime", value="22:00:00"))

    
        try:
            self.ib.placeOrder(contract, order)
            self.ib.sleep(5)
        except Exception as e:
            print(e)

    def run(self, command):
        self.string = command
        self.get_list_args()
        self.set_dict_args()
        self.make_order()


def handle_input():
    global commands
    strategy = Strategy()
    while True:
        for command in commands:
            try:
                strategy.run(commands[0])
                print(f"{command}:  done")
            except Exception as e:
                print(e)
                continue
        
        commands.clear()
        
        
        