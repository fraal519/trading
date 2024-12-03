from ib_insync import IB, util, Contract
import pandas as pd

# Verbindung zur TWS herstellen
ib = IB()
ib.connect('127.0.0.1', 4002, clientId=1)

# Portfolio-Daten abrufen
def fetch_portfolio():
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
            "Konto": position.account,
        }
        portfolio_data.append(data)
    return portfolio_data

# Offene Orders abrufen
def fetch_all_open_orders():
    ib.reqAllOpenOrders()  # Fordere alle offenen Orders an
    ib.sleep(2)  # Warte, bis die Daten geladen sind
    open_orders = ib.trades()  # Abruf der offenen Trades nach Anfrage
    orders_data = []
    for trade in open_orders:
        order = trade.order
        contract = trade.contract
        data = {
            "Symbol": contract.symbol,
            "Order ID": order.orderId,
            "Order Typ": order.orderType,
            "Menge": order.totalQuantity,
            "Preis": order.lmtPrice if order.orderType == "LMT" else "Marktpreis",
            "Richtung": order.action,
            "Status": trade.orderStatus.status,
        }
        orders_data.append(data)
    return orders_data

# Daten abrufen und in Tabellen umwandeln
portfolio_list = fetch_portfolio()
orders_list = fetch_all_open_orders()

# Portfolio-Daten in DataFrame
portfolio_df = pd.DataFrame(portfolio_list)
if portfolio_df.empty:
    print("Keine Portfoliodaten verfügbar.")
else:
    print("\n--- Portfolio-Daten ---\n")
    print(portfolio_df)

# Offene Orders in DataFrame
orders_df = pd.DataFrame(orders_list)
if orders_df.empty:
    print("\nKeine offenen Orders verfügbar.")
else:
    print("\n--- Offene Orders ---\n")
    print(orders_df)

# Verbindung trennen
ib.disconnect()