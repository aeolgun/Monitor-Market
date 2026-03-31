import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime
import os
import parameters as p

# Sayfa Yapılandırması
st.set_page_config(page_title="Monitor-Market", layout="wide")

def liste_yukle():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "inputs.txt")
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return [line.strip().upper() for line in f.readlines() if line.strip()]
        else:
            return ["THYAO.IS"]
    except:
        return ["THYAO.IS"]

def get_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="60d", interval="1h")
        
        if df.empty or len(df) < p.EMA_YAVAS:
            return None, None

        # Hesaplamalar
        df['ema_h'] = ta.ema(df['Close'], length=p.EMA_HIZLI)
        df['ema_y'] = ta.ema(df['Close'], length=p.EMA_YAVAS)
        df['rsi'] = ta.rsi(df['Close'], length=p.RSI_PERIYOT)
        df['v_ma'] = ta.sma(df['Volume'], length=p.HACIM_MA_PERIYOT)
        
        return df.iloc[-1], df['Close'].iloc[-1]
    except:
        return None, None

# ARAYÜZ
st.title("📊 Monitor-Market: Detaylı Analiz")
hisseler = liste_yukle()

# Yan Menü Bilgi
st.sidebar.title("⚙️ Parametreler")
st.sidebar.write(f"Hızlı EMA: **{p.EMA_HIZLI}**")
st.sidebar.write(f"Yavaş EMA: **{p.EMA_YAVAS}**")
st.sidebar.write(f"RSI Periyot: **{p.RSI_PERIYOT}**")
st.sidebar.divider()
st.sidebar.write(f"Takipteki Hisse: {len(hisseler)}")

placeholder = st.empty()

while True:
    with placeholder.container():
        # Her satırda 2 hisse kartı göster
        cols = st.columns(2)
        
        for idx, h in enumerate(hisseler):
            data, price = get_data(h)
            
            if data is not None:
                # Sinyal Mantığı
                trend_yukari = data['ema_h'] > data['ema_y']
                rsi_guclu = data['rsi'] > p.RSI_SINIR
                hacim_onay = data['Volume'] > data['v_ma']
                
                if trend_yukari and rsi_guclu and hacim_onay:
                    durum, renk = "🟢 GÜÇLÜ AL", "green"
                elif not trend_yukari or data['rsi'] > p.RSI_ASIRI_ALIM:
                    durum, renk = "🔴 SAT / RİSK", "red"
                else:
                    durum, renk = "🟡 BEKLE / NÖTR", "gray"

                # Kart İçeriği
                with cols[idx % 2]:
                    with st.container(border=True):
                        st.subheader(f"{h.replace('.IS', '')} : {price:.2f} TL")
                        st.write(f"**Sinyal Kararı:** {durum}")
                        
                        # Parametre Detayları (3 Sütun)
                        c1, c2, c3 = st.columns(3)
                        c1.metric("EMA H/Y", f"{round(data['ema_h'],1)} / {round(data['ema_y'],1)}", 
                                  f"{round(data['ema_h'] - data['ema_y'], 1)}")
                        c2.metric("RSI", f"{round(data['rsi'], 1)}", 
                                  delta="Aşırı Alım" if data['rsi'] > 70 else None, delta_color="inverse")
                        
                        # Hacim bilgisini okunabilir yapalım (Milyon cinsinden)
                        hacim_milyon = data['Volume'] / 1_000_000
                        c3.metric("Hacim (M)", f"{hacim_milyon:.1f}", 
                                  "Onaylı" if hacim_onay else "Düşük")
                        
                        st.caption(f"Trend: {'YUKARI' if trend_yukari else 'AŞAĞI'} | Hacim Ort: {(data['v_ma']/1_000_000):.1f}M")
            
        st.divider()
        st.write(f"⏱️ Son Güncelleme: {datetime.now().strftime('%H:%M:%S')}")
        
        time.sleep(p.GUNCELLEME_SANIYESI)
        st.rerun()