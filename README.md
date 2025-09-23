# Pairs Trading Strategy Algorithm

Pairs trading is a **market-neutral strategy** that involves taking a long position in one stock and a short position in another, based on their historical correlation.  
This project provides tools to identify stock pairs, generate trading signals, and visualize results.

---

## Features
- **Data Pipeline**  
  - Fetches S&P 500 stock data from Wikipedia.  
  - Filters by date added to the index.  
  - Downloads historical price data via Yahoo Finance.  

- **Correlation Analysis**  
  - Identifies highly correlated stock pairs using **Pearson correlation coefficients**.  

- **Pair Trading Analysis**  
  - Computes **z-scores** of price spreads.  
  - Generates long/short trading signals.  
  - Calculates **profit and loss (PnL)** for chosen pairs.  

- **Visualization**  
  - Interactive **Tkinter + Plotly GUI**.  
  - Visualizes stock prices, signals, and trading performance.  

---

## Project Structure
pairs_trading_strategy_algorithm/

├── config.py # Data pipeline for fetching and processing S&P 500 data

├── financial_analysis.py # Core logic for pairs trading analysis

├── visualizer.py # GUI for visualizing pairs and results

├── draft/ # Draft files for experimentation

├── requirements.txt # Python dependencies

├── README.md # Project documentation

└── LICENSE # Apache License 2.0


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

  These signals are plotted directly on the price chart. At the end of the trading period, the algorithm calculates the final margin based on the executed trades, allowing us to evaluate the PnL (Profit and Loss) of this paris trade.



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
