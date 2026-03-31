import streamlit as st
import pandas as pd
import pandas_ta as ta
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime
import os
import parameters as p

st.set_page_config(page_title="Monitor-Market: Dosya Denetimi", layout="wide")

@st.cache_resource
def get_tv_connection():
    return TvDatafeed()

def liste_yukle():
    # Mevcut klasörü ve üst klasörü kontrol et
    possible_paths = [
        os.path.join(os.getcwd(), "inputs.txt"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "inputs.txt"),
        "inputs.txt"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return [line.strip().upper().replace(".IS", "") for line in f.readlines() if line.strip()]
            except:
                continue
    
    # HİÇBİRİ ÇALIŞMAZSA BURASI ÇALIŞIR
    st.sidebar.error(f"Kritik Hata: inputs.txt hiçbir yerde bulunamadı!")
    st.sidebar.info(f"Baktığım yerler: {possible_paths}")
    return ["EREGL", "SASA", "THYAO"] # Bu sefer 3 farklı hisse döndürelim ki default olduğunu anlayalım

# --- ANA KOD ---
st.title("🚀 Monitor-Market: Veri Akışı")
tv = get_tv_connection()
hisseler = liste_yukle()

st.sidebar.success(f"Okunan Hisseler: {', '.join(hisseler)}")

placeholder = st.empty()
while True:
    with placeholder.container():
        cols = st.columns(2)
        for idx, h in enumerate(hisseler):
            try:
                df = tv.get_hist(symbol=h, exchange='BIST', interval=Interval.in_1_hour, n_bars=100)
                if df is not None and not df.empty:
                    df.columns = [x.lower() for x in df.columns]
                    price = df['close'].iloc[-1]
                    
                    # Göstergeler
                    rsi = ta.rsi(df['close'], length=p.RSI_PERIYOT).iloc[-1]
                    ema_h = ta.ema(df['close'], length=p.EMA_HIZLI).iloc[-1]
                    ema_y = ta.ema(df['close'], length=p.EMA_YAVAS).iloc[-1]
                    
                    with cols[idx % 2]:
                        with st.container(border=True):
                            st.subheader(f"{h} : {price:.2f} TL")
                            st.write(f"RSI: `{round(rsi, 1)}` | Trend: `{'Yukarı' if ema_h > ema_y else 'Aşağı'}`")
                            st.caption(f"Hedefler: TP {price*1.25:.2f} / SL {price*0.95:.2f}")
            except:
                st.error(f"{h} verisi çekilemedi.")
                
        st.write(f"⏱️ Güncelleme: {datetime.now().strftime('%H:%M:%S')}")
    time.sleep(p.GUNCELLEME_SANIYESI)
    st.rerun()