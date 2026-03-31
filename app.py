import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime
import parameters as p  # parameters.py dosyasından verileri çeker

# Sayfa Yapılandırması
st.set_page_config(page_title="Monitor-Market", layout="wide")

# 1. DOSYA OKUMA SİSTEMİ (inputs.txt)
def liste_yukle():
    try:
        with open("inputs.txt", "r", encoding="utf-8") as f:
            # Satırları temizle, boş satırları ve hatalı karakterleri ele
            hisseler = [line.strip().upper() for line in f.readlines() if line.strip()]
            return hisseler
    except Exception as e:
        st.error(f"Hisse listesi (inputs.txt) okunamadı: {e}")
        return ["THYAO.IS"]

# 2. VERİ ÇEKME VE HESAPLAMA SİSTEMİ
def get_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # EMA50 hesaplanabilmesi için en az 50 mumluk veri lazım, biz 60 günlük çekiyoruz
        df = ticker.history(period="60d", interval="1h")
        
        if df.empty or len(df) < p.EMA_YAVAS:
            return None, None

        # İndikatörleri parametre dosyasındaki değerlere göre hesapla
        df['ema_h'] = ta.ema(df['Close'], length=p.EMA_HIZLI)
        df['ema_y'] = ta.ema(df['Close'], length=p.EMA_YAVAS)
        df['rsi'] = ta.rsi(df['Close'], length=p.RSI_PERIYOT)
        df['v_ma'] = ta.sma(df['Volume'], length=p.HACIM_MA_PERIYOT)
        
        return df.iloc[-1], df['Close'].iloc[-1]
    except:
        return None, None

# ARAYÜZ BAŞLIĞI
st.title("📈 Monitor-Market: Canlı Takip")

# Yan Menü (Sidebar) Bilgilendirme
hisseler = liste_yukle()
st.sidebar.header("📋 Takip Listesi")
st.sidebar.write(f"Toplam {len(hisseler)} hisse tanımlı.")
st.sidebar.code("\n".join(hisseler)) # Listeyi yan tarafta göster

placeholder = st.empty()

# 3. ANA DÖNGÜ (AKAN VERİ)
while True:
    with placeholder.container():
        # Ekranı 2 sütuna bölerek daha fazla hisse sığdırıyoruz
        cols = st.columns(2)
        idx = 0
        
        found_count = 0
        for h in hisseler:
            data, price = get_data(h)
            
            if data is not None:
                found_count += 1
                # Sinyal Mantığı (Parametrik)
                trend_yukari = data['ema_h'] > data['ema_y']
                rsi_guclu = data['rsi'] > p.RSI_SINIR
                hacim_onay = data['Volume'] > data['v_ma']
                
                # Durum Belirleme
                if trend_yukari and rsi_guclu and hacim_onay:
                    durum, renk = "🟢 GÜÇLÜ AL", "green"
                elif not trend_yukari or data['rsi'] > p.RSI_ASIRI_ALIM:
                    durum, renk = "🔴 SAT / RİSK", "red"
                else:
                    durum, renk = "🟡 BEKLE", "gray"

                # Hisseleri sütunlara dağıt
                with cols[idx % 2]:
                    with st.expander(f"**{h.replace('.IS', '')}** — {price:.2f} TL", expanded=True):
                        st.write(f"**Sinyal:** {durum}")
                        st.write(f"RSI: `{round(data['rsi'], 1)}` | Trend: `{'Yukarı' if trend_yukari else 'Aşağı'}`")
                idx += 1
        
        if found_count == 0:
            st.warning("Hiçbir hisse için veri çekilemedi. Lütfen 'inputs.txt' dosyasındaki sembolleri (Örn: THYAO.IS) kontrol edin.")

        st.divider()
        st.write(f"⏱️ **Son Güncelleme:** {datetime.now().strftime('%H:%M:%S')} | **Periyot:** {p.GUNCELLEME_SANIYESI}s")
        
        time.sleep(p.GUNCELLEME_SANIYESI)
        st.rerun()