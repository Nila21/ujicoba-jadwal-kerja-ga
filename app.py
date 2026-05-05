import streamlit as st
import pandas as pd
import random
from io import BytesIO

# --- LOGIKA PENYEIMBANG BEBAN (WORKLOAD BALANCER) ---

def buat_jadwal_adil(pj_toko, staf_list):
    semua = pj_toko + staf_list
    # 1. Kunci Libur tetap seperti awal (Hard Constraint)
    hari_kerja = [d for d in range(1, 31) if d % 7 != 0]
    random.shuffle(hari_kerja)
    jadwal_libur = {k: [] for k in semua}
    for i, tgl in enumerate(hari_kerja[:len(semua)*3]):
        jadwal_libur[semua[i % len(semua)]].append(tgl)

    hasil = []
    stats = {k: {'Pagi': 0, 'Siang': 0, 'Break': 0, 'Libur': 0} for k in semua}
    shift_kemarin = {k: None for k in semua}

    for hari in range(1, 31):
        if hari % 7 == 0: # Hari Minggu
            hasil.append({"Hari": hari, "Pagi": "Semua Masuk", "Siang": "-", "Break": "-", "Libur": "Minggu"})
            continue

        libur_hari_ini = [k for k, tgl in jadwal_libur.items() if hari in tgl]
        aktif = [k for k in semua if k not in libur_hari_ini]
        
        # --- INTI KEADILAN: Sortir berdasarkan jumlah Break tersedikit ---
        aktif.sort(key=lambda x: stats[x]['Break']) 
        
        pagi, siang, brk = [], [], []
        
        # Prioritaskan mengisi slot Break dulu dengan orang yang paling jarang istirahat
        # asalkan tidak melanggar aturan "Siang -> Break"
        kandidat_break = [k for k in aktif if shift_kemarin[k] not in ["Siang", "Break"]]
        
        # Ambil 2 orang untuk Break (sesuai urutan beban tersedikit)
        brk = kandidat_break[:2]
        for k in brk: stats[k]['Break'] += 1
        
        # Sisanya masukkan ke Pagi dan Siang
        sisa = [k for k in aktif if k not in brk]
        random.shuffle(sisa) # Acak sisa agar Pagi/Siang tetap bervariasi
        
        pagi = sisa[:3]
        for k in pagi: stats[k]['Pagi'] += 1
        
        siang = sisa[3:]
        for k in siang: stats[k]['Siang'] += 1

        # Update riwayat untuk besok
        for k in semua:
            if k in pagi: shift_kemarin[k] = "Pagi"
            elif k in siang: shift_kemarin[k] = "Siang"
            elif k in brk: shift_kemarin[k] = "Break"
            else: 
                shift_kemarin[k] = "Libur"
                if k in libur_hari_ini: stats[k]['Libur'] += 1

        hasil.append({"Hari": hari, "Pagi": ", ".join(pagi), "Siang": ", ".join(siang), "Break": ", ".join(brk), "Libur": ", ".join(libur_hari_ini)})
    
    return hasil, stats

# --- INTERFACE ---
st.title("🗓️ Generator Jadwal Anti-Timpang")
# (Gunakan input text_area seperti sebelumnya untuk PJ dan Staf)
# ... [Bagian input sama dengan kode sebelumnya] ...

if st.button("🚀 Susun Jadwal Adil"):
    pj_list = [x.strip() for x in input_pj.split(",") if x.strip()]
    staf_list = [x.strip() for x in input_staf.split(",") if x.strip()]
    
    jadwal, statistik = buat_jadwal_adil(pj_list, staf_list)
    
    # Tampilkan Tabel Jadwal
    st.table(pd.DataFrame(jadwal))
    
    # Tampilkan Statistik Keadilan
    df_stats = pd.DataFrame(statistik).T.reset_index().rename(columns={'index': 'Nama'})
    
    # Hitung Standar Deviasi untuk membuktikan keadilan
    std_break = df_stats['Break'].std()
    st.subheader(f"📊 Analisis Keadilan (Standar Deviasi: {std_break:.2f})")
    
    if std_break < 1.5:
        st.success("✅ Jadwal Sangat Adil: Beban kerja terdistribusi merata.")
    else:
        st.warning("⚠️ Perhatian: Ada sedikit ketimpangan beban kerja.")
        
    st.dataframe(df_stats)
