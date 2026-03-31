import streamlit as st
import pandas as pd
import pandas_ta as ta
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime
import os
import parameters as p

st.set_page_config(page_title="Monitor-Market: Debug Mode", layout="wide")

# TradingView Bağlantısı
@st.cache_resource
def get_tv_connection():
    return TvDatafeed()

def liste_yukle():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "inputs.txt")
    
    # DOSYA OKUMA TESTİ
    if not os.path.exists(file_path):
        st.sidebar.error(f"DOSYA YOK: {file_path}")
        return ["ASELS"] # ARTIK DEFAULT ASELS (Hata takibi için)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            icerik = [line.strip().upper().replace(".IS", "") for line in f.readlines() if line.strip()]
            if not icerik:
                st.sidebar.warning("Dosya boş!")
                return ["EREGL"] # Dosya boşsa EREGL getir
            return icerik
    except Exception as e:
        st.sidebar.error(f"Okuma Hatası: {e}")
        return ["KCHOL"] # Okuma hatasında KCHOL getir

def get_data(tv, symbol):
    try:
        # TradingView'den veri çekme denemesi
        df = tv.get_hist(symbol=symbol, exchange='BIST', interval=Interval.in_1_hour, n_bars=100)
        
        if df is None or df.empty:
            return "VERI_YOK", None
        
        if len(df) < p.EMA_YAVAS:
            return "YETERSIZ_BAR", None

        df.columns = [x.lower() for x in df.columns]
        df['ema_h'] = ta.ema(df['close'], length=p.EMA_HIZLI)
        df['ema_y'] = ta.ema(df['close'], length=p.EMA_YAVAS)
        df['rsi'] = ta.rsi(df['close'], length=p.RSI_PERIYOT)
        df['v_ma'] = ta.sma(df['volume'], length=p.HACIM_MA_PERIYOT)
        
        return df.iloc[-1], df['close'].iloc[-1]
    except Exception as e:
        return f"HATA: {str(e)}", None

# --- ARAYÜZ ---
st.title("🔍 Monitor-Market: Teşhis Modu")
tv = get_tv_connection()

hisseler = liste_yukle()
st.sidebar.write("### Okunan Liste:", hisseler) # Yan menüde listeyi teyit et

placeholder = st.empty()

while True:
    with placeholder.container():
        cols = st.columns(2)
        success_count = 0
        
        for idx, h in enumerate(hisseler):
            data, price = get_data(tv, h)
            
            # Eğer data bir string ise hata mesajı dönmüştür
            if isinstance(data, str):
                with cols[idx % 2]:
                    st.warning(f"⚠️ {h}: {data}") # Neden gelmediğini ekrana yaz
                continue

            if data is not None:
                success_count += 1
                # Hesaplamalar ve Görselleştirme (Öncekiyle aynı)
                trend_yukari = data['ema_h'] > data['ema_y']
                ka = getattr(p, 'KAR_AL_ORAN', 25.0)
                zk = getattr(p, 'ZARAR_KES_ORAN', 5.0)
                
                with cols[idx % 2]:
                    with st.container(border=True):
                        st.subheader(f"{h} : {price:.2f} TL")
                        st.write(f"RSI: `{round(data['rsi'], 1)}` | Trend: `{'Yukarı' if trend_yukari else 'Aşağı'}`")
                        st.caption(f"Hedefler: TP {price*(1+ka/100):.2f} / SL {price*(1-zk/100):.2f}")
            
        st.write(f"⏱️ Güncelleme: {datetime.now().strftime('%H:%M:%S')}")
    
    time.sleep(p.GUNCELLEME_SANIYESI)
    st.rerun()