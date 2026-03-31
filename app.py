import streamlit as st
import pandas as pd
import pandas_ta as ta
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime
import os
import parameters as p

st.set_page_config(page_title="BIST Pro-Alarm", layout="wide")

# CSS: Yanıp sönen alarm efekti için küçük bir stil ekleyelim
st.markdown("""
    <style>
    @keyframes blinking {
        0% { background-color: #ff4b4b; box-shadow: 0 0 5px #ff4b4b; }
        50% { background-color: #ff0000; box-shadow: 0 0 20px #ff0000; }
        100% { background-color: #ff4b4b; box-shadow: 0 0 5px #ff4b4b; }
    }
    .alarm-box {
        padding: 10px;
        color: white;
        font-weight: bold;
        text-align: center;
        border-radius: 5px;
        animation: blinking 1.5s infinite;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Parametre Güvenliği
ZAMAN_DILIMI = getattr(p, 'ZAMAN_DILIMI', '4h')
GUNCELLEME = getattr(p, 'GUNCELLEME_SANIYESI', 60)

interval_map = {'1h': Interval.in_1_hour, '4h': Interval.in_4_hour, '1d': Interval.in_daily}

@st.cache_resource
def get_tv_connection():
    return TvDatafeed()

def liste_yukle():
    file_path = os.path.join(os.path.dirname(__file__), "inputs.txt")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return [line.strip().upper().replace(".IS", "") for line in f.readlines() if line.strip()]
    return ["THYAO", "ASELS"]

st.title("🚨 BIST Strateji & Alarm Terminali")
tv = get_tv_connection()
placeholder = st.empty()

while True:
    hisseler = liste_yukle()
    with placeholder.container():
        # --- ALARM PANELİ (Üst Kısım) ---
        alarm_listesi = []
        
        cols = st.columns(3)
        for idx, h in enumerate(hisseler):
            try:
                df = tv.get_hist(symbol=h, exchange='BIST', interval=interval_map.get(ZAMAN_DILIMI), n_bars=100)
                if df is not None and not df.empty:
                    df.columns = [x.lower() for x in df.columns]
                    price = df['close'].iloc[-1]
                    rsi = ta.rsi(df['close'], length=p.RSI_PERIYOT).iloc[-1]
                    ema_h = ta.ema(df['close'], length=p.EMA_HIZLI).iloc[-1]
                    ema_y = ta.ema(df['close'], length=p.EMA_YAVAS).iloc[-1]
                    
                    # Alarm Koşulları
                    is_bullish = ema_h > ema_y and rsi > p.RSI_SINIR
                    is_bearish = ema_h < ema_y or rsi > p.RSI_ASIRI_ALIM
                    
                    if is_bullish:
                        alarm_listesi.append(f"🚀 {h}: Alım Sinyali!")
                        bg_color, durum, icon = "#28a745", "ALIM BÖLGESİ", "✅"
                    elif is_bearish:
                        bg_color, durum, icon = "#dc3545", "RİSK / SAT", "⚠️"
                    else:
                        bg_color, durum, icon = "#6c757d", "NÖTR", "⌛"

                    # Kart Tasarımı
                    with cols[idx % 3]:
                        st.markdown(f"""
                            <div style="background-color:{bg_color}; padding:15px; border-radius:10px; color:white; border:2px solid #fff">
                                <h3 style="margin:0;">{icon} {h}</h3>
                                <p style="margin:0; font-size:20px; font-weight:bold;">{price:.2f} TL</p>
                                <hr style="margin:10px 0;">
                                <p style="margin:0;">Durum: {durum}</p>
                                <p style="margin:0;">RSI: {rsi:.1f}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Hedefler İçin Alt Panel
                        with st.container(border=True):
                            st.caption(f"🎯 Kar: {price*(1+p.KAR_AL_ORAN/100):.2f} | 🛡️ Stop: {price*(1-p.ZARAR_KES_ORAN/100):.2f}")

            except: continue

        # --- EKRANIN ÜSTÜNE YANIP SÖNEN ALARMLARI BAS ---
        if alarm_listesi:
            st.sidebar.markdown("### 🔔 AKTİF ALARMLAR")
            for a in alarm_listesi:
                st.sidebar.markdown(f'<div class="alarm-box">{a}</div>', unsafe_allow_html=True)

        st.write(f"⏱️ Son Kontrol: {datetime.now().strftime('%H:%M:%S')}")
        
    time.sleep(GUNCELLEME)
    st.rerun()