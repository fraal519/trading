import yfinance as yf
import numpy as np
import pandas as pd
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

    def error(self, reqId, errorCode, errorString):
        print("Error {} {} {}".format(reqId, errorCode, errorString))

    def nextValidId(self, orderId: OrderId):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)

def websocket_con(app):
    app.run()

def usTechStk(symbol, sec_type="STK", currency="USD", exchange="SMART"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract

def create_order(orderId, action, quantity, order_type, price=None, oca_group=None):
    order = Order()
    order.orderId = orderId
    order.action = action
    order.orderType = order_type
    order.totalQuantity = quantity
    order.tif = "GTC"  # Set the order validity to Good Till Cancelled
    if price is not None:
        order.lmtPrice = round(price, 2)
    if oca_group is not None:
        order.ocaType = 1  # Set OCA type (1 = cancel all other orders in the group)
        order.ocaGroup = oca_group  # Set the OCA group name
    return order

def main():
    # Eingabe des Tickersymbols
    ticker_symbol = input("Bitte geben Sie das Tickersymbol ein: ")
    
    # Eingabe des Stop-Buy-Kurses und des Limit-Kurses
    stop_buy_price = float(input("Bitte geben Sie den Stop-Buy-Kurs ein: "))
    limit_price = float(input("Bitte geben Sie den Limit-Kurs ein: "))
    
    # Berechnung der Anzahl der Aktien für eine Kauforder im Wert von 10.000 USD
    investment_amount = 10000
    number_of_shares = investment_amount // stop_buy_price
    
    # Berechnung des Stop-Loss-Preises (93% des Kaufkurses)
    stop_loss_price = stop_buy_price * 0.93
    
    # Berechnung des Take-Profit-Preises (20% über dem Kaufkurs)
    take_profit_price = stop_buy_price * 1.20
    
    print(f"Kaufpreis: ${stop_buy_price:.2f}")
    print(f"Anzahl der Aktien: {int(number_of_shares)}")
    print(f"Stop-Loss-Preis: ${stop_loss_price:.2f}")
    print(f"Take-Profit-Preis: ${take_profit_price:.2f}")

    # Verbindung zu Interactive Brokers herstellen
    app = TradingApp()
    app.connect("127.0.0.1", 4002, clientId=1)

    # Start a separate daemon thread to execute the websocket connection
    con_thread = threading.Thread(target=websocket_con, args=(app,), daemon=True)
    con_thread.start()
    time.sleep(1)  # some latency added to ensure that the connection is established

    # Wait for next valid order id
    while app.nextValidOrderId is None:
        time.sleep(0.1)

    # Create the contract
    contract = usTechStk(ticker_symbol)

    # Get the next valid order ID
    parentOrderId = app.nextValidOrderId

    # Create the Stop-Buy Order
    stop_buy_order = create_order(parentOrderId, "BUY", int(number_of_shares), "STP", stop_buy_price)
    app.placeOrder(stop_buy_order.orderId, contract, stop_buy_order)
    app.nextValidOrderId += 1

    # OCA Group Name
    oca_group = f"OCA_{parentOrderId}"

    # Create the Stop-Loss Order
    stop_loss_order = create_order(app.nextValidOrderId, "SELL", int(number_of_shares), "STP", stop_loss_price, oca_group)
    app.placeOrder(stop_loss_order.orderId, contract, stop_loss_order)
    app.nextValidOrderId += 1

    # Create the Take-Profit Order
    take_profit_order = create_order(app.nextValidOrderId, "SELL", int(number_of_shares), "LMT", take_profit_price, oca_group)
    app.placeOrder(take_profit_order.orderId, contract, take_profit_order)
    app.nextValidOrderId += 1

    print("Orders erfolgreich platziert.")
    
    # Disconnect the client
    app.disconnect()

if __name__ == "__main__":
    main()
