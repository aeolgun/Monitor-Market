import streamlit as st
import pandas as pd
import pandas_ta as ta
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime
import os
import parameters as p

st.set_page_config(page_title="BIST Karar Terminali", layout="wide")

# CSS: Gelişmiş Okunabilirlik ve Renkli Hacim
st.markdown("""
    <style>
    .stTable { background-color: rgba(255,255,255,0.05); border-radius: 10px; }
    .decision-box { padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 10px; font-size: 18px; }
    .data-row { display: flex; justify-content: space-between; padding: 5px 15px; border-bottom: 1px solid rgba(128, 128, 128, 0.1); }
    .data-label { color: #aaa !important; font-size: 12px; }
    .data-value { color: #fff !important; font-weight: bold; font-family: monospace; }
    .vol-low { color: #ff4b4b !important; }
    .vol-high { color: #00ff00 !important; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_tv_connection():
    return TvDatafeed()

def get_p(attr, default):
    return getattr(p, attr, default)

# --- ÜST STRATEJİ TABLOSU ---
def strateji_tablosu():
    st.subheader("📋 Mevcut Strateji Parametreleri")
    df_strat = pd.DataFrame({
        "Parametre": ["Zaman Dilimi", "Hızlı EMA", "Yavaş EMA", "RSI Periyot", "RSI Eşik", "Kar Al", "Zarar Kes"],
        "Değer": [get_p('ZAMAN_DILIMI','4h'), get_p('EMA_HIZLI',20), get_p('EMA_YAVAS',50), 
                  get_p('RSI_PERIYOT',14), get_p('RSI_SINIR',50), f"%{get_p('KAR_AL_ORAN',25)}", f"%{get_p('ZARAR_KES_ORAN',5)}"]
    })
    st.table(df_strat)

st.title("🛡️ BIST Karar & Takip Terminali")
strateji_tablosu()

tv = get_tv_connection()
placeholder = st.empty()

while True:
    Z_DILIMI = get_p('ZAMAN_DILIMI', '4h')
    interval_map = {'1h': Interval.in_1_hour, '4h': Interval.in_4_hour, '1d': Interval.in_daily}
    
    file_path = os.path.join(os.path.dirname(__file__), "inputs.txt")
    hisseler = ["THYAO", "ASELS"]
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            hisseler = [line.strip().upper().replace(".IS", "") for line in f.readlines() if line.strip()]

    with placeholder.container():
        cols = st.columns(3)
        for idx, h in enumerate(hisseler):
            try:
                df = tv.get_hist(symbol=h, exchange='BIST', interval=interval_map.get(Z_DILIMI), n_bars=200)
                if df is not None and not df.empty:
                    df.columns = [x.lower() for x in df.columns]
                    price = df['close'].iloc[-1]
                    rsi_v = ta.rsi(df['close'], length=get_p('RSI_PERIYOT', 14)).iloc[-1]
                    ema_h_v = ta.ema(df['close'], length=get_p('EMA_HIZLI', 20)).iloc[-1]
                    ema_y_v = ta.ema(df['close'], length=get_p('EMA_YAVAS', 50)).iloc[-1]
                    v_ma_v = ta.sma(df['volume'], length=get_p('HACIM_MA_PERIYOT', 20)).iloc[-1]
                    curr_v = df['volume'].iloc[-1]

                    # --- KARAR MEKANİZMASI ---
                    if ema_h_v > ema_y_v and rsi_v > get_p('RSI_SINIR', 50):
                        decision, bg, color = "🚀 AL", "#1b5e20", "white"
                    elif price > (ema_h_v * 1.02) and ema_h_v > ema_y_v:
                        decision, bg, color = "💎 TUT", "#0d47a1", "white" # Mavi
                    elif ema_h_v < ema_y_v:
                        decision, bg, color = "⚠️ SAT / ÇIK", "#b71c1c", "white"
                    else:
                        decision, bg, color = "⌛ BEKLE", "#f57f17", "white"

                    with cols[idx % 3]:
                        with st.container(border=True):
                            # Karar Kutusu
                            st.markdown(f'<div class="decision-box" style="background-color:{bg}; color:{color};">{h}: {decision}</div>', unsafe_allow_html=True)
                            
                            # Fiyat ve Teknik Veriler
                            st.markdown(f"""
                                <div class="data-row"><span class="data-label">Anlık Fiyat:</span><span class="data-value">{price:.2f} TL</span></div>
                                <div class="data-row"><span class="data-label">RSI Değeri:</span><span class="data-value">{rsi_v:.1f}</span></div>
                                <div class="data-row"><span class="data-label">EMA {get_p('EMA_HIZLI',20)}:</span><span class="data-value">{ema_h_v:.2f}</span></div>
                            """, unsafe_allow_html=True)
                            
                            # Hacim Kontrolü (Renkli Değer)
                            vol_color = "vol-high" if curr_v > v_ma_v else "vol-low"
                            st.markdown(f"""
                                <div class="data-row">
                                    <span class="data-label">Hacim:</span>
                                    <span class="data-value {vol_color}">{curr_v:,.0f}</span>
                                </div>
                            """, unsafe_allow_html=True)

                            st.divider()
                            # Hedefler
                            st.caption(f"🎯 Hedef: {price*(1+get_p('KAR_AL_ORAN',25)/100):.2f} | 🛡️ Stop: {price*(1-get_p('ZARAR_KES_ORAN',5)/100):.2f}")
                else:
                    cols[idx % 3].error(f"{h} Veri Yok")
            except: continue

        st.caption(f"⏱️ Son Güncelleme: {datetime.now().strftime('%H:%M:%S')} | Mod: {Z_DILIMI}")
    
    time.sleep(get_p('GUNCELLEME_SANIYESI', 60))
    st.rerun()