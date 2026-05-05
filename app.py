import streamlit as st
import pandas as pd
import random
from io import BytesIO

# --- FUNGSI LOGIKA ---

def generate_jadwal_lengkap(pj_toko, staf_list):
    semua_karyawan = pj_toko + staf_list
    hari_kerja = [d for d in range(1, 31) if d % 7 != 0]
    random.shuffle(hari_kerja)
    
    # Kunci Libur (3 hari/orang)
    jadwal_libur = {k: [] for k in semua_karyawan}
    slot_libur = hari_kerja[:len(semua_karyawan) * 3]
    for i, tgl in enumerate(slot_libur):
        karyawan = semua_karyawan[i % len(semua_karyawan)]
        jadwal_libur[karyawan].append(tgl)

    hasil = []
    stats = {k: {'Break': 0, 'Libur': 0} for k in semua_karyawan}
    shift_kemarin = {k: None for k in semua_karyawan}

    for hari in range(1, 31):
        is_minggu = (hari % 7 == 0)
        if is_minggu:
            for k in semua_karyawan: stats[k]['Libur'] += 0 # Opsional: catat minggu
            hasil.append({"Hari": hari, "Pagi": "Semua Masuk", "Siang": "-", "Break": "-", "Libur": "Minggu"})
            continue

        libur_hari_ini = [k for k, tgl in jadwal_libur.items() if hari in tgl]
        aktif = [k for k in semua_karyawan if k not in libur_hari_ini]
        random.shuffle(aktif)

        pagi, siang, brk = [], [], []
        for k in aktif:
            # Aturan: Tidak boleh Break jika kemarin Siang/Break
            bisa_break = shift_kemarin[k] not in ["Siang", "Break"]
            
            if len(pagi) < 3:
                pagi.append(k); shift_kemarin[k] = "Pagi"
            elif len(siang) < 2:
                siang.append(k); shift_kemarin[k] = "Siang"
            elif bisa_break and len(brk) < 2:
                brk.append(k); shift_kemarin[k] = "Break"; stats[k]['Break'] += 1
            else:
                pagi.append(k); shift_kemarin[k] = "Pagi"

        for k in libur_hari_ini: 
            stats[k]['Libur'] += 1
            shift_kemarin[k] = "Libur"

        hasil.append({
            "Hari": hari,
            "Pagi": ", ".join(pagi),
            "Siang": ", ".join(siang),
            "Break": ", ".join(brk),
            "Libur": ", ".join(libur_hari_ini)
        })
    
    return hasil, stats

# --- TAMPILAN (STREAMLIT) ---

st.set_page_config(page_title="Penjadwalan Toko", layout="wide")
st.title("📑 Sistem Penyusunan Jadwal Cabang")

# Bagian 1: Manajemen Karyawan (Untuk Rotasi)
with st.expander("⚙️ Pengaturan Karyawan (Rotasi Cabang)", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        input_pj = st.text_area("PJ Toko (Pisahkan koma):", "Indah, Andri")
    with col2:
        input_staf = st.text_area("Staf (Pisahkan koma):", "Tika, Firman, Elan, Nila, Novi, Alfi")

pj_list = [x.strip() for x in input_pj.split(",") if x.strip()]
staf_list = [x.strip() for x in input_staf.split(",") if x.strip()]

if st.button("🚀 Susun Jadwal & Hitung Indikator"):
    jadwal, statistik = generate_jadwal_lengkap(pj_list, staf_list)
    
    # Bagian 2: Tabel Jadwal
    st.subheader("🗓️ Jadwal Operasional")
    df_jadwal = pd.DataFrame(jadwal)
    st.table(df_jadwal)

    # Bagian 3: Indikator Persyaratan (Sesuai Gambar 2)
    st.subheader("📊 Statistik & Indikator Persyaratan")
    data_stats = []
    for k, v in statistik.items():
        terpenuhi = "✅ Ya" if v['Libur'] >= 3 else "❌ Tidak"
        data_stats.append({
            "Nama Karyawan": k,
            "Total Break": v['Break'],
            "Total Libur": v['Libur'],
            "Syarat Terpenuhi?": terpenuhi
        })
    st.dataframe(pd.DataFrame(data_stats))

    # Fitur Download Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_jadwal.to_excel(writer, index=False, sheet_name='Jadwal')
        pd.DataFrame(data_stats).to_excel(writer, index=False, sheet_name='Statistik')
    
    st.download_button(
        label="📥 Download Jadwal (Excel)",
        data=output.getvalue(),
        file_name="jadwal_toko_cabang.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
