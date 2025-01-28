import yfinance as yf

def calculate_candle_ratios(ticker, n):
    """
    Berechnet die Anzahl der grünen und roten Kerzen und das Verhältnis zueinander
    für die letzten n Handelstage eines gegebenen Aktientickersymbols.

    :param ticker: Das Aktientickersymbol als String
    :param n: Die Anzahl der letzten Handelstage als Integer
    :return: Ein Dictionary mit der Anzahl der grünen und roten Kerzen und dem Verhältnis
    """
    # Laden der historischen Daten für den gegebenen Ticker
    data = yf.download(ticker, period=f'{n}d')
    
    # Initialisieren der Zähler für grüne und rote Kerzen
    green_candles = 0
    red_candles = 0
    
    # Durchlaufen der letzten n Tage und Zählen der grünen und roten Kerzen
    for index, row in data.iterrows():
        if row['Close'] > row['Open']:
            green_candles += 1
        elif row['Close'] < row['Open']:
            red_candles += 1
    
    # Berechnen des Verhältnisses
    if red_candles == 0:
        ratio = float('inf')  # Vermeidung der Division durch Null
    else:
        ratio = green_candles / red_candles
    
    # Rückgabe eines Dictionaries mit den Ergebnissen
    return {
        'green_candles': green_candles,
        'red_candles': red_candles,
        'ratio': ratio
    }

# Beispielaufruf der Funktion
result = calculate_candle_ratios('AAPL', 10)
print(result)