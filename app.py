import streamlit as st
import pandas as pd
import pandas_ta as ta
from tvDatafeed import TvDatafeed, Interval
import time
from datetime import datetime
import os
import parameters as p

st.set_page_config(page_title="BIST Pro Terminal", layout="wide")

# CSS: Karanlık/Aydınlık Mod Uyumlu Dinamik Tasarım
st.markdown("""
    <style>
    /* Kartın genel gövdesi */
    .stContainer { 
        border-radius: 15px; 
        background-color: rgba(255, 255, 255, 0.05); 
        border: 1px solid rgba(128, 128, 128, 0.3);
        padding: 0px !important;
        margin-bottom: 20px;
    }
    /* Renkli Başlık Alanı */
    .metric-header { 
        padding: 15px; 
        border-radius: 12px 12px 0 0; 
        text-align: center; 
    }
    .metric-header h3, .metric-header h4 { 
        color: white !important; 
        margin: 0; 
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    /* Veri Satırları - OKUNABİLİR FONT */
    .data-row { 
        display: flex; 
        justify-content: space-between; 
        padding: 8px 15px; 
        border-bottom: 1px solid rgba(128, 128, 128, 0.2); 
    }
    .data-label { 
        color: #999 !important; /* Gri etiketler */
        font-weight: bold; 
        font-size: 13px; 
    }
    .data-value { 
        color: #00ff00 !important; /* Fosforlu Yeşil Değerler (Karanlıkta parlar) */
        font-weight: 800; 
        font-family: 'Courier New', monospace; 
        font-size: 15px; 
    }
    /* Kritik Uyarı Renkleri */
    .val-red { color: #ff4b4b !important; }
    .val-white { color: #ffffff !important; }
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
    # Parametreleri Yükle
    Z_DILIMI = get_p('ZAMAN_DILIMI', '4h')
    EMA_H_L = get_p('EMA_HIZLI', 20)
    EMA_Y_L = get_p('EMA_YAVAS', 50)
    RSI_L = get_p('RSI_PERIYOT', 14)
    HACIM_L = get_p('HACIM_MA_PERIYOT', 20)
    
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
                    rsi_v = ta.rsi(df['close'], length=RSI_L).iloc[-1]
                    ema_h_v = ta.ema(df['close'], length=EMA_H_L).iloc[-1]
                    ema_y_v = ta.ema(df['close'], length=EMA_Y_L).iloc[-1]
                    v_ma_v = ta.sma(df['volume'], length=HACIM_L).iloc[-1]
                    curr_v = df['volume'].iloc[-1]

                    # Dinamik Renk Belirleme
                    if ema_h_v > ema_y_v and rsi_v > get_p('RSI_SINIR', 50):
                        bg, status = "#1b5e20", "GÜÇLÜ AL" # Koyu Yeşil
                    elif ema_h_v < ema_y_v:
                        bg, status = "#b71c1c", "SATIŞ RİSKİ" # Koyu Kırmızı
                    else:
                        bg, status = "#f57f17", "NÖTR" # Koyu Turuncu

                    with cols[idx % 3]:
                        with st.container():
                            st.markdown(f"""
                                <div class="metric-header" style="background-color:{bg};">
                                    <h3>{h}</h3>
                                    <h4>{price:.2f} TL</h4>
                                    <small>{status}</small>
                                </div>
                                <div class="data-row"><span class="data-label">Zaman:</span><span class="data-value" style="color:white !important;">{Z_DILIMI}</span></div>
                                <div class="data-row"><span class="data-label">EMA {EMA_H_L}:</span><span class="data-value">{ema_h_v:.2f}</span></div>
                                <div class="data-row"><span class="data-label">EMA {EMA_Y_L}:</span><span class="data-value">{ema_y_v:.2f}</span></div>
                                <div class="data-row"><span class="data-label">RSI {RSI_L}:</span><span class="data-value">{rsi_v:.1f}</span></div>
                                <div class="data-row"><span class="data-label">Hacim:</span><span class="data-value">{'✅ GÜÇLÜ' if curr_v > v_ma_v else '❌ DÜŞÜK'}</span></div>
                            """, unsafe_allow_html=True)
                            
                            # Hedefler
                            st.divider()
                            st.info(f"🎯 Kar Al: **{price*(1+get_p('KAR_AL_ORAN',25)/100):.2f}**")
                            st.warning(f"🛡️ Stop: **{price*(1-get_p('ZARAR_KES_ORAN',5)/100):.2f}**")
                else:
                    cols[idx % 3].error(f"{h} Veri Yok")
            except: continue

        st.caption(f"⏱️ Son Güncelleme: {datetime.now().strftime('%H:%M:%S')}")
    
    time.sleep(get_p('GUNCELLEME_SANIYESI', 60))
    st.rerun()