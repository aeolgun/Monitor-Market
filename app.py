import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime
import os
import parameters as p

st.set_page_config(page_title="Monitor-Market", layout="wide")

def liste_yukle():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "inputs.txt")
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return [line.strip().upper() for line in f.readlines() if line.strip()]
        else: return ["THYAO.IS"]
    except: return ["THYAO.IS"]

def get_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="60d", interval="1h")
        if df.empty or len(df) < p.EMA_YAVAS: return None, None
        
        df['ema_h'] = ta.ema(df['Close'], length=p.EMA_HIZLI)
        df['ema_y'] = ta.ema(df['Close'], length=p.EMA_YAVAS)
        df['rsi'] = ta.rsi(df['Close'], length=p.RSI_PERIYOT)
        df['v_ma'] = ta.sma(df['Volume'], length=p.HACIM_MA_PERIYOT)
        
        return df.iloc[-1], df['Close'].iloc[-1]
    except: return None, None

st.title("📊 Monitor-Market: Risk & Analiz")

# Üst Panel
with st.expander("🛡️ Aktif Strateji Ayarları", expanded=True):
    c1, c2, c3 = st.columns(3)
    # Parametrelerin varlığını kontrol ederek hata önleme
    ka = getattr(p, 'KAR_AL_ORAN', 25.0)
    zk = getattr(p, 'ZARAR_KES_ORAN', 5.0)
    
    c1.metric("Hedef Kar", f"%{ka}")
    c2.metric("Zarar Kes", f"%{zk}")
    c3.write(f"**EMA:** {p.EMA_HIZLI}/{p.EMA_YAVAS} | **RSI:** {p.RSI_SINIR}")

st.divider()

hisseler = liste_yukle()
placeholder = st.empty()

while True:
    hisseler = liste_yukle() # Listeyi her döngüde yenile
    with placeholder.container():
        cols = st.columns(2)
        for idx, h in enumerate(hisseler):
            data, price = get_data(h)
            if data is not None:
                trend_yukari = data['ema_h'] > data['ema_y']
                rsi_guclu = data['rsi'] > p.RSI_SINIR
                hacim_onay = data.get('Volume', 0) > data.get('v_ma', 0)
                
                # Dinamik Fiyatlar
                ka_fiyat = price * (1 + ka / 100)
                zk_fiyat = price * (1 - zk / 100)
                
                if trend_yukari and rsi_guclu and hacim_onay:
                    durum = "🟢 GÜÇLÜ AL"
                elif not trend_yukari or data['rsi'] > p.RSI_ASIRI_ALIM:
                    durum = "🔴 SAT / RİSK"
                else:
                    durum = "🟡 BEKLE"

                with cols[idx % 2]:
                    with st.container(border=True):
                        st.subheader(f"{h.replace('.IS', '')} : {price:.2f} TL")
                        st.info(f"**Sinyal:** {durum}")
                        
                        d1, d2 = st.columns(2)
                        with d1:
                            st.write("**Teknik Gösterge**")
                            st.write(f"RSI: `{round(data['rsi'], 1)}`")
                            st.write(f"Hacim: `{'✅' if hacim_onay else '❌'}`")
                        
                        with d2:
                            st.write("**Hedef Seviyeler**")
                            st.success(f"🎯 Kar: {ka_fiyat:.2f}")
                            st.error(f"🛡️ Stop: {zk_fiyat:.2f}")
            
        st.write(f"⏱️ Güncelleme: {datetime.now().strftime('%H:%M:%S')}")
    time.sleep(p.GUNCELLEME_SANIYESI)
    st.rerun()