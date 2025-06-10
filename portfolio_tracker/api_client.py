import yfinance as yf
import pandas as pd

def get_current_price(ticker_symbol: str) -> float | None:
    """
    Fetches the current market price for a given ticker symbol.
    Tries 'regularMarketPrice', then 'currentPrice', then 'previousClose'.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        price = info.get('regularMarketPrice')
        if price is None:
            price = info.get('currentPrice')
        if price is None:
            price = info.get('previousClose')

        if price is not None:
            return float(price)
        else:
            print(f"Could not find current price for {ticker_symbol} in info object. Available keys: {info.keys()}")
            return None

    except Exception as e:
        print(f"Error fetching current price for {ticker_symbol}: {e}")
        return None

def get_historical_data(ticker_symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame | None:
    """
    Fetches historical market data for a given ticker symbol.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist_df = ticker.history(period=period, interval=interval)

        if hist_df.empty:
            print(f"No historical data found for {ticker_symbol} with period={period}, interval={interval}.")
            return None

        return hist_df

    except Exception as e:
        print(f"Error fetching historical data for {ticker_symbol}: {e}")
        return None

if __name__ == '__main__':
    # Simple test cases
    print("--- Testing get_current_price ---")
    test_tickers_price = ['AAPL', 'GOOGL', 'MSFT', 'NONEXISTENTTICKER']
    for t in test_tickers_price:
        price = get_current_price(t)
        if price is not None:
            print(f"Current price of {t}: ${price:.2f}")
        else:
            print(f"Could not fetch current price for {t}")

    print("\n--- Testing get_historical_data ---")
    test_tickers_hist = ['AAPL', 'GOOGL'] # Using valid tickers for history to avoid too many errors
    for t in test_tickers_hist:
        print(f"\nHistorical data for {t} (last 5 days of 1y period):")
        hist_data = get_historical_data(t, period="1y", interval="1d")
        if hist_data is not None:
            print(hist_data.tail())
        else:
            print(f"Could not fetch historical data for {t}")

    print("\n--- Test with potentially problematic ticker for history ---")
    hist_data_problem = get_historical_data("NONEXISTENTTICKERXYZ", period="1mo")
    if hist_data_problem is None:
        print("Fetching historical data for NONEXISTENTTICKERXYZ correctly returned None.")
    else:
        print("Fetching historical data for NONEXISTENTTICKERXYZ did not return None as expected.")

    print("\n--- Test get_current_price for a crypto (BTC-USD) ---")
    btc_price = get_current_price('BTC-USD')
    if btc_price is not None:
        print(f"Current price of BTC-USD: ${btc_price:.2f}")
    else:
        print(f"Could not fetch current price for BTC-USD")

    print("\n--- Test get_historical_data for a crypto (ETH-USD) ---")
    eth_hist = get_historical_data('ETH-USD', period="7d", interval="1d")
    if eth_hist is not None:
        print("Historical data for ETH-USD (last 7 days):")
        print(eth_hist)
    else:
        print("Could not fetch historical data for ETH-USD")
