import streamlit as st
import pandas as pd
import pandas_ta as ta
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime
import os
import parameters as p

st.set_page_config(page_title="Monitor-Market: TV Edition", layout="wide")

# TradingView Bağlantısı (Misafir Girişi)
@st.cache_resource
def get_tv_connection():
    return TvDatafeed()

def liste_yukle():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "inputs.txt")
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                # TradingView için .IS ekine gerek yok, sadece isim yeterli (Örn: THYAO)
                return [line.strip().upper().replace(".IS", "") for line in f.readlines() if line.strip()]
        else: return ["THYAO"]
    except: return ["THYAO"]

def get_data(tv, symbol):
    try:
        # BIST hisseleri için 'BIST' borsasını belirtiyoruz
        df = tv.get_hist(symbol=symbol, exchange='BIST', interval=Interval.in_1_hour, n_bars=100)
        
        if df is None or df.empty or len(df) < p.EMA_YAVAS:
            return None, None

        # Sütun isimlerini küçük harfe çevirelim (Standardizasyon için)
        df.columns = [x.lower() for x in df.columns]
        
        # İndikatörler
        df['ema_h'] = ta.ema(df['close'], length=p.EMA_HIZLI)
        df['ema_y'] = ta.ema(df['close'], length=p.EMA_YAVAS)
        df['rsi'] = ta.rsi(df['close'], length=p.RSI_PERIYOT)
        df['v_ma'] = ta.sma(df['volume'], length=p.HACIM_MA_PERIYOT)
        
        return df.iloc[-1], df['close'].iloc[-1]
    except:
        return None, None

# --- ARAYÜZ ---
st.title("🚀 Monitor-Market: TradingView Altyapısı")
tv = get_tv_connection()

# Parametreler
ka = getattr(p, 'KAR_AL_ORAN', 25.0)
zk = getattr(p, 'ZARAR_KES_ORAN', 5.0)

with st.expander("🛡️ Strateji Ayarları", expanded=False):
    st.write(f"**Kar Al:** %{ka} | **Zarar Kes:** %{zk} | **EMA:** {p.EMA_HIZLI}/{p.EMA_YAVAS}")

st.divider()
placeholder = st.empty()

while True:
    hisseler = liste_yukle()
    with placeholder.container():
        cols = st.columns(2)
        success_count = 0
        
        for idx, h in enumerate(hisseler):
            data, price = get_data(tv, h)
            
            if data is not None:
                success_count += 1
                trend_yukari = data['ema_h'] > data['ema_y']
                rsi_guclu = data['rsi'] > p.RSI_SINIR
                hacim_onay = data['volume'] > data['v_ma']
                
                # Risk Fiyatları
                tp_fiyat = price * (1 + ka / 100)
                sl_fiyat = price * (1 - zk / 100)
                
                if trend_yukari and rsi_guclu and hacim_onay:
                    durum = "🟢 GÜÇLÜ AL"
                elif not trend_yukari or data['rsi'] > p.RSI_ASIRI_ALIM:
                    durum = "🔴 SAT / RİSK"
                else:
                    durum = "🟡 BEKLE"

                with cols[idx % 2]:
                    with st.container(border=True):
                        st.subheader(f"{h} : {price:.2f} TL")
                        st.info(f"**Sinyal:** {durum}")
                        
                        d1, d2 = st.columns(2)
                        with d1:
                            st.write(f"RSI: `{round(data['rsi'], 1)}`")
                            st.write(f"Hacim: `{'✅' if hacim_onay else '❌'}`")
                        with d2:
                            st.success(f"🎯 Kar: {tp_fiyat:.2f}")
                            st.error(f"🛡️ Stop: {sl_fiyat:.2f}")
            
        st.write(f"⏱️ Güncelleme: {datetime.now().strftime('%H:%M:%S')}")
    
    time.sleep(p.GUNCELLEME_SANIYESI)
    st.rerun()