import yfinance as yf
import pandas as pd

def calculate_candle_ratios(ticker, n):
    """
    Berechnet die Anzahl der grünen und roten Kerzen basierend auf dem Vortagesvergleich
    für die letzten n Handelstage eines gegebenen Aktientickersymbols.

    :param ticker: Das Aktientickersymbol als String
    :param n: Die Anzahl der zu berechnenden Kerzen
    :return: Ein Dictionary mit der Anzahl der grünen und roten Kerzen und dem Verhältnis
    """
    # Wir brauchen n+1 Tage, um n Kerzen zu berechnen
    extra_days = n + 1  

    # Zeitraum für yfinance bestimmen
    period = '6mo' if n <= 90 else '1y'

    # Historische Daten abrufen
    data = yf.download(ticker, period=period)

    # Prüfen, ob Daten vorhanden sind
    if data.empty:
        raise ValueError(f"Keine Daten für {ticker} gefunden.")

    # Sicherstellen, dass genügend Daten verfügbar sind
    if len(data) < extra_days:
        raise ValueError(f"Nicht genügend Daten: Nur {len(data)} statt {extra_days} verfügbar.")

    # Die letzten n+1 Handelstage auswählen
    data = data.iloc[-extra_days:]

    # Berechnung der Kerzenfarbe anhand des Vortags
    green_candles = 0
    red_candles = 0

    for i in range(1, len(data)):  # Start bei 1, weil wir den Vortag brauchen
        current_close = data["Close"].iloc[i].item()  # Sicherstellen, dass der Wert ein Scalar ist
        previous_close = data["Close"].iloc[i - 1].item()  # Sicherstellen, dass der Wert ein Scalar ist
        
        if current_close > previous_close:
            green_candles += 1
        elif current_close < previous_close:
            red_candles += 1

    # Verhältnis berechnen
    if red_candles == 0:
        ratio = 1.0
        result_text = "Es gibt nur grüne Kerzen"
    elif green_candles == 0:
        ratio = 1.0
        result_text = "Es gibt nur rote Kerzen"
    else:
        ratio = green_candles / red_candles
        result_text = ""

    return {
        'green_candles': green_candles,
        'red_candles': red_candles,
        'ratio': ratio,
    }

# Beispielaufruf für 20 Kerzen
result = calculate_candle_ratios('AAPL', 20)
print(result)