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

    def openOrder(self, orderId, contract, order, orderState):
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
    parent.eTradeOnly = False
    parent.firmQuoteOnly = False
    
    takeProfit = Order()
    takeProfit.orderId = parentOrderId + 1
    takeProfit.action = "SELL"
    takeProfit.orderType = "LMT"
    takeProfit.totalQuantity = quantity
    takeProfit.lmtPrice = round(takeProfitPrice, 2)
    takeProfit.parentId = parentOrderId
    takeProfit.transmit = False
    takeProfit.eTradeOnly = False
    takeProfit.firmQuoteOnly = False
    
    stopLoss = Order()
    stopLoss.orderId = parentOrderId + 2
    stopLoss.action = "SELL"
    stopLoss.orderType = "STP"
    stopLoss.totalQuantity = quantity
    stopLoss.auxPrice = round(stopLossPrice, 2)
    stopLoss.parentId = parentOrderId
    stopLoss.transmit = True
    stopLoss.eTradeOnly = False
    stopLoss.firmQuoteOnly = False
    
    return [parent, takeProfit, stopLoss]

# Funktion zum Abrufen der historischen Aktiendaten
def get_stock_data(ticker_symbol, period="1mo"):
    """
    Ruft die historischen Daten für eine Aktie von Yahoo Finance ab.

    Args:
    ticker_symbol (str): Das Tickersymbol der Aktie.
    period (str): Der Zeitraum, für den die historischen Daten abgerufen werden sollen.

    Returns:
    tuple: Listen von Höchst-, Tiefst- und Schlusskursen.
    """
    stock = yf.Ticker(ticker_symbol)
    hist = stock.history(period=period)
    return hist['High'].tolist(), hist['Low'].tolist(), hist['Close'].tolist()

# Funktion zur Berechnung des Average True Range (ATR)
def calculate_atr(high_prices, low_prices, close_prices, period=21):
    """
    Berechnet den Average True Range (ATR) einer Aktie.

    Args:
    high_prices (list): Liste der Höchstkurse.
    low_prices (list): Liste der Tiefstkurse.
    close_prices (list): Liste der Schlusskurse.
    period (int): Die Periode, über die der ATR berechnet wird.

    Returns:
    float: Der berechnete ATR-Wert.
    """
    tr_values = [max(high, low, previous_close) - min(low, previous_close) 
                 for high, low, previous_close in zip(high_prices[1:], low_prices[1:], close_prices[:-1])]
    tr_values.insert(0, high_prices[0] - low_prices[0])  # Erster TR-Wert

    # ATR berechnen, indem der Durchschnitt der TR-Werte über die angegebene Periode genommen wird
    atr = np.mean(tr_values[-period:])
    return atr

# Funktion zur Berechnung der Position
def calculate_position(depot_size=100000, risk_per_position=10, total_risk=5, anzahl_positionen=5, ticker_symbol="AAPL"):
    """
    Berechnet die Anzahl der Aktien, den Kaufpreis und den Stop-Loss-Preis basierend auf verschiedenen Risikoparametern.

    Args:
    depot_size (int): Die Größe des Depots in USD.
    risk_per_position (int): Das Risiko pro Position in Prozent.
    total_risk (int): Das Gesamtrisiko des Portfolios in Prozent.
    anzahl_positionen (int): Die Anzahl der Positionen.
    ticker_symbol (str): Das Tickersymbol der Aktie.

    Returns:
    tuple: Anzahl der Aktien, Kaufpreis, ATR-basierter Stop-Loss-Preis, niedrigster Stop-Loss-Preis, 20%-Stop-Loss-Preis, ATR(21).
    """
    high_prices, low_prices, close_prices = get_stock_data(ticker_symbol)
    
    # Der Kaufpreis ist der letzte Schlusskurs plus 0,5%
    stock_price = high_prices[-1] * 1.005
        
    # Berechnen Sie den ATR (Average True Range) mit Periode 21
    atr_21 = calculate_atr(high_prices, low_prices, close_prices, period=21)
    
    # Berechnen Sie das maximale Risiko für das Portfolio in USD
    max_portfolio_risk = depot_size * (total_risk / 100)
    
    # Berechnen Sie das maximale Risiko für eine einzelne Position in USD
    max_position_risk = depot_size * (risk_per_position / 100)
    
    # Stellen Sie sicher, dass das Risiko einer Position nicht das Gesamtrisiko des Portfolios übersteigt
    max_position_risk = min(max_position_risk, max_portfolio_risk)
    
    # Limit für die Position auf 20% des Depotwerts
    max_depot_value_limit = depot_size * 0.20
    
    # Berechnen Sie den Stopploss-Preis basierend auf dem ATR
    stop_loss_price_atr = stock_price - (2 * atr_21)
    
    # Berechnen Sie den Stopploss-Preis basierend auf -10% vom Kaufpreis
    stop_loss_price_10 = stock_price * 0.9
    
    # Finden Sie den niedrigsten Preis der letzten 14 Tage
    stop_loss_price_14_days = min(low_prices[-14:])
    
    return stock_price, stop_loss_price_atr, stop_loss_price_14_days, stop_loss_price_10, atr_21, risk_per_position

