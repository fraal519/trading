from ib_insync import *
import pandas as pd

class IBOrderFetcher(IB):
    def __init__(self):
        super().__init__()  # Initialize without connection parameters
        
        # List to store completed orders
        self.completed_orders = []

        # Initialize the doneEvent
        self.doneEvent = Event()

    def completedOrder(self, orderId: int, contract: Contract, order: Order, orderState: OrderState):
        """
        Callback method that is called when a completed order is received.
        It prints all order details and stores them in a list.
        """
        print(f"Completed Order: {orderId}, {contract}, {order}, {orderState}")
        self.completed_orders.append({
            "orderId": orderId,
            "symbol": contract.symbol,
            "action": order.action,
            "totalQuantity": order.totalQuantity,
            "orderType": order.orderType,
            "lmtPrice": order.lmtPrice,
            "auxPrice": order.auxPrice,
            "status": orderState.status,
            "filledQuantity": orderState.filled,
            "remainingQuantity": orderState.remaining,
            "lastFillPrice": orderState.lastFillPrice,
            "commission": orderState.commission,
            "commissionCurrency": orderState.commissionCurrency
        })

        # Set the doneEvent when orders are received
        self.doneEvent.set()

    def fetch_orders(self):
        """
        Fetch and print completed orders.
        """
        print("Requesting completed orders...")
        self.reqCompletedOrders(True)
        self.doneEvent.wait()

    def display_completed_orders(self):
        """
        Display the fetched completed orders in a DataFrame.
        """
        if self.completed_orders:
            df = pd.DataFrame(self.completed_orders)
            print("Completed Orders:")
            print(df)
        else:
            print("No completed orders found.")

def main():
    # Initialize the IBOrderFetcher instance
    ib = IBOrderFetcher()
    
    # Connect to the IB Gateway or TWS using the correct port and client ID
    ib.connect('127.0.0.1', 4002, clientId=1)
    
    # Fetch completed orders
    ib.fetch_orders()

    # Display completed orders
    ib.display_completed_orders()

    # Disconnect from IBKR
    ib.disconnect()

if __name__ == "__main__":
    main()