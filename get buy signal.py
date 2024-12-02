import pandas as pd
import numpy as np
import yfinance as yf
from IPython.display import display

def read_stock_symbols(filename):
    """
    Liest die CSV-Datei mit Aktiensymbolen ein.

    Args:
        filename (str): Der Dateiname der CSV-Datei.

    Returns:
        list: Eine Liste von Aktiensymbolen.
    """
    df = pd.read_csv(filename)
    return df['Symbol'].tolist()

def get_stock_data(symbol):
    """
    Holt die historischen Daten für ein gegebenes Aktiensymbol.

    Args:
        symbol (str): Das Aktiensymbol.

    Returns:
        DataFrame: Ein DataFrame mit historischen Daten.
    """
    stock = yf.Ticker(symbol)
    return stock.history(period="1y")

def calculate_sma(data, window):
    """
    Berechnet den einfachen gleitenden Durchschnitt (SMA).

    Args:
        data (DataFrame): Ein DataFrame mit historischen Daten.
        window (int): Die Fenstergröße für den gleitenden Durchschnitt.

    Returns:
        Series: Eine Serie mit den SMA-Werten.
    """
    return data['Close'].rolling(window=window).mean()

def calculate_ichimoku(data):
    """
    Berechnet die Ichimoku-Komponenten.

    Args:
        data (DataFrame): Ein DataFrame mit historischen Daten.

    Returns:
        None: Die Funktion fügt die Ichimoku-Komponenten direkt zum DataFrame hinzu.
    """
    high_9 = data['High'].rolling(window=9).max()
    low_9 = data['Low'].rolling(window=9).min()
    tenkan_sen = (high_9 + low_9) / 2

    high_26 = data['High'].rolling(window=26).max()
    low_26 = data['Low'].rolling(window=26).min()
    kijun_sen = (high_26 + low_26) / 2

    data['Tenkan_Sen'] = tenkan_sen
    data['Kijun_Sen'] = kijun_sen

    span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)
    high_52 = data['High'].rolling(window=52).max()
    low_52 = data['Low'].rolling(window=52).min()
    span_b = ((high_52 + low_52) / 2).shift(26)

    data['Span_A'] = span_a
    data['Span_B'] = span_b

def check_cup_with_handle(data):
    """
    Überprüft, ob eine "Cup with Handle"-Formation vorliegt.

    Args:
        data (DataFrame): Ein DataFrame mit historischen Daten.

    Returns:
        bool: True, wenn eine "Cup with Handle"-Formation vorliegt, sonst False.
    """
    # Eine vereinfachte Implementierung zur Erkennung der "Cup with Handle"-Formation
    cup_found = False
    handle_found = False

    # Parameter für die Cup-Formation
    cup_depth_threshold = 0.15  # 15% Rückgang vom Höchststand
    handle_depth_threshold = 0.05  # 5% Rückgang vom Höchststand
    cup_length = 30  # Anzahl der Tage für die Cup-Formation
    handle_length = 10  # Anzahl der Tage für die Handle-Formation

    # Überprüfung der Cup-Formation
    for i in range(len(data) - cup_length - handle_length):
        cup = data['Close'].iloc[i:i + cup_length]
        max_price = cup.max()
        min_price = cup.min()
        if (max_price - min_price) / max_price > cup_depth_threshold:
            cup_found = True

            # Überprüfung der Handle-Formation
            handle = data['Close'].iloc[i + cup_length:i + cup_length + handle_length]
            handle_max_price = handle.max()
            handle_min_price = handle.min()
            if (handle_max_price - handle_min_price) / handle_max_price < handle_depth_threshold:
                handle_found = True
                break

    return cup_found and handle_found

def check_buy_signals(data):
    """
    Überprüft die Kaufsignale.

    Args:
        data (DataFrame): Ein DataFrame mit historischen Daten.

    Returns:
        list: Eine Liste von Kaufsignalen.
    """
    signals = []

    # SMA 15 kreuzt SMA 50 von unten nach oben
    sma_15 = calculate_sma(data, 15)
    sma_50 = calculate_sma(data, 50)
    if (sma_15.iloc[-4] < sma_50.iloc[-4]) and (sma_15.iloc[-3] > sma_50.iloc[-3]):
        signals.append("SMA 15 kreuzt SMA 50 von unten nach oben")

    # Handelsvolumen ist 20% höher als der 50 Tage Durchschnitt (letzten beiden Handelstage)
    avg_volume_50 = data['Volume'].rolling(window=50).mean()
    if data['Volume'].iloc[-2] > 1.2 * avg_volume_50.iloc[-2] or data['Volume'].iloc[-3] > 1.2 * avg_volume_50.iloc[-3]:
        signals.append("Handelsvolumen ist 20% höher als der 50 Tage Durchschnitt (letzten beiden Handelstage)")

    # Ichimoku Bedingung
    calculate_ichimoku(data)
    if (data['Tenkan_Sen'].iloc[-4] < data['Kijun_Sen'].iloc[-4]) and (data['Tenkan_Sen'].iloc[-3] > data['Kijun_Sen'].iloc[-3]):
        if data['Tenkan_Sen'].iloc[-3] > max(data['Span_A'].iloc[-3], data['Span_B'].iloc[-3]) and data['Kijun_Sen'].iloc[-3] > max(data['Span_A'].iloc[-3], data['Span_B'].iloc[-3]):
            signals.append("Starkes Ichimoku Kaufsignal: Kreuzung oberhalb der Wolke")

    # Überprüfung auf "Cup with Handle"-Formation
    if check_cup_with_handle(data):
        signals.append("Cup with Handle-Formation erkannt")

    return signals

def main():
    """
    Hauptprogramm, das die CSV-Datei einliest, die Kaufsignale überprüft und die Ergebnisse ausgibt.

    Args:
        None

    Returns:
        None
    """
    while True:
        filename = input("Bitte geben Sie den Dateinamen der CSV-Datei ein: ")
        symbols = read_stock_symbols(filename)

        results = []

        for symbol in symbols:
            print(f"Überprüfe Kaufsignale für {symbol}...")
            data = get_stock_data(symbol)
            signals = check_buy_signals(data)
            for signal in signals:
                results.append({"Symbol": symbol, "Signal": signal})

        if results:
            results_df = pd.DataFrame(results)
            print("\nErgebnisse:")
            display(results_df)
        else:
            print("Keine Kaufsignale gefunden.")

        another_calculation = input("Möchten Sie eine weitere Berechnung durchführen? (1 für Ja, 2 für Nein): ").strip()
        if another_calculation != '1':
            break

if __name__ == "__main__":
    main()
