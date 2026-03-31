import streamlit as st
import pandas as pd
import pandas_ta as ta
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime
import os
import parameters as p

st.set_page_config(page_title="BIST Strateji Terminali", layout="wide")

# CSS: Dinamik ve Okunaklı Arayüz
st.markdown("""
    <style>
    .decision-box { padding: 12px; border-radius: 10px; text-align: center; font-weight: bold; margin-bottom: 10px; font-size: 20px; border: 1px solid rgba(255,255,255,0.2); }
    .data-row { display: flex; justify-content: space-between; padding: 6px 15px; border-bottom: 1px solid rgba(128, 128, 128, 0.1); }
    .data-label { color: #bbb !important; font-size: 13px; font-weight: 500; }
    .data-value { color: #fff !important; font-weight: bold; font-family: 'Courier New', monospace; }
    .vol-low { color: #ff4b4b !important; font-weight: bold; }
    .vol-high { color: #00ff00 !important; font-weight: bold; }
    .target-box { background-color: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; margin-top: 10px; border: 1px dashed #555; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_tv_connection():
    return TvDatafeed()

def get_p(attr, default):
    return getattr(p, attr, default)

st.title("🛡️ BIST Profesyonel Karar Destek")

# Üst Strateji Özeti (Küçük ve Şık)
expander = st.expander("📋 Aktif Strateji Parametrelerini Gör", expanded=False)
with expander:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Zaman Dilimi", get_p('ZAMAN_DILIMI','4h'))
    c2.metric("EMA Hızlı/Yavaş", f"{get_p('EMA_HIZLI',20)} / {get_p('EMA_YAVAS',50)}")
    c3.metric("RSI Eşik", get_p('RSI_SINIR',50))
    c4.metric("Kar/Zarar Oranı", f"%{get_p('KAR_AL_ORAN',25)} / %{get_p('ZARAR_KES_ORAN',5)}")

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

                    # --- KARAR VE RENK MANTIĞI ---
                    has_position = False
                    if ema_h_v > ema_y_v and rsi_v > get_p('RSI_SINIR', 50):
                        decision, bg, has_position = "🚀 AL", "#1b5e20", True
                    elif price > (ema_h_v * 1.01) and ema_h_v > ema_y_v:
                        decision, bg, has_position = "💎 TUT", "#0d47a1", True
                    elif ema_h_v < ema_y_v:
                        decision, bg, has_position = "⚠️ SAT / ÇIK", "#b71c1c", True
                    else:
                        decision, bg, has_position = "⌛ BEKLE", "#444", False

                    with cols[idx % 3]:
                        with st.container(border=True):
                            # Karar Başlığı
                            st.markdown(f'<div class="decision-box" style="background-color:{bg}; color:white;">{h}: {decision}</div>', unsafe_allow_html=True)
                            
                            # Teknik Veriler
                            st.markdown(f"""
                                <div class="data-row"><span class="data-label">Fiyat:</span><span class="data-value">{price:.2f} TL</span></div>
                                <div class="data-row"><span class="data-label">EMA {get_p('EMA_HIZLI',20)}:</span><span class="data-value">{ema_h_v:.2f}</span></div>
                                <div class="data-row"><span class="data-label">EMA {get_p('EMA_YAVAS',50)}:</span><span class="data-value">{ema_y_v:.2f}</span></div>
                                <div class="data-row"><span class="data-label">RSI:</span><span class="data-value">{rsi_v:.1f}</span></div>
                            """, unsafe_allow_html=True)
                            
                            # Hacim Bilgisi (Kıyaslamalı ve Renkli)
                            vol_status = "vol-high" if curr_v > v_ma_v else "vol-low"
                            st.markdown(f"""
                                <div class="data-row" style="border:none;">
                                    <span class="data-label">Hacim (Güncel/Ort):</span>
                                    <span class="data-value {vol_status}">{curr_v:,.0f} / {v_ma_v:,.0f}</span>
                                </div>
                            """, unsafe_allow_html=True)

                            # --- ŞARTLI HEDEF GÖSTERİMİ ---
                            if has_position:
                                ka_fiyat = price * (1 + get_p('KAR_AL_ORAN', 25) / 100)
                                zk_fiyat = price * (1 - get_p('ZARAR_KES_ORAN', 5) / 100)
                                st.markdown(f"""
                                    <div class="target-box">
                                        <p style="margin:0; font-size:13px; color:#aaa; text-align:center;">🎯 Kar Al: <b style="color:#00ff00;">{ka_fiyat:.2f}</b></p>
                                        <p style="margin:0; font-size:13px; color:#aaa; text-align:center;">🛡️ Stop: <b style="color:#ff4b4b;">{zk_fiyat:.2f}</b></p>
                                    </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown('<div style="height:62px; display:flex; align-items:center; justify-content:center; color:#666; font-style:italic; font-size:12px;">Pozisyon bekleniyor...</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"{h} Hatası")
                
    time.sleep(get_p('GUNCELLEME_SANIYESI', 60))
    st.rerun()