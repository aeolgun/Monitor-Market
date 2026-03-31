import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime
import os
import parameters as p

# Sayfa Genişliği Ayarı
st.set_page_config(page_title="Monitor-Market", layout="wide")

# 1. DOSYA OKUMA FONKSİYONU (Hatalara Karşı Güçlendirilmiş)
def liste_yukle():
    # Dosyanın tam yolunu bul (Streamlit Cloud dosya sistemi uyumu için)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "inputs.txt")
    
    try:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                # Satırları temizle, boş satırları atla ve büyük harfe çevir
                hisseler = [line.strip().upper() for line in f.readlines() if line.strip()]
                return hisseler
        else:
            st.sidebar.error("⚠️ inputs.txt dosyası bulunamadı!")
            return ["THYAO.IS"]
    except Exception as e:
        st.sidebar.error(f"❌ Liste okuma hatası: {e}")
        return ["THYAO.IS"]

# 2. VERİ ÇEKME VE HESAPLAMA FONKSİYONU
def get_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # EMA_YAVAS periyodundan daha fazla veri çekilmeli (En az 60 gün idealdir)
        df = ticker.history(period="60d", interval="1h")
        
        if df.empty or len(df) < p.EMA_YAVAS:
            return None, None

        # Parametre dosyasındaki değerleri kullanarak hesaplama yap
        df['ema_h'] = ta.ema(df['Close'], length=p.EMA_HIZLI)
        df['ema_y'] = ta.ema(df['Close'], length=p.EMA_YAVAS)
        df['rsi'] = ta.rsi(df['Close'], length=p.RSI_PERIYOT)
        df['v_ma'] = ta.sma(df['Volume'], length=p.HACIM_MA_PERIYOT)
        
        return df.iloc[-1], df['Close'].iloc[-1]
    except Exception:
        return None, None

# --- ARAYÜZ BAŞLANGICI ---
st.title("📈 Monitor-Market: BIST Teknik Analiz")
st.caption(f"Strateji: EMA {p.EMA_HIZLI}/{p.EMA_YAVAS} | RSI {p.RSI_PERIYOT} | Veriler 15 dk gecikmelidir.")

# Yan Menüde Takip Listesini Göster
hisseler = liste_yukle()
st.sidebar.header("📋 Takip Edilenler")
st.sidebar.write(f"Toplam: {len(hisseler)} Hisse")
st.sidebar.info("\n".join(hisseler))

# Ana Ekran Alanı
placeholder = st.empty()

# 3. ANA DÖNGÜ
while True:
    with placeholder.container():
        # Görünümü 2 sütuna böl
        cols = st.columns(2)
        count = 0
        success_count = 0
        
        for h in hisseler:
            data, price = get_data(h)
            
            if data is not None:
                success_count += 1
                # Sinyal Mantığı
                trend_yukari = data['ema_h'] > data['ema_y']
                rsi_guclu = data['rsi'] > p.RSI_SINIR
                hacim_onay = data['Volume'] > data['v_ma']
                
                # Durum ve Renk Belirleme
                if trend_yukari and rsi_guclu and hacim_onay:
                    durum, renk = "🟢 GÜÇLÜ AL", "green"
                elif not trend_yukari or data['rsi'] > p.RSI_ASIRI_ALIM:
                    durum, renk = "🔴 SAT / RİSK", "red"
                else:
                    durum, renk = "🟡 BEKLE / NÖTR", "gray"

                # Sütunlara kartları yerleştir
                with cols[count % 2]:
                    with st.expander(f"**{h.replace('.IS', '')}** — {price:.2f} TL", expanded=True):
                        st.markdown(f"**Durum:** {durum}")
                        st.write(f"RSI: `{round(data['rsi'], 1)}` | Trend: `{'Yukarı' if trend_yukari else 'Aşağı'}`")
                count += 1
        
        if success_count == 0:
            st.warning("⚠️ Seçili hisseler için veri alınamadı. Lütfen 'inputs.txt' içeriğini kontrol edin.")

        st.divider()
        st.write(f"⏱️ **Son Güncelleme:** {datetime.now().strftime('%H:%M:%S')} | **Yenileme:** {p.GUNCELLEME_SANIYESI}s")
        
        # Sayfayı beklet ve yeniden çalıştır
        time.sleep(p.GUNCELLEME_SANIYESI)
        st.rerun()