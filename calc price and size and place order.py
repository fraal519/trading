import yfinance as yf
import numpy as np
import pandas as pd
from IPython.display import display
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

    def openOrder(self, orderId, contract, order):
        self.openOrders.append((orderId, contract.symbol, order.action, order.totalQuantity, order.lmtPrice))
        print("Open Order: OrderId: {}, Symbol: {}, Action: {}, Quantity: {}, Limit Price: {}".format(orderId, contract.symbol, order.action, order.totalQuantity, order.lmtPrice))

def websocket_con(app):
    app.run()

def usTechStk(symbol, sec_type="STK", currency="USD", exchange="SMART"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract

def bracketOrder(parentOrderId, action, quantity, limitPrice, takeProfitPrice, stopLossPrice):
    parent = Order()
    parent.orderId = parentOrderId
    parent.action = action
    parent.orderType = "STP"
    parent.totalQuantity = quantity
    parent.auxPrice = round(limitPrice, 2)
    parent.transmit = False
    
    takeProfit = Order()
    takeProfit.orderId = parentOrderId + 1
    takeProfit.action = "SELL"
    takeProfit.orderType = "LMT"
    takeProfit.totalQuantity = quantity
    takeProfit.lmtPrice = round(takeProfitPrice, 2)
    takeProfit.parentId = parentOrderId
    takeProfit.transmit = False
    
    stopLoss = Order()
    stopLoss.orderId = parentOrderId + 2
    stopLoss.action = "SELL"
    stopLoss.orderType = "STP"
    stopLoss.totalQuantity = quantity
    stopLoss.auxPrice = round(stopLossPrice, 2)
    stopLoss.parentId = parentOrderId
    stopLoss.transmit = True
    
    return [parent, takeProfit, stopLoss]

def get_stock_data(ticker_symbol, period="1mo"):
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period=period)
    return hist['High'].tolist(), hist['Low'].tolist(), hist['Close'].tolist()

def calculate_atr(high_prices, low_prices, close_prices, period=21):
    """
    Calculate the Average True Range (ATR) for a given period.

    Parameters:
    high_prices (list): List of high prices.
    low_prices (list): List of low prices.
    close_prices (list): List of close prices.
    period (int): The period over which to calculate the ATR.

    Returns:
    float: The calculated ATR value.
    """
    tr_values = [max(high, low, previous_close) - min(low, previous_close) 
                             for high, low, previous_close in zip(high_prices[1:], low_prices[1:], close_prices[:-1])]
    tr_values = [max(high, previous_close) - min(low, previous_close) 
                             for high, low, previous_close in zip(high_prices[1:], low_prices[1:], close_prices[:-1])]
    tr_values.insert(0, high_prices[0] - low_prices[0])
    atr = np.mean(tr_values[-period:])
    return atr

def calculate_sma(prices, period=20):
    """Berechnet den einfachen gleitenden Durchschnitt (SMA) über eine gegebene Periode."""
    if len(prices) < period:
        raise ValueError("Nicht genug Daten, um den SMA zu berechnen.")
    return np.mean(prices[-period:])

def calculate_position(depot_size, risk_per_position, total_risk, p, ticker_symbol="AAPL"):
    high_prices, low_prices, close_prices = get_stock_data(ticker_symbol)
    stock_price = high_prices[-1] * 1.001  # Kaufpreis leicht oberhalb des aktuellen Höchstkurses
    atr_21 = calculate_atr(high_prices, low_prices, close_prices, period=21)
    max_portfolio_risk = depot_size * (total_risk / 100)
    max_position_risk = depot_size * (risk_per_position / 100)
    max_position_risk = min(max_position_risk, max_portfolio_risk)
    
    stop_loss_price_atr = stock_price - (2 * atr_21)
    stop_loss_price_sma_20 = calculate_sma(close_prices, period=20)  # Stop-Loss basierend auf SMA(20)
    stop_loss_price_14_days = min(low_prices[-14:])  # Niedrigster Preis der letzten 14 Tage
    kelly_factor = p - q
    q = 1 - p
    kelly_factor = p - (q / (p / q))
    return stock_price, stop_loss_price_atr, stop_loss_price_14_days, stop_loss_price_sma_20, kelly_factor

def main():
    depot_size = float(input("Bitte geben Sie die Depotgröße ein: "))
    risk_per_position = float(input("Bitte geben Sie das Risiko pro Position in Prozent ein: "))
    total_risk = float(input("Bitte geben Sie das Gesamtrisiko des Portfolios in Prozent ein: "))
    anzahl_positionen = int(input("Bitte geben Sie die Anzahl der Positionen ein: "))
    p = float(input("Bitte geben Sie die Gewinnwahrscheinlichkeit p ein: "))
    
    while True:
        ticker_symbol = input("Bitte geben Sie das Tickersymbol ein: ")
        purchase_price, stop_loss_price_atr, stop_loss_price_14_days, stop_loss_price_sma_20, kelly_factor = calculate_position(depot_size, risk_per_position, total_risk, p, ticker_symbol=ticker_symbol)
        
        print(f"Kaufpreis: ${purchase_price:.2f}")
        print(f"1. Stop-Loss-Preis (ATR-basiert): ${stop_loss_price_atr:.2f} ({((purchase_price - stop_loss_price_atr) / purchase_price) * 100:.2f}%)")
        print(f"2. Stop-Loss-Preis (niedrigster Preis der letzten 14 Tage): ${stop_loss_price_14_days:.2f} ({((purchase_price - stop_loss_price_14_days) / purchase_price) * 100:.2f}%)")
        print(f"3. Stop-Loss-Preis (SMA 20): ${stop_loss_price_sma_20:.2f} ({((purchase_price - stop_loss_price_sma_20) / purchase_price) * 100:.2f}%)")
        
        while True:
            stop_loss_choice = input("Welchen Stop-Loss-Preis möchten Sie verwenden? (1/2/3): ")
            if stop_loss_choice in ['1', '2', '3']:
                break
        
        if stop_loss_choice == '1':
            stop_loss_price = stop_loss_price_atr
        elif stop_loss_choice == '2':
            stop_loss_price = stop_loss_price_14_days
        elif stop_loss_choice == '3':
            stop_loss_price = stop_loss_price_sma_20
        
        take_profit_price = purchase_price + 3 * (purchase_price - stop_loss_price)
        risk_per_share = purchase_price - stop_loss_price
        max_position_risk = depot_size * (risk_per_position / 100)
        max_purchase_value = depot_size / anzahl_positionen
        number_of_shares = min(max_position_risk // risk_per_share, max_purchase_value // purchase_price)
        number_of_shares = int(number_of_shares * kelly_factor)
        
        print(f"Anzahl der Aktien: {number_of_shares}")
        
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
        
        another_calculation = input("\nMöchten Sie eine weitere Berechnung durchführen? (1 = Ja, 2 = Nein): ")
        if another_calculation == '2':
            break

if __name__ == "__main__":
    main()