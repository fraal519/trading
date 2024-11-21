from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time


class TestApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.orderId = None
        self.connected_event = threading.Event()  # Signal für Verbindung
    
    def nextValidId(self, orderId):
        self.orderId = orderId
        self.connected_event.set()  # Signal, dass ID bereit ist
    
    def nextId(self):
        self.orderId += 1
        return self.orderId

    def error(self, reqId, errorCode, errorString, advancedOrderReject=""):
        print(f"Error - reqId: {reqId}, errorCode: {errorCode}, errorString: {errorString}, orderReject: {advancedOrderReject}")

    def contractDetails(self, reqId, contractDetails):
        attrs = vars(contractDetails)
        print("\n".join(f"{name}: {value}" for name, value in attrs.items()))
    
    def contractDetailsEnd(self, reqId):
        print("End of contract details")
        self.disconnect()


def main():
    app = TestApp()
    app.connect("127.0.0.1", 4002, 1)

    # Starten des Hintergrund-Threads
    thread = threading.Thread(target=app.run)
    thread.start()

    # Warten auf Verbindung
    if not app.connected_event.wait(timeout=10):
        print("Verbindung konnte nicht hergestellt werden.")
        app.disconnect()
        return

    # Vertrag konfigurieren
    mycontract = Contract()

    # Beispiel: Aktie (Stock)
    mycontract.symbol = "AAPL"
    mycontract.secType = "STK"
    mycontract.currency = "USD"
    mycontract.exchange = "SMART"
    mycontract.primaryExchange = "NASDAQ"

    # Beispiel: Future (auskommentieren, wenn nicht benötigt)
    # mycontract.symbol = "ES"
    # mycontract.secType = "FUT"
    # mycontract.currency = "USD"
    # mycontract.exchange = "CME"
    # mycontract.lastTradeDateOrContractMonth = "202412"

    # Beispiel: Option (auskommentieren, wenn nicht benötigt)
    # mycontract.symbol = "SPX"
    # mycontract.secType = "OPT"
    # mycontract.currency = "USD"
    # mycontract.exchange = "SMART"
    # mycontract.lastTradeDateOrContractMonth = "202412"
    # mycontract.right = "P"
    # mycontract.tradingClass = "SPXW"
    # mycontract.strike = 5300

    # Anfrage stellen
    app.reqContractDetails(app.nextId(), mycontract)

    # Programm läuft für eine Weile
    time.sleep(10)

    # Verbindung sauber beenden
    app.disconnect()
    thread.join()
    print("Programm beendet.")


if __name__ == "__main__":
    main()