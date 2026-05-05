import yfinance as yf
import pandas as pd
import streamlit as st

def _clean_columns(df):
    """Fix MultiIndex columns from yfinance."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def resample_to_4h(df):
    """Resample 1h dataframe to 4h."""
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # FIX: Changed "4H" to "4h" for Pandas 2.0+ compatibility
    df_4h = df.resample("4h").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum"
    })
    df_4h.dropna(inplace=True)
    return df_4h

@st.cache_data(ttl=3600) 
def fetch_data(symbol, interval):
    """
    Fetches data using yfinance.
    Automatically determines period based on interval.
    """
    period_map = {
        "15m": "60d",   # Yfinance restricts 15m to last 60 days
        "1h":  "730d",  
        "1d":  "5y",    
        "4h":  "730d"   # We will fetch 1h and resample
    }
    
    # For 4h, we fetch 1h data to resample accurately
    fetch_interval = "1h" if interval == "4h" else interval
    period = period_map.get(interval, "1y")
    
    try:
        # Added timeout=10 to prevent the app from hanging on blank screen
        df = yf.download(
            symbol,
            period=period,
            interval=fetch_interval,
            progress=False,
            auto_adjust=True,
            timeout=10
        )
        
        if df.empty:
            return df

        df = _clean_columns(df)
        df.dropna(inplace=True)
        
        # Resample to 4h if requested
        if interval == "4h":
            df = resample_to_4h(df)
            
        return df

    except Exception as e:
        # This ensures errors are shown in the Streamlit UI instead of crashing the app
        st.error(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()