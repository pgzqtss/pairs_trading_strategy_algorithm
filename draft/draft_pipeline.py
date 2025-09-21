import pandas as pd
import datetime
import yfinance as yf
import requests
from io import StringIO
import logging
import numpy as np
import tkinter as tk
from tkinter import ttk
import plotly.graph_objs as go
from plotly.offline import plot
import webbrowser
import tempfile
import matplotlib.pyplot as plt

# Set up logging to record errors that occur during the download of stock data
logging.basicConfig(filename='failed_downloads.log', level=logging.ERROR)

url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

# Add a User-Agent header to the request to avoid 403 errors
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'}
response = requests.get(url, headers=headers) # Returns an HTTP response object as a string

# Use pandas to read the HTML content
sp500 = pd.read_html(StringIO(response.text)) # sp500 is a list of DataFrames, each representing a table found in the HTML content
sp500 = sp500[0][["Symbol", "Date added"]] # Selects the first table (so many rows(companies) with only the 'Symbol' and 'Date added' columns)
sp500['Date added'] = sp500['Date added'].fillna('1900-01-01')
sp500['Date added'] = pd.to_datetime(sp500['Date added'], errors='coerce', format='%Y-%m-%d')
'''
1.  pd.read_html can directly read from a URL or a file, however when you already have the HTML content as a string, 
    (response = requests.get(url).text), you need to convert it into a file-like object using StringIO before passing it to pd.read_html.
2.  Then access the first table in the list returned by pd.read_html using sp500[0].
3.  The 'Date added' column may contain NaT values if the conversion fails, so set a default date for NaN values before conversion.
4.  Use the correct date format '%Y-%m-%d' in pd.to_datetime to match the format of the dates in the 'Date added' column.
'''

end_time = datetime.datetime.today()
start_time = end_time - pd.DateOffset(months=26)

# Only want stocks added to the S&P 500 before the start_time
sp500_list = sp500[sp500['Date added'] <= start_time]['Symbol'].to_list()
# sp500_list is a list of strings(tickers symbols)

# Download daily close prices via Yahoo Finance with error handling
try:
    data_1d = yf.download(sp500_list, start=start_time, end=end_time, interval='1d', auto_adjust=False)["Close"]
    # data_1d = DataFrame, rows=dates(index), columns=tickers symbols, values=closing prices(floats)
except Exception as e:
    logging.error(f"Failed to download data: {e}")
    # Remove problematic tickers and try again
    sp500_list = [ticker for ticker in sp500_list if ticker not in ['FTV', 'CSCO', 'BRK.B', 'BF.B']]
    data_1d = yf.download(sp500_list, start=start_time, end=end_time, interval='1d', auto_adjust=False)["Close"]   
''' For Example:
            AAPL     MSFT     GOOG
Date                               
2023-07-01  187.2   340.3   120.6
2023-07-02  188.5   342.7   121.2

'''
    
# ----------------------------------------------------------------------------
'''
Split data into two parts:
1.  A 24-Month Period (Long-term historical window)
    Purpose: To calculate the correlation matrix and identify stock pairs that have historically moved together.
2.  A 60-Day Period (Recent High-frequency window)
    Purpose: To backtest the selected pairs using intraday or high-frequency data
             Act as a testing phase, you want to see if those historically correlated pairs still bahave as expected in the short term.
'''

# 24 months (from the earliest date to 2 months before end date)
start_time_corr = start_time
final_time_corr = end_time - pd.DateOffset(days=60)

# 60 days (the most recent 60 days)
start_time_reassurance = final_time_corr + pd.DateOffset(days=1)
final_time_reassurance = end_time

# Sclicing out a time range (still a DataFrame with tickers as columns, prices as values, dates as index)
data_1d_corr = data_1d.loc[start_time_corr:final_time_corr].copy()
corr_matrix = data_1d_corr.corr() #.corr() computes the person correlation coefficient between every pair of columns.
# replace index with correlation coefficients

# Flattens the matrix into 1D array and remove self-correlations
corr_values = corr_matrix.values.flatten()
corr_values = corr_values[(corr_values != 1)] # Exclude self-correlations (1s on the diagonal)

# Create a Upper Traingle = 1 else 0
'''
Upper Triangle avoids the duplicate pairs [A,B]=[B,A] and self-correlations [A,A].
np.ones(corr_matrix.shape) creates a matrix of ones with the same shape as the correlation matrix
np.triu(...) keeps only the upper triangle of the matrix, setting all other values to 0.
k=1 skips the diagonal, so you only get values above the diagonal
'''
mask_upper_triangle = np.triu(np.ones(corr_matrix.shape), k=1)

# Multiply corr matrix by the mask to keep only upper triangle values
upper_corr_matrix = np.multiply(corr_matrix, mask_upper_triangle)

# Converts the 2D DataFrame into 1D Series of (stock1, stock2) correlation pairs
# index = tuple of (stock1, stock2), value = correlation coefficient
stacked_corr = upper_corr_matrix.stack()
'''
(AAPL, MSFT)    0.85
(AAPL, GOOG)    0.77
(MSFT, GOOG)    0.92
'''

sorted_corr = stacked_corr.sort_values(ascending=False)
high_corr_pairs = sorted_corr.index[0:3000].to_list()  # Top 3000 pairs (list of tuples)

# Visualize the correlation distribution ------------------------------------
# Create main window
root = tk.Tk()
root.title("Stock Pair Visualizer")

# Dropdown(Combobox) for selecting stock pairs
pair_var = tk.StringVar()
pair_dropdown = ttk.Combobox(root, textvariable=pair_var)
pair_dropdown['values'] = [f"{pair[0]} & {pair[1]}" for pair in high_corr_pairs]
pair_dropdown.grid(row=0, column=0, padx=10, pady=10)

# Function to plot the selected stock pair
'''
1. Get the chosen pair from the dropdown menu.
2. Split into stock 1 and stock 2.
3. Build a Plotly figure with two y-axes (left=stock1, right=stock2).
4. Save it as a temporary HTML file and open in default web browser.
'''
def plot_selected_pair():
    selected = pair_var.get()
    if not selected:
        return   
    stock1, stock2 = selected.split(" & ")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data_1d.index, y=data_1d[stock1], name=stock1, yaxis="y1"))
    fig.add_trace(go.Scatter(x=data_1d.index, y=data_1d[stock2], name=stock2, yaxis="y2"))
    fig.update_layout(
        yaxis=dict(title=stock1, tickfont=dict(color="blue")),
        yaxis2=dict(title=stock2, tickfont=dict(color="red"), overlaying="y", side="right"),
        title="Stock Prices Over Time",
        xaxis_title="Date"
    )
    
    # Save to temp HTML and open in browser
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
        plot(fig, filename=tmpfile.name, auto_open=False)
        webbrowser.open(f"file://{tmpfile.name}")

# Button to plot the selected pair
plot_button = tk.Button(root, text="Plot Pair", command=plot_selected_pair)
plot_button.grid(row=0, column=1, padx=10, pady=10)

# Run the application
root.mainloop()