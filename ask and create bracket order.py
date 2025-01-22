# -*- coding: utf-8 -*-
"""
IBAPI - Bracket Order mit Stop-Buy, Stop-Loss und Take-Profit

@author: Dein Name
"""

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.common import OrderId
import threading
import time


class TradingApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.nextValidOrderId = None
        self.positions = []
        self.openOrders = []

    def error(self, reqId, errorCode, errorString):
        print("Error {} {} {}".format(reqId, errorCode, errorString))

    def nextValidId(self, orderId: OrderId):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)

    def position(self, account, contract, position, avgCost):
        self.positions.append((account, contract.symbol, position, avgCost))
        print("Position: Account: {}, Symbol: {}, Position: {}, Avg Cost: {}".format(account, contract.symbol, position, avgCost))

    def openOrder(self, orderId, contract, order, orderState):
        self.openOrders.append((orderId, contract.symbol, order.action, order.totalQuantity, order.lmtPrice))
        print("Open Order: OrderId: {}, Symbol: {}, Action: {}, Quantity: {}, Limit Price: {}".format(orderId, contract.symbol, order.action, order.totalQuantity, order.lmtPrice))

def websocket_con():
    app.run()

def usTechStk(symbol, sec_type="STK", currency="USD", exchange="SMART"):
    """
    Create a US stock contract for Interactive Brokers API.

    :param symbol: The ticker symbol of the stock.
    :param sec_type: The security type, default is "STK".
    :param currency: The currency, default is "USD".
    :param exchange: The exchange, default is "SMART".
    :return: A Contract object with the specified parameters.
    """
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract

def stopOrder(direction, quantity, stop_price):
    order = Order()
    order.action = direction
    order.orderType = "STP"
    order.totalQuantity = quantity
    order.auxPrice = stop_price
    return order

def bracketOrder(parentOrderId, action, quantity, limitPrice, takeProfitPrice, stopLossPrice):
    parent = Order()
    parent.orderId = parentOrderId
    parent.action = action
    parent.orderType = "MKT"
    parent.totalQuantity = quantity
    parent.auxPrice = limitPrice
    parent.transmit = False
    parent.eTradeOnly = False
    parent.firmQuoteOnly = False
    
    takeProfit = Order()
    takeProfit.orderId = parentOrderId + 1
    takeProfit.action = "SELL" if action == "BUY" else "BUY"
    takeProfit.orderType = "LMT"
    takeProfit.totalQuantity = quantity
    takeProfit.lmtPrice = takeProfitPrice
    takeProfit.parentId = parentOrderId
    takeProfit.transmit = False
    takeProfit.eTradeOnly = False
    takeProfit.firmQuoteOnly = False
    
    stopLoss = Order()
    stopLoss.orderId = parentOrderId + 2
    stopLoss.action = "SELL" if action == "BUY" else "BUY"
    stopLoss.orderType = "STP"
    stopLoss.totalQuantity = quantity
    stopLoss.auxPrice = stopLossPrice
    stopLoss.parentId = parentOrderId
    stopLoss.transmit = True
    stopLoss.eTradeOnly = False
    stopLoss.firmQuoteOnly = False
    
    return [parent, takeProfit, stopLoss]

app = TradingApp()
app.connect("127.0.0.1", 4002, clientId=1)

# Start a separate daemon thread to execute the websocket connection
con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()
time.sleep(1)  # some latency added to ensure that the connection is established

# Wait for next valid order id
while app.nextValidOrderId is None:
    time.sleep(0.1)

# User inputs for the bracket order
symbol = input("Geben Sie das Aktiensymbol ein: ")
quantity = int(input("Geben Sie die Menge ein: "))
stop_buy_price = float(input("Geben Sie den Kaufpreis (Stop-Buy Preis) ein: "))
take_profit_price = float(input("Geben Sie den Take-Profit Preis ein: "))
stop_loss_price = float(input("Geben Sie den Stop-Loss Preis ein: "))

# Create the contract
contract = usTechStk(symbol)

# Get the next valid order ID
parentOrderId = app.nextValidOrderId

# Create the bracket order
bracket = bracketOrder(parentOrderId, "BUY", quantity, stop_buy_price, take_profit_price, stop_loss_price)

# Place the bracket order
for order in bracket:
    app.placeOrder(order.orderId, contract, order)
    time.sleep(1)  # some latency added to ensure that the order is placed

# Requesting account positions
app.reqPositions()
time.sleep(5)  # some latency added to ensure that the positions are retrieved

# Requesting open orders
app.reqOpenOrders()
time.sleep(5)  # some latency added to ensure that the open orders are retrieved

# Disconnect the client
app.disconnect()
