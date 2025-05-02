import streamlit as st
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
from st_click_detector import click_detector

# Ideas for improvement:
# 1. Add more stock tickers to the list.  #E - Completed
# 2. Allow users to input a custom date range for the stock data. #E
# 3. Allow users to provide their own tickers, with error handling for tickers not in the S&P500. (Remove the ability to click on the icons) #M - Completed
# 4. Show information about the stock (e.g., market cap, P/E ratio) alongside the chart. #M
# 5. Investment portfolio tracker: Allow users to input multiple stocks and return their portfolio's current worth. #H - Completed
# 6. Add a news section to show the latest news related to the selected stock (you can use the news attribute of yfinance.Ticker). #H

# Create the images as a href elements with tickers as IDs
def show_tickers():
    content = """
        <a href='#' id='MSFT'><img height='60px' width='60px' src='https://banner2.cleanpng.com/20180609/jq/aa8dbj2or.webp'></a>
        <a href='#' id='AAPL'><img height='60px' width='60px' src='https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg'></a>
        <a href='#' id='GOOGL'><img height='60px' width='60px' src='https://www.citypng.com/public/uploads/preview/google-logo-icon-gsuite-hd-701751694791470gzbayltphh.png'></a>
        <a href='#' id='AMZN'><img height='60px' width='60px' src='https://upload.wikimedia.org/wikipedia/commons/thumb/a/a9/Amazon_logo.svg/1024px-Amazon_logo.svg.png'></a>
        <a href='#' id='TSLA'><img height='60px' width='60px' src='https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Tesla_logo.png/600px-Tesla_logo.png'></a>
    """
    return content

# Load S&P500 tickers
def get_sp500_tickers():
    # Load S&P500 tickers from CSV
    url = "https://gist.githubusercontent.com/ZeccaLehn/f6a2613b24c393821f81c0c1d23d4192/raw/fe4638cc5561b9b261225fd8d2a9463a04e77d19/SP500.csv"
    try:
        sp500 = pd.read_csv(url)
        return sp500['Symbol'].tolist()
    except Exception as e:
        st.error(f"Error loading S&P 500 tickers: {e}")
        return []

# Make the images clickable using st_click_detector
def get_ticker():
    content = show_tickers()
    clicked = click_detector(content)
    return clicked

# Get the stock dataframe for the given ticker using yfinance
def get_dataframe(ticker):
    stock_data = yf.Ticker(ticker)
    df = stock_data.history(period="1y")
    df.reset_index(inplace=True)  # This moves the date from index to a column
    return df

# Create a candlestick chart using plotly
def plot_candlestick(df, ticker):
    fig = go.Figure(data=[go.Candlestick(x=df['Date'],
                                         open=df['Open'],
                                         high=df['High'],
                                         low=df['Low'],
                                         close=df['Close'])])
    fig.update_layout(title=f'{ticker} Stock Price', xaxis_title='Date', yaxis_title='Price (USD)')
    return fig

# Show a plotly chart in Streamlit
def show_plot(fig):
    st.plotly_chart(fig, use_container_width=True)

def portfolio_tracker():
    st.header("Investment Portfolio Tracker")
    
    # Session state to store portfolio stocks
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []
    
    # Input for new stock
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        new_stock = st.text_input("Add a stock ticker:")
    with col2:
        shares = st.number_input("Number of shares:", min_value=0.0, step=1.0)
    with col3:
        if st.button("Add to Portfolio"):
            if new_stock and shares > 0:
                # Check if ticker exists
                try:
                    stock = yf.Ticker(new_stock)
                    info = stock.info
                    if 'regularMarketPrice' not in info and 'currentPrice' not in info:
                        st.error(f"Could not find ticker {new_stock}")
                    else:
                        # Get current price
                        price = info.get('currentPrice', info.get('regularMarketPrice', 0))
                        # Add to portfolio
                        st.session_state.portfolio.append({
                            'ticker': new_stock,
                            'shares': shares,
                            'price': price,
                            'value': shares * price
                        })
                        st.success(f"Added {shares} shares of {new_stock}")
                except Exception as e:
                    st.error(f"Error adding stock: {e}")
    
    # Display portfolio
    if st.session_state.portfolio:
        # Create DataFrame from portfolio
        portfolio_df = pd.DataFrame(st.session_state.portfolio)
        
        # Calculate total value
        total_value = portfolio_df['value'].sum()
        
        # Show total portfolio value
        st.metric("Total Portfolio Value", f"${total_value:,.2f}")
        
        # Show portfolio table
        st.dataframe(portfolio_df[['ticker', 'shares', 'price', 'value']])
        
        # Portfolio chart
        if len(portfolio_df) > 1:  # Only show chart if more than one stock
            fig = go.Figure(data=[go.Pie(
                labels=portfolio_df['ticker'],
                values=portfolio_df['value'],
                hole=.3)])
            fig.update_layout(title="Portfolio Allocation")
            st.plotly_chart(fig)
        
        # Clear portfolio button
        if st.button("Clear Portfolio"):
            st.session_state.portfolio = []
            st.experimental_rerun()

# Main app
def main():
    st.title("📈 Stock Market Analysis App")
    
    # Create tabs for different app sections
    tab1, tab2 = st.tabs(["Stock Analysis", "Portfolio Tracker"])
    
    with tab1:
        # Method 1: Click on icons
        st.subheader("Option 1: Click on a company logo")
        ticker = get_ticker()
        
        # Method 2: Enter ticker
        st.subheader("Option 2: Enter a stock ticker")
        user_ticker = st.text_input("Enter a stock ticker (e.g., AAPL, MSFT):", "")
        
        # Validate ticker
        selected_ticker = ticker if ticker else user_ticker
        
        if selected_ticker:
            try:
                # Get and display stock data
                df = get_dataframe(selected_ticker)
                
                # Check if dataframe is empty
                if df.empty:
                    st.warning(f"No data available for {selected_ticker}.")
                else:
                    # Show stock chart
                    fig = plot_candlestick(df, selected_ticker)
                    show_plot(fig)
                    
                    # Warning if not in S&P500
                    sp500_tickers = get_sp500_tickers()
                    if selected_ticker not in sp500_tickers:
                        st.info(f"Note: {selected_ticker} is not in the S&P 500 index.")
            
            except Exception as e:
                st.error(f"Error loading data for {selected_ticker}: {e}")
                st.info("Please check that you entered a valid ticker symbol.")
    
    with tab2:
        portfolio_tracker()

if __name__ == "__main__":
    main()