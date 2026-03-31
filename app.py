import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime
import os
import parameters as p  # Tüm parametreleri buradan alıyoruz

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

        df['ema_h'] = ta.ema(df['Close'], length=p.EMA_HIZLI)
        df['ema_y'] = ta.ema(df['Close'], length=p.EMA_YAVAS)
        df['rsi'] = ta.rsi(df['Close'], length=p.RSI_PERIYOT)
        df['v_ma'] = ta.sma(df['Volume'], length=p.HACIM_MA_PERIYOT)
        return df.iloc[-1], df['Close'].iloc[-1]
    except:
        return None, None

# --- ARAYÜZ ÜST BİLGİ PANELİ (PARAMETRELER) ---
st.title("📊 Monitor-Market: Canlı Analiz")

# Parametreleri bir genişletilebilir panel içinde gösterelim (Ekranı kaplamasın diye)
with st.expander("⚙️ Mevcut Strateji Parametreleri (parameters.py)", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    c1.write(f"**Hızlı EMA:** {p.EMA_HIZLI}")
    c1.write(f"**Yavaş EMA:** {p.EMA_YAVAS}")
    c2.write(f"**RSI Periyot:** {p.RSI_PERIYOT}")
    c2.write(f"**RSI Eşik:** {p.RSI_SINIR}")
    c3.write(f"**RSI Aşırı Alım:** {p.RSI_ASIRI_ALIM}")
    c3.write(f"**Hacim MA:** {p.HACIM_MA_PERIYOT}")
    c4.write(f"**Güncelleme:** {p.GUNCELLEME_SANIYESI}s")

st.divider()

hisseler = liste_yukle()
placeholder = st.empty()

while True:
    with placeholder.container():
        cols = st.columns(2)
        
        for idx, h in enumerate(hisseler):
            data, price = get_data(h)
            
            if data is not None:
                # Sinyal Mantığı (Parametrelerden gelen değerlerle)
                trend_yukari = data['ema_h'] > data['ema_y']
                rsi_guclu = data['rsi'] > p.RSI_SINIR
                hacim_onay = data['Volume'] > data['v_ma']
                
                if trend_yukari and rsi_guclu and hacim_onay:
                    durum = "🟢 GÜÇLÜ AL"
                elif not trend_yukari or data['rsi'] > p.RSI_ASIRI_ALIM:
                    durum = "🔴 SAT / RİSK"
                else:
                    durum = "🟡 BEKLE / NÖTR"

                with cols[idx % 2]:
                    with st.container(border=True):
                        # Başlık: Hisse ve Anlık Fiyat
                        st.subheader(f"{h.replace('.IS', '')} : {price:.2f} TL")
                        st.info(f"**Karar:** {durum}")
                        
                        # Detaylı Parametre Değerleri
                        d1, d2, d3 = st.columns(3)
                        
                        # EMA Sütunu
                        d1.write("**EMA Durumu**")
                        d1.write(f"Hızlı ({p.EMA_HIZLI}): `{round(data['ema_h'], 2)}`")
                        d1.write(f"Yavaş ({p.EMA_YAVAS}): `{round(data['ema_y'], 2)}`")
                        
                        # RSI Sütunu
                        d2.write("**Momentum**")
                        d2.write(f"RSI ({p.RSI_PERIYOT}): `{round(data['rsi'], 1)}`")
                        rsi_durum = "Güçlü" if rsi_guclu else "Zayıf"
                        d2.write(f"Durum: `{rsi_durum}`")
                        
                        # Hacim Sütunu
                        d3.write("**Hacim Bilgisi**")
                        hacim_milyon = data['Volume'] / 1_000_000
                        ma_milyon = data['v_ma'] / 1