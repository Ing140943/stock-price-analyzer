# --- Import Required Libraries ---
import yfinance as yf   # For fetching stock data from Yahoo Finance
import pandas as pd     # For handling data in DataFrame format
import streamlit as st  # For building interactive web app UI
from sklearn.linear_model import LinearRegression   # For linear regression model
import matplotlib.pyplot as plt  # For plotting graphs
import matplotlib.dates as mdates
import numpy as np      # For numerical operations (e.g., arrays)

# --- Streamlit Page Configuration ---
# Title shown in browser tab
# Icon shown in browser tab (emoji or path to .png)
# Centered layout for better presentation
st.set_page_config(
    page_title="Stock Price Analyzer", 
    page_icon="arrow.png",
    layout="centered")
# --- Page Title ---
st.title("📈 Stock Price Analyzer (AI-Powered)")

# --- Input box: User enters stock symbol ---
ticker = st.text_input("Enter stock symbol (e.g., AAPL, TSLA):")

# --- If user inputs a stock ticker ---
if ticker:
    try:
        # --- Fetch 1-year historical stock price data ---
        data = yf.download(ticker, period="1y")
        # --- Handle case where no data is returned ---
        if data.empty:
            st.warning("No data found. Please check the stock symbol")
            st.stop()
        else:
            # --- Get additional stock/company information ---
            stock = yf.Ticker(ticker)
            info = stock.info

            # Extract company name and business summary
            company_name = info.get("longName", "N/A")
            st.subheader(f"🏢 {company_name}")
            
            full_description = info.get("longBusinessSummary", "No description available.")
            # --- Display Company Info ---
            max_length = 200
            # Show preview with inline toggle
            show_full = st.toggle("Read more", key="desc_toggle")
            # Show company description with 'Read more'
            if show_full:
                    st.markdown(full_description)
            else:
                preview = full_description[:max_length].rstrip() + "..."
                st.markdown(preview)


            # --- Show historical closing price chart ---
            st.subheader("📊 Historical Price (1 year)")
            st.line_chart(data['Close'])

            # --- Prepare data for ML model ---
            data = data.reset_index()
            # Convert dates to ordinal numbers (for regression)
            data['Date_ordinal'] = data['Date'].map(pd.Timestamp.toordinal)
            X = data['Date_ordinal'].values.reshape(-1, 1)
            y = data['Close'].values

            # --- Build and train Linear Regression model ---
            model = LinearRegression()
            model.fit(X, y)

            # --- Predict the next 7 days ---
            last_date = data['Date'].max()
            future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 31)]
            future_ordinals = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)
            future_preds = model.predict(future_ordinals)

            # Filter last 7 days of actual data
            last_7_days = data[data['Date'] >= (last_date - pd.Timedelta(days=7))]

            # Combine last 7 days + next 7 predicted days
            plot_dates = pd.concat([last_7_days['Date'], pd.Series(future_dates)], ignore_index=True)
            plot_prices = np.concatenate([last_7_days['Close'].values, future_preds])

            # --- Plot actual vs predicted prices ---
            st.subheader("📉 Predicted Price (Next 7 Days)")
            fig, ax = plt.subplots()
            # Plot recent actual prices
            ax.plot(last_7_days['Date'], last_7_days['Close'], label="Actual Price")
            # Plot predicted prices
            ax.plot(future_dates, future_preds, label="Predicted Price", linestyle='--')
            ax.set_xlabel("Date")
            ax.set_ylabel("Price ($)")
            ax.legend()

            # Set X-axis date format
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
            fig.autofmt_xdate(rotation=45)

            st.pyplot(fig)

            # --- Show simple trend indicator (Up/Down) ---
            direction = "🔺 Upward" if future_preds[-1] > y[-1] else "🔻 Downward"
            st.markdown(f"**Trend Prediction:** {direction}")


    except Exception as e:
        st.error(f"Error loading data: {e}")