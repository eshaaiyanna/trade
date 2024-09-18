import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

import alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame



# Define the path to your CSV file
file_path = 'C:/Users/Admin/Downloads/AAPL.csv'

# Load the CSV file into a DataFrame
data = pd.read_csv(file_path)

# Display the DataFrame
# print(data.head())


os.environ['APCA_API_BASE_URL'] = 'https://paper-api.alpaca.markets/v2'

api_key_id = 'PK9O3AR1MOP7QA3FA0PH'
api_secret_key = '22aU2EpIANoVhuZf9KjVaT9Quh4RFGi0ze3rLInj'
base_url = 'https://paper-api.alpaca.markets/v2'

# Initialize Alpaca API
api = tradeapi.REST(api_key_id, api_secret_key, base_url, api_version='v2')

# api_key = 'X9WMN3GN92Z39M5P'
# symbol = 'AAPL'
# url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}&outputsize=full&datatype=csv'

# data = pd.read_csv(url)
# data.to_csv('AAPL_data.csv', index=False)

# data = pd.read_csv('AAPL_data.csv')
# print(data.columns)

# data.rename(columns={"close": "Close"}, inplace=True)

# data["timestamp"] = pd.to_datetime(data["timestamp"])
# e = data.head()
# print(e)



# Analysis Code
short_window = 50
long_window = 200
data['Short_MA'] = data['Close'].rolling(window=short_window).mean()
data['Long_MA'] = data['Close'].rolling(window=long_window).mean()

# Step 5: Create signals for Moving Average Crossover Strategy
data['MASignal'] = 0
data.loc[data['Short_MA'] > data['Long_MA'], 'MASignal'] = 1


macd_short_ema = 12
macd_long_ema = 26
macd_signal_ema = 9

data['Short_EMA'] = data['Close'].ewm(span=macd_short_ema, adjust=False).mean()
data['Long_EMA'] = data['Close'].ewm(span=macd_long_ema, adjust=False).mean()
data['MACD_Line'] = data['Short_EMA'] - data['Long_EMA']
data['Signal_Line'] = data['MACD_Line'].ewm(span=macd_signal_ema, adjust=False).mean()

mean_window = 20

data['Mean'] = data['Close'].rolling(window=mean_window).mean()
data['Std'] = data['Close'].rolling(window=mean_window).std()
data['Z-Score'] = (data['Close'] - data['Mean']) / data['Std']
data['Mean_Rev_Buy'] = data['Z-Score'] < -2  # Buy signal
data['Mean_Rev_Sell'] = data['Z-Score'] > 2  # Sell signal

data['MA_Signal'] = 0
data.loc[data['Short_MA'] > data['Long_MA'], 'MA_Signal'] = 1  # Buy
data.loc[data['Short_MA'] < data['Long_MA'], 'MA_Signal'] = -1  # Sell

data['MACD_Signal'] = 0
data.loc[data['MACD_Line'] > data['Signal_Line'], 'MACD_Signal'] = 1  # Buy
data.loc[data['MACD_Line'] < data['Signal_Line'], 'MACD_Signal'] = -1  # Sell


print(data[['Date', 'Mean_Rev_Buy', 'Mean_Rev_Sell', 'MA_Signal', 'MACD_Signal']].head(10))

# Initialize Combined_Signal to 0
data['Combined_Signal'] = 0

# Update Combined_Signal to 1 for buy signals
data.loc[
    (data['Mean_Rev_Buy']) | (data['MA_Signal'] == 1) | (data['MACD_Signal'] == 1),
    'Combined_Signal'
] = 1

# Update Combined_Signal to -1 for sell signals
data.loc[
    (data['Mean_Rev_Sell']) | (data['MA_Signal'] == -1) | (data['MACD_Signal'] == -1),
    'Combined_Signal'
] = -1

print(data[['Date', 'Mean_Rev_Buy', 'Mean_Rev_Sell', 'MA_Signal', 'MACD_Signal','Combined_Signal']].head(100))
# # No Signal: Ensure that there are no NaN values in Combined_Signal
# data['Combined_Signal'].fillna(0, inplace=True)

# # Calculate Daily Returns
# data['Daily_Return'] = data['Close'].pct_change()

# # Calculate Strategy Returns: Use the previous day's Combined_Signal
# data['Strategy_Return'] = data['Daily_Return'] * data['Combined_Signal'].shift(1)

# # Calculate Cumulative Strategy Returns
# data['Cumulative_Strategy_Return'] = (1 + data['Strategy_Return']).cumprod()

# # Debugging: Print sample data to verify signals
# print(data[['Date', 'Close', 'Mean_Rev_Buy', 'Mean_Rev_Sell', 'MA_Signal', 'MACD_Signal', 'Combined_Signal', 'Daily_Return', 'Strategy_Return', 'Cumulative_Strategy_Return']].head(20))





def place_order(symbol, qty, side, order_type):
    try:
        order = api.submit_order(
            symbol='AAPL',
            qty=1,
            side='buy',
            type='market',
        )
        print(f"Order placed: {side} {qty} shares of {symbol}")
    except tradeapi.rest.APIError as e:
        print(f"Error placing order: {e.message}")


# # Sample function to place an order
# def place_order(signal, price):
#     try:
#         # Check if the signal is valid
#         if signal == 'buy':
#             print(f"Placing a buy order at {price}")
#             # Code to place buy order
#         elif signal == 'sell':
#             print(f"Placing a sell order at {price}")
#             # Code to place sell order
#         else:
#             print("Invalid signal")
#     except Exception as e:
#         print(f"Error placing order: {e}")




# Example trading decision
def execute_trades(data):
#     # print("Starting trade execution...")
#     # if not is_market_open():
#     #     print("Market is closed. No trades will be executed.")
#     #     return

    for index, row in data.iterrows():
        try:
            # print(f"Processing row {index}: {row.to_dict()}")
            
            symbol = row.get('symbol', 'AAPL')

            if row['Combined_Signal'] == 1:
                # print(f"Placing buy order for {symbol}")
                place_order(symbol=symbol, qty=1, side='buy', order_type='market')
            elif row['Combined_Signal'] == -1:
                # print(f"Placing sell order for {symbol}")
                place_order(symbol=symbol, qty=1, side='sell', order_type='market')

        except Exception as e:
            print(f"Error processing row {index}: {e}")

    print("Trade execution finished.")

# # Run the trading logic immediately
execute_trades(data)



