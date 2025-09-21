import pandas as pd
import numpy as np
import math

class PairTradingFinancialAnalysisDraft:
    '''
    Parameters:
    pair(tuple): A tuple with 2 stock names
    df_whole(df): A DataFrame that contains price history of all stocks (columns for each tickers)
    window(int): An integer that tells the class how many days to use for std when calculating z-score
    zscore_threshold(float): A float that defines how far away in std the spread must move before we open a trade
    margin_init(float): Your starting money in the margin account
    margin_ratio(float): Ratio of margin to buying power (leverage) (0.25 means for every $1 margin, you can trade $4 worth of stock)
    
    Attributes:
    stock1, stock2(str): The two stocks in the pair
    window, zscore_threshold, margin_init, margin_ratio: See Parameters
    margin(float): Current margin balance, starts at margin_init
    df_pair(df): A DataFrame with only the two chosen stocks' price history
    df_signal_summary(df): A DataFrame that stores trade summaries, initially empty
    df_margin(df): A DataFrame stores how margin changes after each trade, initially empty
    '''
    def __init__(self, pair, df_whole, window, zscore_threshold, margin_init, margin_ratio):
        self.stock1, self.stock2 = pair[0], pair[1]
        self.window = window
        self.zscore_threshold = zscore_threshold
        self.margin_init = margin_init
        self.margin_ratio = margin_ratio
        self.margin = margin_init
        self.df_pair = df_whole.loc[:, pair].copy()
        self.df_signal_summary = pd.DataFrame()
        self.df_margin = pd.DataFrame()

    # __repr__ is a special method, it defines how the object is shown (string representation) when you type the object's name in the console or print it
    def __repr__(self):
        return f"""PairTradingFinancialAnalysis(pair = {self.stock1} and {self.stock2}, 
                window = {self.window}, zscore_threshold = {self.zscore_threshold}, 
                margin_init = {self.margin_init}, margin_ratio = {self.margin_ratio})"""

    # Z-score tells us when the relationship between stock1 and stock2 looks unusual
    # High z-score -> stock1 is more expensive than stock2; Low z-score -> stock1 is cheaper than stock2
    def zscore_calculation(self):
        '''
        ratio:  Take ratio = log(price1/price2)
                Why?
                    1. Symmetric: log(2)=+0.693, log(0.5)=-0.693
                    2. Stability: Stock prices grow over time, log-ration helps make the series more stable and closer to stationary
        ma:     Moving average of the ratio over the chosen window (e.g. 10 days)
                .shift(1) means we use ytd's moving average, to avoid look-ahead bias
        msd:    Moving stardard deviation of the ratio over the chosen window
                .shifr(1) prevents using future info
        zscore: How many std away is today's ratio from normal?
                zscore = (ratio - ma)/msd
                if zscore = 0, ratio is exactly at its average
                if zscore = 2, ratio is 2 std above normal
                ...
        '''
        self.df_pair["ratio"] = np.log(self.df_pair[self.stock1] / self.df_pair[self.stock2])
        self.df_pair["ma"] = self.df_pair["ratio"].rolling(window=self.window).mean().shift(1)
        self.df_pair["msd"] = self.df_pair["ratio"].rolling(window=self.window).std().shift(1)
        self.df_pair["zscore"] = (self.df_pair["ratio"] - self.df_pair["ma"]) / self.df_pair["msd"]
        
    # Using z-score, we decide what to do (signal)
    def signal_calculation(self):
        '''
        1.  .nan: Initialize a new column signal that will hold buy/sell/hold decisions
        2.  Case 1: Overpriced (short spread)
                If z-score > threshold -> ratio is too high -> stock1 is expensive vs stock2 ->
                so set signal = -1 (short stock1, long stock2),
                prevent crazy outliers so zscore < 5
            Case 2: Underpriced (long spread)
                If z-score < - threshold -> ratio is too low -> stock1 is cheap vs stock2 ->
                so set signal = +1 (long stock1, short stock2)
                prevent crazy outliers so zscore > -5
            Case 3: Neutral zone (no trade)
                If -1 < z-score < 1 -> ratio is normal ->
                so set signal = 0 (flat, no position)
        3. .ffill(): If no new condition is triggered, keep the previous signal
                           There is no cases between threshold and +-1 -> in this range, no signal trigger
        4. .fillna(0): Fill remaining NaN with 0
        '''
        self.df_pair['signal'] = np.nan
        self.df_pair['signal'] = np.where((self.df_pair['zscore'] > self.zscore_threshold) & (self.df_pair['zscore'] < 5), -1, self.df_pair['signal'])
        self.df_pair['signal'] = np.where((self.df_pair['zscore'] < -self.zscore_threshold) & (self.df_pair['zscore'] > -5), 1, self.df_pair['signal'])
        self.df_pair['signal'] = np.where((self.df_pair['zscore'] > -1) & (self.df_pair['zscore'] < 1), 0, self.df_pair['signal'])
        self.df_pair['signal'] = self.df_pair['signal'].ffill() # Fill forward
        self.df_pair['signal'] = self.df_pair['signal'].fillna(0)  

    # Summarize trades based on signal changes
    def signal_summary(self):
        '''
        diff() -> difference between consecutive signals
        ne(0) -> True if signal changed
        cumsum() -> cumulative sum: assign a group number that increments each time signal changes
        '''
        self.df_pair["signal_group"] = self.df_pair["signal"].diff().ne(0).cumsum() 
        # Copies the index(date/time) of the DataFrame into a new column "time"
        self.df_pair["time"] = self.df_pair.index
        '''
        1. Combine all rows in the same signal group
        2. Pick the first row in each group for signal, time, stock1 and stock2 starting prices
        3. .reset_index turn the group object back into a regular DataFrame
        4. Rename columns as follows
        '''
        self.df_signal_summary = (self.df_pair
                        .groupby("signal_group")
                        .agg({"signal": "first", # +1, -1, 0
                                "time": "first", # start date
                                self.stock1: ["first"], 
                                self.stock2: ["first"]})
                            .reset_index(drop=True)
                            )
        self.df_signal_summary.columns = ["signal", "time_start","stock1_start_price", "stock2_start_price"]
        
        # Add columns for end time and  end price (moves next row's start become this row's end)
        self.df_signal_summary["time_end"] = self.df_signal_summary["time_start"].shift(-1)
        self.df_signal_summary["stock1_final_price"] = self.df_signal_summary["stock1_start_price"].shift(-1)
        self.df_signal_summary["stock2_final_price"] = self.df_signal_summary["stock2_start_price"].shift(-1)
        
        # Last trade has no next row, so fill manually (last date and last avaliable stock prices)
        self.df_signal_summary.loc[self.df_signal_summary.index[-1], "time_end"] = self.df_pair.index[-1]
        self.df_signal_summary.loc[self.df_signal_summary.index[-1], "stock1_final_price"] = self.df_pair[self.stock1].iloc[-1]
        self.df_signal_summary.loc[self.df_signal_summary.index[-1], "stock2_final_price"] = self.df_pair[self.stock2].iloc[-1]

        # Reorder columns
        self.df_signal_summary = self.df_signal_summary[["signal", "time_start", "time_end", 
                                                        "stock1_start_price", "stock1_final_price", 
                                                        "stock2_start_price", "stock2_final_price"]]

    def margin_calculation(self):
        margin = self.margin_init
        buying_power = margin / self.margin_ratio # Total amount you can trade, considering leverage
        # Copy the summary DataFrame to df_margin
        df_margin = self.df_signal_summary.copy()
        # Only keep actual trades (signal = +-1)
        df_margin = df_margin[df_margin['signal'].isin([1, -1])]
        
        # Go through each trade episode to calculate margin changes
        for i, row in df_margin.iterrows():
            # Split buying power equally, divide by starting price -> number of shares you can buy, then floor (round down) to nearest integer
            stock1_units = math.floor((0.5 * buying_power) / row["stock1_start_price"])
            stock2_units = math.floor((0.5 * buying_power) / row["stock2_start_price"])
            
            # Calculate commissions for buying and selling
            if row["signal"] == 1: # Long stock1, short stock2
                commision_buy = min(max(stock1_units * 0.005, 1), 0.5 * buying_power * 0.01)
                commision_sell = min(max(stock2_units * 0.005, 1), 0.5 * buying_power * 0.01) + 0.000008 * 0.5 * buying_power + 0.000166 * stock2_units
                total_commission = commision_buy + commision_sell
            else: # Signal == -1 -> Short stock1, long stock2
                commision_buy = min(max(stock2_units * 0.005, 1), 0.5 * buying_power * 0.01)
                commision_sell = min(max(stock1_units * 0.005, 1), 0.5 * buying_power * 0.01) + 0.000008 * 0.5 * buying_power + 0.000166 * stock1_units
                total_commission = commision_buy + commision_sell

            # Calculate margin
            if row["signal"] == 1:
                margin += ((row["stock1_final_price"] * 0.9997 - row["stock1_start_price"] * 1.0003) * stock1_units - 
                           (row["stock2_final_price"] * 1.0003 - row["stock2_start_price"] * 0.9997) * stock2_units) - total_commission
            else:
                margin += ((row["stock2_final_price"] * 0.9997 - row["stock2_start_price"] * 1.0003) * stock2_units - 
                           (row["stock1_final_price"] * 1.0003 - row["stock1_start_price"] * 0.9997) * stock1_units) - total_commission
                
            # Update margin and buying power for each iteration
            df_margin.loc[i, "margin"] = margin # Save margin for this trade in DataFrame
            buying_power = margin / self.margin_ratio # Recalculate buy power for next trade
            self.margin = margin # Update object's self.margin
            
        self.df_margin = df_margin
        
    # Main Run
    def trading_summary(self):
        self.zscore_calculation()
        self.signal_calculation()
        self.signal_summary()
        self.margin_calculation()
        # Create trading_result dictionary to summarize key parameters and final margin
        trading_result = {
            'pair': (self.stock1, self.stock2),
            'window': self.window,
            'zscore_threshold': self.zscore_threshold,
            'margin': self.margin
        }
        return trading_result
