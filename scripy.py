from ib_insync import *
import argparse


class IB:
    ib=IB()
    ib.connect('127.0.0.1',7497,0)

class Strategy:

    def __init__(self,string) -> None:
      
        self.string=string
        self.list_of_args = []
        self.dict_of_args = {}
        self.get_list_args()
        self.set_dict_args()
        self.make_order()

    
    def get_list_args(self):
        self.list_of_args = self.string.split(' ')

    def update_quantity(self,contract):
        if self.dict_of_args["quantity"] == "ALL":
            # sum all the quantity based on account salary
            account_details = IB.ib.accountSummary()

            # Filter the account details to find the cash balance
            cash_balance = None

            for item in account_details:
                if item.tag == 'TotalCashValue':
                    cash_balance = float(item.value)
                    break

            IB.ib.qualifyContracts(contract)
            market_data = IB.ib.reqMktData(contract)
            IB.ib.sleep(2)
            quantity = int(cash_balance / market_data.close)
            self.dict_of_args["quantity"]=quantity
        else:
            self.dict_of_args["quantity"]=int(self.dict_of_args["quantity"])



    def update_price(self,contract):
       
        if "price" in self.dict_of_args.keys():
            try:
                if self.dict_of_args["price"][3] == '+':
                    IB.ib.qualifyContracts(contract)
                    market_data = IB.ib.reqMktData(contract)
                    IB.ib.sleep(10)
                    lst=self.dict_of_args["price"].split('+')
                    if lst[0] == "MID":
                        self.dict_of_args["price"]=market_data.mid
                    elif lst[0] == "BID":
                        self.dict_of_args["price"]=market_data.bid
                    elif lst[0] == "ASK":
                        self.dict_of_args["price"]=market_data.ask

                    self.dict_of_args["price"]+=float(lst[1])
                
                elif(self.dict_of_args["price"][3] == '-'):
                    IB.ib.qualifyContracts(contract)
                    market_data = IB.ib.reqMktData(contract)
                    IB.ib.sleep(10)
                    lst=self.dict_of_args["price"].split('-')
                    if lst[0] == "MID":
                        self.dict_of_args["price"]=market_data.mid
                    elif lst[0] == "BID":
                        self.dict_of_args["price"]=market_data.bid
                    elif lst[0] == "ASK":
                        self.dict_of_args["price"]=market_data.ask
                    self.dict_of_args["price"]-=float(lst[1])
                else:
                    self.dict_of_args["price"]=float(self.dict_of_args["price"])
            except Exception as e:
                self.dict_of_args["price"]=float(self.dict_of_args["price"])
        

    def set_dict_args(self):

        if len(self.list_of_args) < 4:
            raise ValueError("Not enough arguments")
        
        
        self.dict_of_args["action"] = self.list_of_args[0]
        self.dict_of_args["quantity"] = self.list_of_args[1]
        self.dict_of_args["symbol"] = self.list_of_args[2]
        self.dict_of_args["order_type"] = self.list_of_args[3]

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

        self.dict_of_args["symbol"]=self.dict_of_args["symbol"].upper()
        self.dict_of_args["action"] = self.dict_of_args["action"].upper()
        self.dict_of_args["order_type"] =self.dict_of_args["order_type"].upper()
        self.dict_of_args["quantity"] =self.dict_of_args["quantity"].upper()

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
        print("aaaaaaaa")
        parent = LimitOrder('BUY',100, 57,outsideRth=False, algoStrategy='VWAP',
                                algoParams=[TagValue(tag='noTakeLiq', value='1'),
                                            TagValue(tag='allowPastEndTime', value='0'), 
                                            TagValue(tag='speedUp', value='0'),
                                            TagValue(tag='startTime', value='20231001-18:12:51'),
                                            TagValue(tag='endTime', value='20231002-20:12:54')])
        x=IB.ib.placeOrder(contract,parent)
        print(x)
        if order.orderType == "LMT" or order.orderType == "TWAP":
            order.lmtPrice = self.dict_of_args["price"]
        
        if order.orderType == "TWAP":
            order.orderType = "LMT"
            order.lmtPrice = self.dict_of_args["price"]

           


        try:
            pass
            IB.ib.placeOrder(contract,order)
        except Exception as e:
            pass
def handle_input(command):
    strategy=Strategy(command)
    
           
if __name__ == "__main__":

    while True :
        
        command = input("Enter The Statement:")
        handle_input(command)

    