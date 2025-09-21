        Wikipedia URL
              │
              ▼
 response = requests.get(url)
   (Response object: webpage HTML)

              │
              ▼
 sp500 = pd.read_html(StringIO(response.text))
   (List of DataFrames)

              │ pick first table
              ▼
 sp500 = sp500[0][["Symbol", "Date added"]]
   (DataFrame: 2 columns = Symbol, Date added)

              │ fix dates (fillna, to_datetime)
              ▼
 sp500 (DataFrame: Symbol = str, Date added = datetime)

              │ filter by start_time
              ▼
 sp500_list = sp500[sp500["Date added"] <= start_time]["Symbol"].to_list()
   (List of strings: ["AAPL", "MSFT", "GOOG", ...])

              │ download prices
              ▼
 data_1d = yf.download(sp500_list, ... )["Close"]
   (DataFrame: rows = dates, cols = tickers, values = float prices)

              │ slice time window
              ▼
 data_1d_corr = data_1d.loc[start_time_corr:final_time_corr]
   (DataFrame: subset of prices)

              │ compute correlation
              ▼
 corr_matrix = data_1d_corr.corr()
   (DataFrame: square matrix of correlations)

              │ mask upper triangle
              ▼
 upper_corr_matrix
   (DataFrame: same shape, but only upper half kept)

              │ flatten to 1D
              ▼
 stacked_corr = upper_corr_matrix.stack()
   (Series: index = (ticker1, ticker2), value = correlation)

              │ sort & select
              ▼
 sorted_corr = stacked_corr.sort_values(...)
 high_corr_pairs = sorted_corr.index[:3000].to_list()
   (List of tuples: [("MSFT","GOOG"), ("AAPL","MSFT"), ...])
