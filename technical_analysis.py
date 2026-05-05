import pandas as pd
import numpy as np

def get_bollinger_bands(df, length=20, std_dev=2.0, ma_type="SMA", source="Close", offset=0):
    """
    Calculates Bollinger Bands and Band Width.
    """
    src = df[source]
    
    if ma_type == "SMA":
        basis = src.rolling(window=length).mean()
    elif ma_type == "EMA":
        basis = src.ewm(span=length, adjust=False).mean()
    elif ma_type == "SMMA (RMA)":
        basis = src.ewm(alpha=1/length, adjust=False).mean()
    elif ma_type == "WMA":
        weights = np.arange(1, length + 1)
        basis = src.rolling(window=length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)
    elif ma_type == "VWMA":
        pv = src * df['Volume']
        basis = pv.rolling(window=length).sum() / df['Volume'].rolling(window=length).sum()
    else:
        basis = src.rolling(window=length).mean()

    dev = src.rolling(window=length).std() * std_dev
    upper = basis + dev
    lower = basis - dev
    
    bbw = ((upper - lower) / basis) * 100

    if offset != 0:
        basis = basis.shift(-offset)
        upper = upper.shift(-offset)
        lower = lower.shift(-offset)
        bbw = bbw.shift(-offset)

    return {
        "basis": basis,
        "upper": upper,
        "lower": lower,
        "width": bbw
    }

def get_mfi(df, period=20):
    """
    Calculates Money Flow Index.
    Matches Pine Script: src = hlc3
    """
    # Pine Script: src = hlc3 (High + Low + Close) / 3
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    
    tp_diff = typical_price.diff()
    positive_flow = money_flow.where(tp_diff > 0, 0)
    negative_flow = money_flow.where(tp_diff < 0, 0)
    
    positive_mf = positive_flow.rolling(window=period, min_periods=1).sum()
    negative_mf = negative_flow.rolling(window=period, min_periods=1).sum()
    
    mfi_ratio = positive_mf / negative_mf.replace(0, pd.NA)
    mfi = 100 - (100 / (1 + mfi_ratio))
    return mfi