import pandas as pd
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.account_summary_tags import AccountSummaryTags
import time

class TradeApp(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.account_data = []

    def accountSummary(self, reqId: int, account: str, tag: str, value: str, currency: str):
        """
        Collects the account summary data for account DU4662643 and stores it in a list of dictionaries.
        """
        # Only process data for account 'DU4662643'
        if account == "DU4662643":
            data = {
                'Account': account,
                'Tag': tag,
                'Value': value,
                'Currency': currency
            }
            self.account_data.append(data)
    
    def accountSummaryEnd(self, reqId: int):
        """
        Display the account summary data as a table when all data is received.
        """
        print(f"AccountSummaryEnd. ReqId: {reqId}")
        self.display_data()

    def display_data(self):
        """
        Displays the collected account summary data as a table using pandas.
        """
        # Convert the account data to a pandas DataFrame
        df = pd.DataFrame(self.account_data)
        
        # Display the table
        print("\nAccount Summary Data:")
        print(df.to_string(index=False))  # Display without row indices

def main():
    # Initialize the app
    app = TradeApp()
    
    # Connect to Interactive Brokers TWS (port 4002, clientId 1)
    app.connect("127.0.0.1", 4002, clientId=1)
    
    # Allow time for connection to establish
    time.sleep(1)
    
    # Request account summary for account 'DU4662643' only (using the specific account number)
    app.reqAccountSummary(9001, "DU4662643", AccountSummaryTags.AllTags)
    
    # Start the application's event loop to receive account summary data
    app.run()

if __name__ == "__main__":
    main()