def main(depot_size=100000, anzahl_positionen=5):
    while True:
        ticker_symbol = input("Bitte geben Sie das Tickersymbol ein: ")
        purchase_price, stop_loss_price_atr, stop_loss_price_14_days, stop_loss_price_10, atr_21, risk_per_position = calculate_position(ticker_symbol=ticker_symbol)
        
      
        print(f"Kaufpreis: ${purchase_price:.2f}")
        
        # Ausgabe der Stop-Loss-Preise und deren prozentuale Änderung zum Kaufpreis
        print(f"1. Stop-Loss-Preis (ATR-basiert): ${stop_loss_price_atr:.2f} ({((purchase_price - stop_loss_price_atr) / purchase_price) * 100:.2f}%)")
        print(f"2. Stop-Loss-Preis (niedrigster Preis der letzten 14 Tage): ${stop_loss_price_14_days:.2f} ({((purchase_price - stop_loss_price_14_days) / purchase_price) * 100:.2f}%)")
        print(f"3. Stop-Loss-Preis (-10% vom Kaufpreis): ${stop_loss_price_10:.2f} ({((purchase_price - stop_loss_price_10) / purchase_price) * 100:.2f}%)")
        
        # Abfrage, welches Stop-Loss-Wert verwendet werden soll
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
            stop_loss_price = stop_loss_price_10
        
        # Berechnung des Take-Profit-Preises basierend auf dem gewählten Stop-Loss-Preis
        take_profit_price = purchase_price + 3 * (purchase_price - stop_loss_price)
        
        # Berechnung der Anzahl der Aktien
        risk_per_share = purchase_price - stop_loss_price
        max_position_risk = 100000 * (risk_per_position / 100)
        max_purchase_value = depot_size / anzahl_positionen  # depot_size / anzahl_positionen
        number_of_shares = min(int(max_position_risk // risk_per_share), int(max_purchase_value // purchase_price))
        
        # Berechnung der prozentualen Änderung zwischen Kaufpreis und Stop-Loss-Kurs
        stop_loss_change_percentage = ((purchase_price - stop_loss_price) / purchase_price) * 100
        
        # Berechnung der prozentualen Änderung zwischen Kaufpreis und Take-Profit-Kurs
        take_profit_change_percentage = ((take_profit_price - purchase_price) / purchase_price) * 100
        
        # Erstellung der Ergebnistabelle
        results = {
            "Anzahl der Aktien": [int(number_of_shares)],
            "Kaufpreis (Stop Buy)": [f"${purchase_price:.2f}"],
            "Stop-Loss": [f"${stop_loss_price:.2f} ({stop_loss_change_percentage:.2f}%)"],
            "Take Profit": [f"${take_profit_price:.2f} ({take_profit_change_percentage:.2f}%)"]
        }
        
        df = pd.DataFrame(results)
        
        # Ausgabe der Ergebnisse in einer Tabelle
        print("\nErgebnisse:")
        display(df)
        
        # Abfrage, ob eine Kauforder angelegt werden soll
        place_order = input("Möchten Sie eine Kauforder anlegen? (1 = Ja, 2 = Nein): ")
        if place_order == '1':
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
            
            # Create the bracket order
            bracket = bracketOrder(parentOrderId, "BUY", int(number_of_shares), purchase_price, take_profit_price, stop_loss_price)
            
            # Place the bracket order
            for order in bracket:
                app.placeOrder(order.orderId, contract, order)
                time.sleep(1)  # some latency added to ensure that the order is placed
                app.nextValidOrderId += 1
            
            print("Order erfolgreich platziert.")
            
            # Disconnect the client
            app.disconnect()
        
        # Abfrage, ob eine weitere Berechnung durchgeführt werden soll
        another_calculation = input("\nMöchten Sie eine weitere Berechnung durchführen? (1 = Ja, 2 = Nein): ")
        if another_calculation == '2':
            break

if __name__ == "__main__":
    main()
