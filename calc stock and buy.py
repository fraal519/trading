import yfinance as yf
import numpy as np
import pandas as pd
from IPython.display import display
from ibapi.client import *
from ibapi.wrapper import *
from ibapi.contract import Contract
from ibapi.order import Order
import threading
import time

class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.next_order_id = None

    def nextValidId(self, orderId: int):
        self.next_order_id = orderId
        print(f"Next valid order ID: {orderId}")

    def openOrder(self, orderId: OrderId, contract: Contract, order: Order, orderState: OrderState):
        print(f"openOrder: {orderId}, contract: {contract}, order: {order}, Maintenance Margin: {orderState.maintMarginChange}")

    def orderStatus(self, orderId: OrderId, status: str, filled: float, remaining: float, avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):
        print(f"orderStatus. orderId: {orderId}, status:  {status}, filled: {filled}, remaining: {remaining}, avgFillPrice: {avgFillPrice}, permId: {permId}, parentId: {parentId}, lastFillPrice: {lastFillPrice}, clientId: {clientId}, whyHeld: {whyHeld}, mktCapPrice: {mktCapPrice}")

    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        print(f"execDetails. reqId: {reqId}, contract: {contract}, execution: {execution}")

    def create_bracket_order(self, symbol, quantity, limit_price, take_profit_price, stop_loss_price):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        parent = Order()
        parent.orderId = self.next_order_id
        parent.orderType = "LMT"
        parent.lmtPrice = limit_price
        parent.action = "BUY"
        parent.totalQuantity = quantity
        parent.transmit = False

        take_profit = Order()
        take_profit.orderId = parent.orderId + 1
        take_profit.parentId = parent.orderId
        take_profit.action = "SELL"
        take_profit.orderType = "LMT"
        take_profit.lmtPrice = take_profit_price
        take_profit.totalQuantity = quantity
        take_profit.transmit = False

        stop_loss = Order()
        stop_loss.orderId = parent.orderId + 2
        stop_loss.parentId = parent.orderId
        stop_loss.orderType = "STP"
        stop_loss.auxPrice = stop_loss_price
        stop_loss.action = "SELL"
        stop_loss.totalQuantity = quantity
        stop_loss.transmit = True

        self.placeOrder(parent.orderId, contract, parent)
        self.placeOrder(take_profit.orderId, contract, take_profit)
        self.placeOrder(stop_loss.orderId, contract, stop_loss)

def run_loop():
    app.run()

# Funktion zum Abrufen der historischen Aktiendaten
def get_stock_data(ticker_symbol, period="1mo"):
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period=period)
    return hist['High'].tolist(), hist['Low'].tolist(), hist['Close'].tolist()

# Funktion zur Berechnung des Average True Range (ATR)
def calculate_atr(high_prices, low_prices, close_prices, period=21):
    tr_values = [max(high, low, previous_close) - min(low, previous_close) 
                 for high, low, previous_close in zip(high_prices[1:], low_prices[1:], close_prices[:-1])]
    tr_values.insert(0, high_prices[0] - low_prices[0])  # Erster TR-Wert
    atr = np.mean(tr_values[-period:])
    return atr

# Funktion zur Berechnung der Position
def calculate_position(depot_size=20000, risk_per_position=10, total_risk=5, anzahl_positionen=5, ticker_symbol="AAPL"):
    high_prices, low_prices, close_prices = get_stock_data(ticker_symbol)
    stock_price = high_prices[-1] * 1.001
    atr_21 = calculate_atr(high_prices, low_prices, close_prices, period=21)
    max_portfolio_risk = depot_size * (total_risk / 100)
    max_position_risk = depot_size * (risk_per_position / 100)
    max_position_risk = min(max_position_risk, max_portfolio_risk)
    max_depot_value_limit = depot_size * 0.20
    stop_loss_price_atr = stock_price - (2 * atr_21)
    stop_loss_price_20 = stock_price * 0.8
    stop_loss_price_14_days = min(low_prices[-14:])
    return stock_price, stop_loss_price_atr, stop_loss_price_14_days, stop_loss_price_20, atr_21

