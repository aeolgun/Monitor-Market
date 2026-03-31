import streamlit as st
import pandas as pd
import pandas_ta as ta
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime
import os
import parameters as p

st.set_page_config(page_title="BIST Karar Terminali", layout="wide")

# CSS: Karanlık Mod ve Dinamik Tasarım
st.markdown("""
    <style>
    .stContainer { border-radius: 15px; background-color: rgba(255,255,255,0.05); border: 1px solid rgba(128,128,128,0.2); padding: 0px !important; margin-bottom: 20px; }
    .decision-box { padding: 12px; border-radius: 10px; text-align: center; font-weight: bold; margin-bottom: 10px; font-size: 20px; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }
    .data-row { display: flex; justify-content: space-between; padding: 6px 15px; border-bottom: 1px solid rgba(128,128,128,0.1); }
    .data-label { color: #999 !important; font-size: 13px; font-weight: bold; }
    .data-value { color: #00ff00 !important; font-weight: 800; font-family: 'Courier New', monospace; font-size: 15px; }
    .vol-low { color: #ff4b4b !important; }
    .vol-high { color: #00ff00 !important; }
    .target-box { background-color: rgba(0,255,0,0.05); padding: 10px; border-radius: 8px; margin-top: 10px; border: 1px dashed #444; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_tv_connection():
    return TvDatafeed()

def get_p(attr, default):
    return getattr(p, attr, default)

st.title("🛡️ BIST Profesyonel Karar Destek")

# --- STRATEJİ ÖZETİ ---
with st.expander("📋 Aktif Strateji Parametrelerini Gör", expanded=True):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Zaman Dilimi", get_p('ZAMAN_DILIMI','4h'))
    c2.metric("EMA Hızlı/Yavaş", f"{get_p('EMA_HIZLI',20)} / {get_p('EMA_YAVAS',50)}")
    c3.metric("RSI Giriş (AL)", get_p('RSI_SINIR',50))
    c4.metric("RSI Kar Al (SAT)", get_p('RSI_ASIRI_ALIM',70))
    c5.metric("Hedef Kar/Stop", f"%{get_p('KAR_AL_ORAN',25)} / %{get_p('ZARAR_KES_ORAN',5)}")

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

                    # --- KARAR MANTIĞI ---
                    has_position = False
                    if ema_h_v > ema_y_v and get_p('RSI_ASIRI_ALIM',70) > rsi_v > get_p('RSI_SINIR', 50):
                        decision, bg, has_position = "🚀 AL", "#1b5e20", True
                    elif price > (ema_h_v * 0.99) and ema_h_v > ema_y_v and rsi_v < get_p('RSI_ASIRI_ALIM',70):
                        decision, bg, has_position = "💎 TUT", "#0d47a1", True
                    elif ema_h_v < ema_y_v or rsi_v >= get_p('RSI_ASIRI_ALIM',70):
                        msg = "KAR AL" if rsi_v >= get_p('RSI_ASIRI_ALIM',70) else "RİSKLİ / SAT"
                        decision, bg, has_position = f"⚠️ {msg}", "#b71c1c", True
                    else:
                        decision, bg, has_position = "⌛ BEKLE", "#444", False

                    with cols[idx % 3]:
                        with st.container(border=True):
                            st.markdown(f'<div class="decision-box" style="background-color:{bg}; color:white;">{h}: {decision}</div>', unsafe_allow_html=True)
                            
                            st.markdown(f"""
                                <div class="data-row"><span class="data-label">Fiyat:</span><span class="data-value" style="color:white !important;">{price:.2f} TL</span></div>
                                <div class="data-row"><span class="data-label">EMA {get_p('EMA_HIZLI',20)}/{get_p('EMA_YAVAS',50)}:</span><span class="data-value">{ema_h_v:.1f} / {ema_y_v:.1f}</span></div>
                                <div class="data-row"><span class="data-label">RSI Değeri:</span><span class="data-value">{rsi_v:.1f}</span></div>
                            """, unsafe_allow_html=True)
                            
                            v_col = "vol-high" if curr_v > v_ma_v else "vol-low"
                            st.markdown(f"""
                                <div class="data-row" style="border:none;">
                                    <span class="data-label">Hacim (G/O):</span>
                                    <span class="data-value {v_col}">{curr_v:,.0f} / {v_ma_v:,.0f}</span>
                                </div>
                            """, unsafe_allow_html=True)

                            if has_position:
                                ka = price * (1 + get_p('KAR_AL_ORAN', 25) / 100)
                                zk = price * (1 - get_p('ZARAR_KES_ORAN', 5) / 100)
                                st.markdown(f'<div class="target-box"><p style="margin:0; font-size:13px; color:#aaa; text-align:center;">🎯 Hedef: <b style="color:#00ff00;">{ka:.2f}</b> | 🛡️ Stop: <b style="color:#ff4b4b;">{zk:.2f}</b></p></div>', unsafe_allow_html=True)
                            else:
                                st.markdown('<div style="height:50px; display:flex; align-items:center; justify-content:center; color:#666; font-size:12px; font-style:italic;">Nötr / Pozisyon Bekleniyor</div>', unsafe_allow_html=True)
            except: continue

        st.caption(f"⏱️ Son Güncelleme: {datetime.now().strftime('%H:%M:%S')} | Mod: {Z_DILIMI}")
    
    time.sleep(get_p('GUNCELLEME_SANIYESI', 60))
    st.rerun()