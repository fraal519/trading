import yfinance as yf
import pandas as pd

def calculate_candle_ratios(ticker, n):
    """
    Berechnet die Anzahl der grünen und roten Kerzen und das Verhältnis zueinander
    für die letzten n Handelstage eines gegebenen Aktientickersymbols.

    :param ticker: Das Aktientickersymbol als String
    :param n: Die Anzahl der letzten Handelstage als Integer
    :return: Ein Dictionary mit der Anzahl der grünen und roten Kerzen und dem Verhältnis
    """
    # Umwandlung von Tagen in einen gültigen Zeitraum für yfinance
    if n <= 5:
        period = '1mo'
    elif n <= 30:
        period = '3mo'
    elif n <= 90:
        period = '6mo'
    elif n <= 180:
        period = '1y'
    elif n <= 365:
        period = '2y'
    elif n <= 730:
        period = '5y'
    else:
        period = '10y'
    
    # Laden der historischen Daten für den gegebenen Ticker
    data = yf.download(ticker, period=period)
    
    # Überprüfen, ob Daten geladen wurden
    if data.empty:
        raise ValueError(f"Keine Daten für Ticker {ticker} gefunden.")
    
    # Überprüfen, ob genügend Daten vorhanden sind
    if len(data) < n:
        raise ValueError(f"Nicht genügend Daten vorhanden. Nur {len(data)} Handelstage verfügbar.")
    
    # Auswahl der letzten n Handelstage
    data = data.iloc[-n:]
    
    # Initialisieren der Zähler für grüne und rote Kerzen
    green_candles = 0
    red_candles = 0
    
    # Durchlaufen der letzten n Tage und Zählen der grünen und roten Kerzen
    for index, row in data.iterrows():
        close_value = row['Close'].item()
        open_value = row['Open'].item()
        if close_value > open_value:
            green_candles += 1
        elif close_value < open_value:
            red_candles += 1
    
    # Berechnen des Verhältnisses
    if red_candles == 0:
        ratio = 1.0
        result_text = "Es gibt nur grüne Kerzen"
    elif green_candles == 0:
        ratio = 1.0
        result_text = "Es gibt nur rote Kerzen"
    else:
        ratio = green_candles / red_candles
        result_text = ""
    
    # Rückgabe eines Dictionaries mit den Ergebnissen
    return {
        'green_candles': green_candles,
        'red_candles': red_candles,
        'ratio': ratio,
        'result_text': result_text
    }

# Beispielaufruf der Funktion
result = calculate_candle_ratios('AAPL', 20)
print(result)