def main():
    global app
    app = TestApp()
    app.connect("127.0.0.1", 4002, 1)
    
    api_thread = threading.Thread(target=run_loop, daemon=True)
    api_thread.start()

    while True:
        ticker_symbol = input("Bitte geben Sie das Tickersymbol ein: ")
        purchase_price, stop_loss_price_atr, stop_loss_price_14_days, stop_loss_price_20, atr_21 = calculate_position(ticker_symbol=ticker_symbol)
        
        print(f"Kaufpreis: ${purchase_price:.2f}")
        
        print(f"1. Stop-Loss-Preis (ATR-basiert): ${stop_loss_price_atr:.2f} ({((purchase_price - stop_loss_price_atr) / purchase_price) * 100:.2f}%)")
        print(f"2. Stop-Loss-Preis (niedrigster Preis der letzten 14 Tage): ${stop_loss_price_14_days:.2f} ({((purchase_price - stop_loss_price_14_days) / purchase_price) * 100:.2f}%)")
        print(f"3. Stop-Loss-Preis (-20% vom Kaufpreis): ${stop_loss_price_20:.2f} ({((purchase_price - stop_loss_price_20) / purchase_price) * 100:.2f}%)")
        
        while True:
            stop_loss_choice = input("Welchen Stop-Loss-Preis möchten Sie verwenden? (1/2/3): ")
            if stop_loss_choice in ['1', '2', '3']:
                break
            else:
                print("Ungültige Auswahl. Bitte geben Sie 1, 2 oder 3 ein.")
                
        if stop_loss_choice == '1':
            stop_loss_price = stop_loss_price_atr
        elif stop_loss_choice == '2':
            stop_loss_price = stop_loss_price_14_days
        elif stop_loss_choice == '3':
            stop_loss_price = stop_loss_price_20
        
        take_profit_price = purchase_price + 3 * (purchase_price - stop_loss_price)
        risk_per_share = purchase_price - stop_loss_price
        max_position_risk = 20000 * (10 / 100)
        max_purchase_value = 20000 / 5
        number_of_shares = min(max_position_risk // risk_per_share, max_purchase_value // purchase_price)
        
        stop_loss_change_percentage = ((purchase_price - stop_loss_price) / purchase_price) * 100
        take_profit_change_percentage = ((take_profit_price - purchase_price) / purchase_price) * 100
        
        results = {
            "Anzahl der Aktien": [int(number_of_shares)],
            "Kaufpreis (Stop Buy)": [f"${purchase_price:.2f}"],
            "Stop-Loss": [f"${stop_loss_price:.2f} ({stop_loss_change_percentage:.2f}%)"],
            "Take Profit": [f"${take_profit_price:.2f} ({take_profit_change_percentage:.2f}%)"]
        }
        
        df = pd.DataFrame(results)
        print("\nErgebnisse:")
        display(df)
        
        while True:
            create_order = input("\nMöchten Sie eine Bracket Order bei Interactive Brokers anlegen? (1 = Ja, 2 = Nein): ")
            if create_order in ['1', '2']:
                break
            else:
                print("Ungültige Auswahl. Bitte geben Sie 1 oder 2 ein.")
        
        if create_order == '1':
            while app.next_order_id is None:
                time.sleep(0.1)
            app.create_bracket_order(ticker_symbol, int(number_of_shares), purchase_price, take_profit_price, stop_loss_price)
        
        while True:
            another_calculation = input("\nMöchten Sie eine weitere Berechnung durchführen? (1 = Ja, 2 = Nein): ")
            if another_calculation in ['1', '2']:
                break
            else:
                print("Ungültige Auswahl. Bitte geben Sie 1 oder 2 ein.")
        
        if another_calculation == '2':
            break

if __name__ == "__main__":
    main()
