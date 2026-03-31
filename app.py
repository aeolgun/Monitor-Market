import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime
import parameters as p  # Parametre dosyasını içe aktar

st.set_page_config(page_title="Monitor-Market", layout="centered")

def liste_yukle():
    try:
        with open("inputs.txt", "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        return ["THYAO.IS"]

def get_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # EMA_YAVAS'tan daha fazla veri çekmeliyiz ki hesaplama doğru olsun
        df = ticker.history(period="1mo", interval="1h")
        
        if df.empty or len(df) < p.EMA_YAVAS:
            return None, None

        # Parametrik İndikatörler
        df['ema_h'] = ta.ema(df['Close'], length=p.EMA_HIZLI)
        df['ema_y'] = ta.ema(df['Close'], length=p.EMA_YAVAS)
        df['rsi'] = ta.rsi(df['Close'], length=p.RSI_PERIYOT)
        df['v_ma'] = ta.sma(df['Volume'], length=p.HACIM_MA_PERIYOT)
        
        return df.iloc[-1], df['Close'].iloc[-1]
    except:
        return None, None

st.title("📈 Monitor-Market")
st.caption(f"Strateji: EMA {p.EMA_HIZLI}/{p.EMA_YAVAS} | RSI {p.RSI_PERIYOT}")

placeholder = st.empty()

while True:
    hisseler = liste_yukle()
    
    with placeholder.container():
        for h in hisseler:
            data, price = get_data(h)
            if data is not None:
                # Parametrik Sinyal Mantığı
                trend_yukari = data['ema_h'] > data['ema_y']
                rsi_guclu = data['rsi'] > p.RSI_SINIR
                hacim_onay = data['Volume'] > data['v_ma']
                
                if trend_yukari and rsi_guclu and hacim_onay:
                    durum, renk = "🟢 GÜÇLÜ AL", "green"
                elif not trend_yukari or data['rsi'] > p.RSI_ASIRI_ALIM:
                    durum, renk = "🔴 SAT / RİSK", "red"
                else:
                    durum, renk = "🟡 BEKLE", "gray"

                with st.expander(f"{h.replace('.IS', '')} - {price:.2f} TL", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Sinyal", durum)
                    c2.metric("RSI", round(data['rsi'], 1))
                    c3.metric("Fiyat", f"{price:.2f}")
                    
        st.write(f"⏱️ Son Güncelleme: {datetime.now().strftime('%H:%M:%S')}")
        time.sleep(p.GUNCELLEME_SANIYESI)
        st.rerun()
