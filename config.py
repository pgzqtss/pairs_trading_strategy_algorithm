import pandas as pd
import datetime
import yfinance as yf
import requests
from io import StringIO
import logging
import numpy as np

# Configures logging to write error messages to a file
logging.basicConfig(filename='failed_downloads.log', level=logging.ERROR)

class SP500Data:
    # Initializes the SP500Data instance
    def __init__(self, months_back=26):
        self.url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        # Use headers to mimic a browser visit, avoid 403 errors
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/85.0.4183.121 Safari/537.36'
        }
        # initialize attributes
        self.months_back = months_back
        self.sp500 = None # DataFrame containing S&P500 data
        self.sp500_list = None # List of ticker symbols
        self.data_1d = None # DataFrame of daily closing prices
        self.high_corr_pairs = None # List of tuples of highly correlated stock pairs

        self.start_time = None
        self.end_time = None

    # Fetch S&P 500 list and filter by date added
    def fetch_sp500_list(self):
        response = requests.get(self.url, headers=self.headers)
        sp500_tables = pd.read_html(StringIO(response.text))
        sp500 = sp500_tables[0][["Symbol", "Date added"]]

        sp500['Date added'] = sp500['Date added'].fillna('1900-01-01')
        sp500['Date added'] = pd.to_datetime(
            sp500['Date added'], errors='coerce', format='%Y-%m-%d'
        )

        self.end_time = datetime.datetime.today()
        self.start_time = self.end_time - pd.DateOffset(months=self.months_back)
        self.sp500 = sp500
        self.sp500_list = sp500[sp500['Date added'] <= self.start_time]['Symbol'].to_list()

    # Download daily closing prices
    def download_data(self):
        try:
            self.data_1d = yf.download(
                self.sp500_list, start=self.start_time, end=self.end_time,
                interval='1d', auto_adjust=False
            )["Close"]
        except Exception as e:
            logging.error(f"Failed to download data: {e}")
            self.sp500_list = [t for t in self.sp500_list if t not in ['FTV', 'CSCO', 'BRK.B', 'BF.B']]
            self.data_1d = yf.download(
                self.sp500_list, start=self.start_time, end=self.end_time,
                interval='1d', auto_adjust=False
            )["Close"]

    # Compute top N highly correlated stock pairs
    def compute_high_corr_pairs(self, top_n=3000):
        start_time_corr = self.start_time
        final_time_corr = self.end_time - pd.DateOffset(days=60)

        data_1d_corr = self.data_1d.loc[start_time_corr:final_time_corr].copy()
        corr_matrix = data_1d_corr.corr()

        mask_upper_triangle = np.triu(np.ones(corr_matrix.shape), k=1)
        upper_corr_matrix = np.multiply(corr_matrix, mask_upper_triangle)

        stacked_corr = upper_corr_matrix.stack()
        sorted_corr = stacked_corr.sort_values(ascending=False)
        self.high_corr_pairs = sorted_corr.index[0:top_n].to_list()

    # Run the entire pipeline
    def run_pipeline(self):
        self.fetch_sp500_list()
        self.download_data()
        self.compute_high_corr_pairs()

