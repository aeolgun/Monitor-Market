import streamlit as st
import pandas as pd
import pandas_ta as ta
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime
import os
import parameters as p

st.set_page_config(page_title="BIST Pro Terminal", layout="wide")

# CSS: Parlak Renkler ve Okunabilir Siyah Yazılar
st.markdown("""
    <style>
    .stContainer { border-radius: 15px; background-color: #f8f9fa; border: 1px solid #ddd; }
    .metric-header { padding: 15px; border-radius: 12px 12px 0 0; text-align: center; margin-bottom: 10px; }
    .metric-header h3, .metric-header h4, .metric-header small { color: white !important; margin: 0; }
    .data-row { display: flex; justify-content: space-between; padding: 6px 15px; border-bottom: 1px solid #eee; }
    .data-label { color: #444 !important; font-weight: bold; font-size: 13px; }
    .data-value { color: #000 !important; font-weight: 800; font-family: 'Courier New', monospace; font-size: 14px; }
    .stMarkdown p { color: #000 !important; } /* Genel metin siyah */
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_tv_connection():
    return TvDatafeed()

def get_p(attr, default):
    return getattr(p, attr, default)

st.title("🚀 BIST Teknik Analiz Paneli")
tv = get_tv_connection()
placeholder = st.empty()

while True:
    # Parametreleri Döngü Başında Al
    Z_DILIMI = get_p('ZAMAN_DILIMI', '4h')
    EMA_H_L = get_p('EMA_HIZLI', 20)
    EMA_Y_L = get_p('EMA_YAVAS', 50)
    RSI_L = get_p('RSI_PERIYOT', 14)
    HACIM_L = get_p('HACIM_MA_PERIYOT', 20)
    
    interval_map = {'1h': Interval.in_1_hour, '4h': Interval.in_4_hour, '1d': Interval.in_daily}
    
    file_path = os.path.join(os.path.dirname(__file__), "inputs.txt")
    hisseler = ["THYAO", "ASELS"] # Default
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            hisseler = [line.strip().upper().replace(".IS", "") for line in f.readlines() if line.strip()]

    with placeholder.container():
        cols = st.columns(3)
        for idx, h in enumerate(hisseler):
            try:
                # Daha fazla bar çekelim (n_bars=200) ki indikatörler hesaplanabilsin
                df = tv.get_hist(symbol=h, exchange='BIST', interval=interval_map.get(Z_DILIMI), n_bars=200)
                
                if df is not None and not df.empty:
                    df.columns = [x.lower() for x in df.columns]
                    
                    # --- HESAPLAMA BLOĞU ---
                    price = df['close'].iloc[-1]
                    rsi_series = ta.rsi(df['close'], length=RSI_L)
                    ema_h_series = ta.ema(df['close'], length=EMA_H_L)
                    ema_y_series = ta.ema(df['close'], length=EMA_Y_L)
                    v_ma_series = ta.sma(df['volume'], length=HACIM_L)

                    # Veri kontrolü (Boşsa "Veri Yok" yazması için)
                    rsi_v = rsi_series.iloc[-1] if rsi_series is not None else 0
                    ema_h_v = ema_h_series.iloc[-1] if ema_h_series is not None else 0
                    ema_y_v = ema_y_series.iloc[-1] if ema_y_series is not None else 0
                    v_ma_v = v_ma_series.iloc[-1] if v_ma_series is not None else 0
                    curr_v = df['volume'].iloc[-1]

                    # Renk Kararı (Tam Doygun)
                    if ema_h_v > ema_y_v and rsi_v > get_p('RSI_SINIR', 50):
                        bg = "#00c853" # Parlak Yeşil
                        status = "GÜÇLÜ AL"
                    elif ema_h_v < ema_y_v:
                        bg = "#d50000" # Parlak Kırmızı
                        status = "SATIŞ RİSKİ"
                    else:
                        bg = "#ffd600" # Parlak Sarı
                        status = "NÖTR"

                    with cols[idx % 3]:
                        with st.container():
                            # Renkli Kısım
                            st.markdown(f"""
                                <div class="metric-header" style="background-color:{bg};">
                                    <h3>{h}</h3>
                                    <h4>{price:.2f} TL</h4>
                                    <small>{status}</small>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Detaylar
                            st.markdown(f"""
                                <div class="data-row"><span class="data-label">Zaman:</span><span class="data-value">{Z_DILIMI}</span></div>
                                <div class="data-row"><span class="data-label">EMA {EMA_H_L}:</span><span class="data-value">{ema_h_v:.2f}</span></div>
                                <div class="data-row"><span class="data-label">EMA {EMA_Y_L}:</span><span class="data-value">{ema_y_v:.2f}</span></div>
                                <div class="data-row"><span class="data-label">RSI {RSI_L}:</span><span class="data-value">{rsi_v:.1f}</span></div>
                                <div class="data-row"><span class="data-label">Hacim MA:</span><span class="data-value">{'✅ OK' if curr_v > v_ma_v else '❌ DÜŞÜK'}</span></div>
                            """, unsafe_allow_html=True)
                            
                            # Hedefler (Siyah Yazı)
                            st.divider()
                            st.write(f"**🎯 Kar Al:** {price*(1+get_p('KAR_AL_ORAN',25)/100):.2f}")
                            st.write(f"**🛡️ Stop:** {price*(1-get_p('ZARAR_KES_ORAN',5)/100):.2f}")
                else:
                    cols[idx % 3].error(f"{h} Veri Alınamadı")
            except Exception as e:
                cols[idx % 3].warning(f"{h} Hatası: {str(e)[:30]}")

    time.sleep(get_p('GUNCELLEME_SANIYESI', 60))
    st.rerun()