from ib_insync import IB, Contract
import pandas as pd
from IPython.display import display

# Verbindung zur TWS herstellen
ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

# Portfolio-Daten abrufen
def fetch_portfolio_data():
    portfolio = ib.portfolio()
    portfolio_data = []
    for position in portfolio:
        data = {
            "Symbol": position.contract.symbol,
            "Position": position.position,
            "Marktpreis": position.marketPrice,
            "Marktwert": position.marketValue,
            "Durchschnittlicher Kaufpreis": position.averageCost,
            "Unrealisierter Gewinn/Verlust": position.unrealizedPNL,
            "Realisierter Gewinn/Verlust": position.realizedPNL,
            "Konto": position.account
        }
        portfolio_data.append(data)
    return portfolio_data

# Portfolio abrufen und in ein DataFrame umwandeln
portfolio_list = fetch_portfolio_data()
portfolio_df = pd.DataFrame(portfolio_list)

# Portfolio anzeigen
print("Portfolio:")
display(portfolio_df)
print("-" * 30)
print("-" * 30)

# Verkaufssignale prüfen
def check_sell_signals(row):
    signals = []
    # Beispiel-Kriterium 1: Kurs 25% höher als durchschnittlicher Kaufpreis
    if row["Marktpreis"] > row["Durchschnittlicher Kaufpreis"] * 1.25:
        signals.append("Kurs 25% über Kaufpreis")
    # Beispiel-Kriterium 2: Kurs 7% niedriger als durchschnittlicher Kaufpreis
    if row["Marktpreis"] < row["Durchschnittlicher Kaufpreis"] * 0.93:
        signals.append("Kurs 7% unter Kaufpreis")
    return ", ".join(signals) if signals else "Keine"

portfolio_df["Verkaufssignale"] = portfolio_df.apply(check_sell_signals, axis=1)

# Verkaufssignale anzeigen
def display_sell_signals(df):
    for _, row in df.iterrows():
        print(f"Aktie: {row['Symbol']}")
        print(f"Position: {row['Position']}")
        print(f"Marktpreis: {row['Marktpreis']}")
        print(f"Durchschnittlicher Kaufpreis: {row['Durchschnittlicher Kaufpreis']}")
        print(f"Unrealisierter Gewinn/Verlust: {row['Unrealisierter Gewinn/Verlust']}")
        print(f"Verkaufssignale: {row['Verkaufssignale']}")
        print("-" * 30)

display_sell_signals(portfolio_df)

# Verbindung trennen
ib.disconnect()