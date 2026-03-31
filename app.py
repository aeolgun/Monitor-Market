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

st.title("📊 Monitor-Market: %25 Kar / %5 Zarar Takibi")

# Üst Panel Bilgilendirme
with st.expander("🛡️ Aktif Risk Yönetimi Ayarları", expanded=True):
    c1, c2, c3 = st.columns(3)
    c1.metric("Hedef Kar (TP)", f"%{p.KAR_AL_ORAN}")
    c2.metric("Maksimum Zarar (SL)", f"%{p.ZARAR_KES_ORAN}")
    c3.write(f"**Strateji:** EMA {p.EMA_HIZLI}/{p.EMA_YAVAS}")
    c3.write(f"**RSI:** {p.RSI_SINIR} Üzeri Güçlü")

st.divider()

hisseler = liste_yukle()
placeholder = st.empty()

while True:
    with placeholder.container():
        cols = st.columns(2)
        for idx, h in enumerate(hisseler):
            data, price = get_data(h)
            if data is not None:
                # Sinyal ve Risk Hesaplama
                trend_yukari = data['ema_h'] > data['ema_y']
                rsi_guclu = data['rsi'] > p.RSI_SINIR
                hacim_onay = data.get('Volume', 0) > data.get('v_ma', 0)
                
                # Dinamik Hedef Fiyatlar
                hedef_kar_fiyati = price * (1 + p.KAR_AL_ORAN / 100)
                zarar_kes_fiyati = price * (1 - p.ZARAR_KES_ORAN / 100)
                
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
                            st.write("**Teknik Göstergeler**")
                            st.write(f"RSI: `{round(data['rsi'], 1)}`")
                            st.write(f"Hacim Onayı: `{'VAR' if hacim_onay else 'YOK'}`")
                        
                        with d2:
                            st.write("**Fiyat Hedefleri**")
                            st.success(f"🎯 Kar Al: **{hedef_kar_fiyati:.2f}**")
                            st.error(f"🛡️ Stop: **{zarar_kes_fiyati:.2f}**")
                        
                        st.caption(f"Veri Zamanı: {datetime.now().strftime('%H:%M:%S')}")
            
        time.sleep(p.GUNCELLEME_SANIYESI)
        st.rerun()