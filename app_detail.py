# --- Import Required Libraries ---
import yfinance as yf   # ใช้ดึงข้อมูลราคาหุ้นจาก Yahoo Finance
import pandas as pd     # ใช้จัดการข้อมูลตาราง เช่น DataFrame
import streamlit as st  # ใช้สร้าง Web App UI แบบง่าย
from sklearn.linear_model import LinearRegression   # ใช้โมเดล AI แบบเส้นตรง
import matplotlib.pyplot as plt  # ใช้สร้างกราฟต่าง ๆ
import matplotlib.dates as mdates  # ใช้จัดรูปแบบวันที่บนแกน X
import numpy as np      # ใช้จัดการข้อมูลเชิงตัวเลข เช่น array

# --- Streamlit Page Configuration ---
st.set_page_config(                     # กำหนดค่าพื้นฐานของหน้าเว็บ
    page_title="Stock Price Analyzer",  # ชื่อแท็บในเบราว์เซอร์
    page_icon="arrow.png",              # ไอคอนในแท็บ (ใช้ emoji หรือ path ก็ได้)
    layout="centered"                   # จัด layout ให้อยู่ตรงกลาง
)

st.title("\ud83d\udcc8 Stock Price Analyzer (AI-Powered)")  # หัวข้อใหญ่บนหน้าเว็บ

# --- Input box: User enters stock symbol ---
ticker = st.text_input("Enter stock symbol (e.g., AAPL, TSLA):")  # สร้างกล่องให้ผู้ใช้กรอกชื่อหุ้น

# --- If user inputs a stock ticker ---
if ticker:
    try:
        # --- Fetch 1-year historical stock price data ---
        data = yf.download(ticker, period="1y")  # ดึงข้อมูลราคาหุ้นย้อนหลัง 1 ปี

        if data.empty:  # ถ้าไม่พบข้อมูลหุ้น
            st.warning("No data found. Please check the stock symbol")
            st.stop()   # หยุดการทำงานของโปรแกรมทันที

        # --- Get additional stock/company information ---
        stock = yf.Ticker(ticker)   # สร้างอ็อบเจกต์หุ้นจาก yfinance
        info = stock.info           # ดึงข้อมูลบริษัท เช่น ชื่อ, คำอธิบาย ฯลฯ

        company_name = info.get("longName", ticker.upper())  # ชื่อบริษัท ถ้าไม่มีใช้ชื่อหุ้นแทน
        st.subheader(f"\ud83c\udfe2 {company_name}")  # แสดงชื่อบริษัท

        full_description = info.get("longBusinessSummary", "No description available.")  # คำอธิบายบริษัท

        # --- Display Company Description with 'Read More' ---
        max_length = 200
        show_full = st.toggle("Read more", key="desc_toggle")  # สร้าง toggle ปุ่มเปิด-ปิด

        if show_full:
            st.markdown(full_description)  # แสดงข้อความเต็ม
        else:
            preview = full_description[:max_length].rstrip() + "..."
            st.markdown(preview)  # แสดงข้อความย่อ + ...

        # --- Show historical closing price chart ---
        st.subheader("\ud83d\udcca Historical Price (1 year)")
        st.line_chart(data['Close'])  # แสดงกราฟราคาปิดย้อนหลัง 1 ปี

        # --- Prepare data for ML model ---
        data = data.reset_index()  # คืนค่า index ให้กลายเป็น column
        data['Date_ordinal'] = data['Date'].map(pd.Timestamp.toordinal)  # แปลงวันที่เป็นเลข (ใช้กับโมเดล)
        X = data['Date_ordinal'].values.reshape(-1, 1)  # แปลงเป็นรูปแบบที่ sklearn ต้องการ (2 มิติ)
        y = data['Close'].values  # ราคาปิด (target ที่จะพยากรณ์)

        # --- Build and train Linear Regression model ---
        model = LinearRegression()  # สร้างโมเดล
        model.fit(X, y)             # ฝึกโมเดลด้วยข้อมูลจริง

        # --- Predict the next 7 days ---
        last_date = data['Date'].max()  # วันที่ล่าสุดในข้อมูลย้อนหลัง
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 31)]  # สร้างลิสต์วันที่ล่วงหน้า 30 วัน
        future_ordinals = np.array([d.toordinal() for d in future_dates]).reshape(-1, 1)  # แปลงวันที่เป็นตัวเลข
        future_preds = model.predict(future_ordinals)  # พยากรณ์ราคาด้วยโมเดล

        # Filter last 7 days of actual data
        last_7_days = data[data['Date'] >= (last_date - pd.Timedelta(days=7))]  # กรองเฉพาะข้อมูลจริง 7 วันล่าสุด

        # Combine last 7 days + next 7 predicted days
        plot_dates = pd.concat([last_7_days['Date'], pd.Series(future_dates)], ignore_index=True)
        plot_prices = np.concatenate([last_7_days['Close'].values, future_preds])

        # --- Plot actual vs predicted prices ---
        st.subheader("\ud83d\udcc9 Predicted Price (Next 7 Days)")
        fig, ax = plt.subplots()
        ax.plot(last_7_days['Date'], last_7_days['Close'], label="Actual Price")  # กราฟข้อมูลจริง
        ax.plot(future_dates, future_preds, label="Predicted Price", linestyle='--')  # กราฟพยากรณ์
        ax.set_xlabel("Date")
        ax.set_ylabel("Price ($)")
        ax.legend()

        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))  # จัดรูปแบบวันที่บนแกน X
        fig.autofmt_xdate(rotation=45)  # หมุนวันที่ให้เป็นแนวเฉียง

        st.pyplot(fig)  # แสดงกราฟบนหน้าเว็บ

        # --- Show simple trend indicator (Up/Down) ---
        direction = "\ud83d\udd3a Upward" if future_preds[-1] > y[-1] else "\ud83d\udd3b Downward"
        st.markdown(f"**Trend Prediction:** {direction}")

    except Exception as e:
        st.error(f"Error loading data: {e}")  # ถ้ามี error จะแสดงข้อความแจ้งเตือน
