from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.order import Order
from ibapi.contract import Contract
from decimal import Decimal

class TestApp(EClient, EWrapper):
    
    def __init__(self):
        EClient.__init__(self, self)
        self.order_id = 0

    def nextOrderId(self):
        """Callback für die nächste gültige Order-ID"""
        self.order_id += 1
        return self.order_id

    @staticmethod
    def BracketOrder(parentOrderId: int, action: str, quantity: Decimal, 
                     limitPrice: float, takeProfitLimitPrice: float, 
                     stopLossPrice: float):
        """Erstellt eine Bracket Order bestehend aus Eltern-, Take-Profit- und Stop-Loss-Order"""
        parent = Order()
        parent.orderId = parentOrderId
        parent.action = action
        parent.orderType = "LMT"
        parent.totalQuantity = quantity
        parent.lmtPrice = limitPrice
        parent.transmit = False

        takeProfit = Order()
        takeProfit.orderId = parent.orderId + 1
        takeProfit.action = "SELL" if action == "BUY" else "BUY"
        takeProfit.orderType = "LMT"
        takeProfit.totalQuantity = quantity
        takeProfit.lmtPrice = takeProfitLimitPrice
        takeProfit.parentId = parentOrderId
        takeProfit.transmit = False

        stopLoss = Order()
        stopLoss.orderId = parent.orderId + 2
        stopLoss.action = "SELL" if action == "BUY" else "BUY"
        stopLoss.orderType = "STP"
        stopLoss.auxPrice = stopLossPrice
        stopLoss.totalQuantity = quantity
        stopLoss.parentId = parentOrderId
        stopLoss.transmit = True

        return [parent, takeProfit, stopLoss]

    def placeBracketOrder(self):
        """Brackets Order mit der nächsten gültigen Order-ID platzieren"""
        bracket = self.BracketOrder(self.nextOrderId(), "BUY", 100, 30, 40, 20)
        contract = Contract()
        contract.symbol = "AAPL"
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        
        for order in bracket:
            self.placeOrder(order.orderId, contract, order)
        
    def openOrder(self, orderId: int, contract: Contract, order: Order, orderState: OrderState):
        print(f"openOrder. orderId: {orderId}, contract: {contract}, order: {order}, orderState: {orderState}")

    def orderStatus(self, orderId: int, status: str, filled: Decimal, remaining: Decimal, avgFillPrice: float, permId: int, parentId: int, lastFillPrice: float, clientId: int, whyHeld: str, mktCapPrice: float):
        print(f"orderStatus. orderId: {orderId}, status: {status}, filled: {filled}, remaining: {remaining}, avgFillPrice: {avgFillPrice}, permId: {permId}, parentId: {parentId}, lastFillPrice: {lastFillPrice}, clientId: {clientId}, whyHeld: {whyHeld}, mktCapPrice: {mktCapPrice}")

    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        print(f"execDetails. reqId: {reqId}, contract: {contract}, execution: {execution}")

app = TestApp()
app.connect("127.0.0.1", 4002, 1)  # Verbindung zu IB Gateway oder TWS
app.placeBracketOrder()  # Platzierung der Bracket Order
app.run()