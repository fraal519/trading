import yfinance as yf
import numpy as np
import pandas as pd
from IPython.display import display

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
def calculate_position(depot_size=20000, risk_per_position=10, total_risk=5, anzahl_positionen=5, ticker_symbol="AAPL"):
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
    
    # Der Kaufpreis ist der letzte Schlusskurs plus 0,1%
    stock_price = close_prices[-1] * 1.001
    
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
    
    # Berechnen Sie den Stopploss-Preis basierend auf -20% vom Kaufpreis
    stop_loss_price_20 = stock_price * 0.8
    
    # Finden Sie den niedrigsten Preis der letzten 14 Tage
    stop_loss_price_14_days = min(low_prices[-14:])
    
    return int(stock_price), stop_loss_price_atr, stop_loss_price_14_days, stop_loss_price_20, atr_21

def main():
    while True:
        ticker_symbol = input("Bitte geben Sie das Tickersymbol ein: ")
        purchase_price, stop_loss_price_atr, stop_loss_price_14_days, stop_loss_price_20, atr_21 = calculate_position(ticker_symbol=ticker_symbol)
        
        print(f"Kaufpreis: ${purchase_price:.2f}")
        
        # Ausgabe der Stop-Loss-Preise und deren prozentuale Änderung zum Kaufpreis
        print(f"1. Stop-Loss-Preis (ATR-basiert): ${stop_loss_price_atr:.2f} ({((purchase_price - stop_loss_price_atr) / purchase_price) * 100:.2f}%)")
        print(f"2. Stop-Loss-Preis (niedrigster Preis der letzten 14 Tage): ${stop_loss_price_14_days:.2f} ({((purchase_price - stop_loss_price_14_days) / purchase_price) * 100:.2f}%)")
        print(f"3. Stop-Loss-Preis (-20% vom Kaufpreis): ${stop_loss_price_20:.2f} ({((purchase_price - stop_loss_price_20) / purchase_price) * 100:.2f}%)")
        
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
            stop_loss_price = stop_loss_price_20
        
        # Berechnung des Take-Profit-Preises basierend auf dem gewählten Stop-Loss-Preis
        take_profit_price = purchase_price + 2 * (purchase_price - stop_loss_price)
        
        # Berechnung der Anzahl der Aktien
        risk_per_share = purchase_price - stop_loss_price
        max_position_risk = 20000 * (10 / 100)
        max_purchase_value = 20000 / 5  # depot_size / anzahl_positionen
        number_of_shares = min(max_position_risk // risk_per_share, max_purchase_value // purchase_price)
        
        # Erstellung der Ergebnistabelle
        results = {
            "Anzahl der Aktien": [int(number_of_shares)],
            "Kaufpreis (Stop Buy)": [f"${purchase_price:.2f}"],
            "Stop-Loss": [f"${stop_loss_price:.2f}"],
            "Take Profit": [f"${take_profit_price:.2f}"]
        }
        
        df = pd.DataFrame(results)
        
        # Ausgabe der Ergebnisse in einer Tabelle
        print("\nErgebnisse:")
        display(df)
        
        # Abfrage, ob eine weitere Berechnung durchgeführt werden soll
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