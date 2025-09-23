# Pairs Trading Strategy Algorithm

Pairs trading is a market-neutral strategy that involves taking a long position in one stock and a short position in another, based on their historical correlation.  
This project provides tools to identify stock pairs, generate trading signals, and visualize results.

---
## Pipeline
  - **config.py** prepares the data:
    - Fetches S&P 500 stock data from Wikipedia.
    - Downloads historical stock prices from Yahoo Finance.
    - Identifies correlated stock pairs.
  - **financial_analysis.py** runs the algorithm:
    - **Defining parameters and attributes:**
      - `pair`: Tuple of two stock tickers.
      - `df_whole`: DataFrame containing price history of all stocks.
      - `window`: Rolling window size for calculating moving averages and standard deviations.
      - `zscore_threshold`: Threshold for z-score to trigger trades.
      - `neutral_threshold`: Defines the z-score range where no trades are made (neutral zone).
      - `margin_init`: Initial margin balance.
      - `margin_ratio`: Leverage ratio.
      - `df_pair`: Extracts price data for the selected two stocks.
      - `df_signal_summary`: Stores trade summaries.
      - `df_margin`: Stores margin tracking.
    - **Z-score Calculation**
        - `z-score = (ratio - moving average) / moving standard deviation`, where
        - `ratio = log(price_stock1 / price_stock2)`
          - Logarithm ensures symmetry and stability.
    - **Signal Generation**
        - Case 1: Overpriced
          - z-score > threshold -> Stock1 overpriced -> Short stock1, long stock2 -> signal = -1
        - Case 2: Underpriced
          - z-score < -threshold -> Stock1 underpriced -> Long stock1, short stock2 -> signal = +1
        - Case 3: Neutral zone
          - |z| < neutral_threshold -> no position -> signal = 0
        - If there's no new condition is triggered, keep the previous signal
    - **Margin Calculation**
      - Groups trades by signal changes
      - Calculates the number of shares to trade based on available buying power.
      - Accounts for commissions and fees.
      - Updates the margin balance after each trade.
    - **Trading Summary**
      - Executes the entire trading process and returns a dictionary summarizing the trading parameters and final margin.
  - **visualizer.py** provides a GUI for visualizing and analysing stock pairs using the dictionary returned from 'financial_analysis.py'.




---

##  Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/pgzqtss/pairs_trading_strategy_algorithm.git
   cd pairs_trading_strategy_algorithm
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
3. (Optional) Create a .env file for environment-specific configurations.

## Usage
1. Run the Visualizer:
    ```bash
   python visualizer.py
2. Select a Stock Pair:
- Use the dropdown menu to select a pair of stocks.
- Adjust parameters such as window size, z-score threshold, and margin settings.
3. Analyze and Visualize:
- Click "Run Analysis" to compute trading signals and visualize results.
- The analysis includes z-score calculations, signal generation, and margin updates.

## Example
1. Select AXP & WAB from the dropdown menu and set the parameters (given a default)
   
   <img width="416" height="290" alt="image" src="https://github.com/user-attachments/assets/6c56837a-3370-42a3-ba3e-ccb5f9640c0c" />
3. Click Run Analysis to generate signals.
4. Result graph is displayed as below:
   
   <img width="1248" height="709" alt="image" src="https://github.com/user-attachments/assets/8060c17a-403c-4cac-b70c-ca10f9b26fb7" />

  The graph displays the price movements of two stocks:

  - Blue line: AXP (American Express)
  - Red line: WAB (Westinghouse Air Brake Technologies)
    
  Based on the selected parameters (e.g. window size, z-score threshold, margin), the algorithm       generates trading signals:

  - Green star: Indicates a long position on AXP (buy AXP, short WAB)
  - Red dot: Indicates a short position on AXP (sell AXP, long WAB)

  These signals are plotted directly on the price chart. At the end of the trading period, the algorithm calculates the final margin based on the executed trades, allowing us to evaluate the PnL (Profit and Loss) of this pairs trade.



## Dependencies
Python 3.8+
Libraries: numpy, pandas, matplotlib, yfinance, statsmodels, seaborn, scikit-learn, python-dotenv, streamlit, plotly, tkinter
## License
This project is licensed under the Apache License 2.0.

## Acknowledgments
Data sourced from Yahoo Finance and Wikipedia.

Visualization powered by Plotly and Tkinter.
## Contact
For questions or feedback, please contact znkjennifer58@gmail.com.
