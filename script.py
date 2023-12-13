import calendar
import datetime
import json
import math
from ib_insync import *
import asyncio
import time
import nest_asyncio
import zoneinfo


nest_asyncio.apply()
import threading

util.patchAsyncio()

commands = []

tz = zoneinfo.ZoneInfo("America/New_York")


class Strategy(threading.Thread):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.string = None
        self.list_of_args = []
        self.dict_of_args = {}
        self.market_data = None
        self.ib = IB()
        file_path = "config.json"
        with open(file_path) as json_data_file:
            self.data = json.load(json_data_file)

        self.account = self.data["account"]
        self.ib.connect("127.0.0.1", 7497, 0, account=self.account)

    def get_market_data(self, contract):
        market_data = self.ib.reqMktData(contract)
        import math

        while math.isnan(market_data.bid) or math.isnan(market_data.ask):
            self.ib.sleep(0.1)
            continue
        self.market_data = market_data
        self.ib.cancelMktData(contract)

    def update_mid(self, contract):
        market_data = self.ib.reqMktData(contract)
        import math

        while math.isnan(market_data.bid):
            self.ib.sleep(0.1)
            continue
        self.market_data = market_data
        self.ib.cancelMktData(contract)
        self.dict_of_args["price"] = round(self.market_data.midpoint(), 2)

    def update_bid(self, contract):
        market_data = self.ib.reqMktData(contract)
        import math

        while math.isnan(market_data.bid):
            self.ib.sleep(0.1)
            continue
        self.market_data = market_data
        self.ib.cancelMktData(contract)
        self.dict_of_args["price"] = self.market_data.bid

    def update_ask(self, contract):
        market_data = self.ib.reqMktData(contract)
        import math

        while math.isnan(market_data.bid):
            self.ib.sleep(0.1)
            continue
        self.market_data = market_data
        self.ib.cancelMktData(contract)
        self.dict_of_args["price"] = self.market_data.ask

    def get_list_args(self):
        self.list_of_args = self.string.split(" ")
        self.list_of_args = list(map(lambda x: x.upper(), self.list_of_args))

    def update_quantity(self, contract):
        self.get_market_data(contract)

        if self.dict_of_args["quantity"] == "ALL":
            try:
                account_details = self.ib.accountSummary(self.account)
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
        if "price" in self.dict_of_args.keys() and isinstance(self.dict_of_args["price"], str):
            try:
                if len(self.dict_of_args["price"]) == 3:
                    if self.dict_of_args["price"] == "MID":
                        self.dict_of_args["price"] = (
                            self.market_data.bid + self.market_data.ask
                        ) / 2
                    elif self.dict_of_args["price"] == "BID":
                        self.dict_of_args["price"] = self.market_data.bid
                    elif self.dict_of_args["price"] == "ASK":
                        self.dict_of_args["price"] = self.market_data.ask
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
            except Exception as e:
                pass
            self.dict_of_args["price"] = float(self.dict_of_args["price"])

    def set_dict_args_options(self):
        self.dict_of_args["action"] = self.list_of_args[0]
        self.dict_of_args["quantity"] = self.list_of_args[1]
        if ":" in self.list_of_args[2]:
            self.dict_of_args["symbol"] = self.list_of_args[2].split(":")[0]
            self.dict_of_args["exchange"] = self.list_of_args[2].split(":")[1]
        else:
            self.dict_of_args["symbol"] = self.list_of_args[2]
            self.dict_of_args["exchange"] = "SMART"
        if len(self.list_of_args[3]) == 3:
            self.dict_of_args["expiration"] = self.get_third_friday(self.list_of_args[3])
        else:
            self.dict_of_args["expiration"] = self.get_option_date(
                self.list_of_args[3][:3], self.list_of_args[3][-2:]
            )
        self.dict_of_args["right"] = self.list_of_args[4]
        self.dict_of_args["strike"] = float(self.list_of_args[5])
        self.dict_of_args["order_type"] = self.list_of_args[6]
        if self.dict_of_args["order_type"] == "LMT":
            self.dict_of_args["price"] = self.list_of_args[7]
            if "+" in self.dict_of_args["price"]:
                lst = self.dict_of_args["price"].split("+")
                self.dict_of_args["price"] = lst[0]
                self.dict_of_args["inc"] = float(lst[1])
            elif "-" in self.dict_of_args["price"]:
                lst = self.dict_of_args["price"].split("-")
                self.dict_of_args["price"] = lst[0]
                self.dict_of_args["inc"] = -float(lst[1])
            else:
                self.dict_of_args["inc"] = 0

    def set_dict_args(self):
        if "C" in self.list_of_args or "P" in self.list_of_args:
            self.set_dict_args_options()
            return
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

                        if self.list_of_args[6] != "catch" and self.list_of_args[7] != "catch-up":
                            self.dict_of_args["time"] = self.list_of_args[6]

                            self.dict_of_args["catch"] = self.list_of_args[7]
                        else:
                            self.dict_of_args["catch"] = self.list_of_args[6]
                    else:
                        self.dict_of_args["catch"] = self.list_of_args[5]

                else:
                    if len(self.list_of_args) > 5:
                        if self.list_of_args[5] != "catch" and self.list_of_args[5] != "catch-up":
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
                    if len(self.list_of_args) > 5:
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
            order.lmtPrice = round(self.dict_of_args["price"], 2)
            if order.orderType == "TWAP":
                order.algoStrategy = "Twap"
                order.orderType = "LMT"
                order.account = self.account
                order.transmit = True
                order.algoParams = []
                if self.dict_of_args["catch"] != "":
                    order.algoParams.append(TagValue(tag="catchUp", value="True"))
                else:
                    order.algoParams.append(TagValue(tag="catchUp", value="False"))

                if self.dict_of_args["time"] != "":
                    from datetime import datetime

                    order.algoParams.append(
                        TagValue(tag="startTime", value=datetime.now(tz).strftime("%H:%M:%S"))
                    )
                    order.algoParams.append(
                        TagValue(tag="endTime", value=self.dict_of_args["time"])
                    )

                else:
                    from datetime import datetime

                    order.algoParams.append(
                        TagValue(tag="startTime", value=datetime.now(tz).strftime("%H:%M:%S"))
                    )
                    order.algoParams.append(TagValue(tag="endTime", value="22:00:00"))

        try:
            self.ib.placeOrder(contract, order)
            self.ib.sleep(5)
        except Exception as e:
            print(e)

    def get_third_friday(self, month, next_year=False):
        month_dict = {
            "JAN": 1,
            "FEB": 2,
            "MAR": 3,
            "APR": 4,
            "MAY": 5,
            "JUN": 6,
            "JUL": 7,
            "AUG": 8,
            "SEP": 9,
            "OCT": 10,
            "NOV": 11,
            "DEC": 12,
        }
        year = calendar.datetime.date.today().year
        if next_year:
            year += 1

        month_num = month_dict[month.upper()]
        cal = calendar.monthcalendar(year, month_num)
        first_row = cal[0]
        if first_row[calendar.FRIDAY]:
            third_friday = cal[2][calendar.FRIDAY]
        else:
            third_friday = cal[3][calendar.FRIDAY]
        if datetime.datetime.now() > datetime.datetime(year, month_num, third_friday):
            return self.get_third_friday(month, True)
        return f"{year}{month_num:02d}{third_friday:02d}"

    def get_option_date(self, month, day):
        month_dict = {
            "JAN": 1,
            "FEB": 2,
            "MAR": 3,
            "APR": 4,
            "MAY": 5,
            "JUN": 6,
            "JUL": 7,
            "AUG": 8,
            "SEP": 9,
            "OCT": 10,
            "NOV": 11,
            "DEC": 12,
        }
        date = datetime.datetime.now().replace(month=month_dict[month], day=int(day))
        if date < datetime.datetime.now():
            date = date.replace(year=date.year + 1)
        return date.strftime("%Y%m%d")

    def make_options_order(self):
        contract = Option(
            self.dict_of_args["symbol"],
            self.dict_of_args["expiration"],
            self.dict_of_args["strike"],
            self.dict_of_args["right"],
            self.dict_of_args["exchange"],
            currency="USD",
        )
        self.ib.qualifyContracts(contract)
        all_q = False
        if self.dict_of_args["quantity"] == "ALL":
            all_q = True
        self.update_quantity(contract)
        if all_q:
            self.dict_of_args["quantity"] //= int(contract.multiplier)
        if self.dict_of_args["order_type"] == "MKT":
            self.ib.placeOrder(
                contract,
                MarketOrder(
                    self.dict_of_args["action"],
                    self.dict_of_args["quantity"],
                    account=self.account,
                    transmit=True,
                ),
            )
        elif self.dict_of_args["order_type"] == "LMT":
            if self.dict_of_args["price"] == "MID":
                self.update_mid(contract)
            if self.dict_of_args["price"] == "BID":
                self.update_bid(contract)
            if self.dict_of_args["price"] == "ASK":
                self.update_ask(contract)

            lmt_price = float(self.dict_of_args["price"]) + self.dict_of_args["inc"]
            self.ib.placeOrder(
                contract,
                LimitOrder(
                    self.dict_of_args["action"],
                    self.dict_of_args["quantity"],
                    lmt_price,
                    account=self.account,
                    transmit=True,
                ),
            )

        self.ib.sleep(1)

    def get_trade_exec(self):
        if "right" in self.dict_of_args:
            return self.make_options_order
        else:
            return self.make_order

    def get_contract(self, trade):
        trade_list = trade.upper().split(" ")
        if "C" in trade_list or "P" in trade_list:
            # options contract
            if len(trade_list[3]) == 3:
                trade_list[3] = self.get_third_friday(trade_list[3])
            else:
                trade_list[3] = self.get_option_date(trade_list[3][:3], trade_list[3][-2:])
            contract = Option(
                trade_list[2],
                trade_list[3],
                float(trade_list[5]),
                trade_list[4],
                "SMART",
                "100",
                "USD",
            )
            self.ib.qualifyContracts(contract)
            return (contract, trade_list[0], int(trade_list[1]))
        else:
            contract = Stock(trade_list[2], "SMART", "USD")
            self.ib.qualifyContracts(contract)
            return (contract, trade_list[0], int(trade_list[1]))

    def go_combo(self, command):
        trades = command.upper().split("\n")[1:-1]
        contracts = []
        for trade in trades:
            contracts.append(self.get_contract(trade))
        contract = Contract(
            symbol=contracts[0][0].symbol,
            secType="BAG",
            exchange="SMART",
            currency="USD",
            comboLegs=[
                ComboLeg(
                    conId=contract[0].conId,
                    ratio=contract[2],
                    action=contract[1],
                    exchange="SMART",
                )
                for contract in contracts
            ],
        )
        try:
            price = float(command.split("\n")[-1].split(" ")[1])
            order = LimitOrder("BUY", int(command.split("\n")[-1].split(" ")[0]), price)
            trade = self.ib.placeOrder(contract, order)
        except:
            if len(command.split("\n")[-1].split(" ")) == 3:
                price = (
                    command.upper().split("\n")[-1].split(" ")[1]
                    + command.upper().split("\n")[-1].split(" ")[2]
                )
            else:
                price = command.upper().split("\n")[-1].split(" ")[1]
            self.get_market_data(contract)
            for _ in range(50):
                self.ib.sleep(0.2)
                if not math.isnan(self.market_data.bid) and self.market_data.bid != 0:
                    break
            try:
                if len(price) == 3:
                    if price == "MID":
                        price = (self.market_data.bid + self.market_data.ask) / 2
                    elif price == "BID":
                        price = self.market_data.bid
                    elif price == "ASK":
                        price = self.market_data.ask
                if price[3] == "+":
                    lst = price.split("+")
                    if lst[0] == "MID":
                        price = (self.market_data.bid + self.market_data.ask) / 2
                    elif lst[0] == "BID":
                        price = self.market_data.bid
                    elif lst[0] == "ASK":
                        price = self.market_data.ask

                    price += float(lst[1])

                elif price[3] == "-":
                    lst = price.split("-")
                    if lst[0] == "MID":
                        price = (self.market_data.bid + self.market_data.ask) / 2
                    elif lst[0] == "BID":
                        price = self.market_data.bid
                    elif lst[0] == "ASK":
                        price = self.market_data.ask
                    price -= float(lst[1])
            except Exception as e:
                pass
            price = float(price)
            order = LimitOrder("BUY", int(command.split("\n")[-1].split(" ")[0]), price)
            trade = self.ib.placeOrder(contract, order)
            self.ib.sleep(0.01)

    def run(self, command):
        if command.split("\n")[0].upper() == "CMB":
            self.go_combo(command)
            print("#################")
            return
        self.string = command
        self.dict_of_args.clear()
        self.get_list_args()
        self.set_dict_args()
        trade = self.get_trade_exec()
        trade()
        print("#################")


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
