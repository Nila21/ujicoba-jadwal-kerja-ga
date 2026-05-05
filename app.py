import streamlit as st
import pandas as pd
import random
from io import BytesIO

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Generator Jadwal Shift", layout="wide")

st.title("🗓️ Generator Jadwal Shift Toko (Algoritma Genetika)")

# --- SIDEBAR: MANAJEMEN KARYAWAN ---
with st.sidebar:
    st.header("🏢 Konfigurasi Cabang")
    
    pj_input = st.text_area("Daftar PJ (Pisahkan dengan koma)", "Indah, Andri")
    staf_input = st.text_area("Daftar Staf (Pisahkan dengan koma)", "Tika, Firman, Elan, Nila, Novi, Alfi")
    
    list_pj = [x.strip() for x in pj_input.split(",") if x.strip()]
    list_staf = [x.strip() for x in staf_input.split(",") if x.strip()]
    semua_karyawan = list_pj + list_staf
    
    st.divider()
    st.subheader("📊 Info Karyawan Terdaftar")
    col1, col2 = st.columns(2)
    col1.metric("Total PJ", len(list_pj))
    col2.metric("Total Staf", len(list_staf))
    st.info(f"**Total Keseluruhan:** {len(semua_karyawan)} Orang")
    
    st.divider()
    st.header("⚙️ Parameter GA")
    generasi = st.slider("Jumlah Generasi (Iterasi)", 50, 1000, 200)
    populasi_size = 20

# --- LOGIKA FITNESS ---
def hitung_fitness(individu, list_pj, semua_karyawan):
    penalti = 0
    libur_count = {k: 0 for k in semua_karyawan}
    break_count = {k: 0 for k in semua_karyawan}
    total_k = len(semua_karyawan)
    
    for d in range(30):
        hari_ke = d + 1
        is_minggu = (hari_ke % 7 == 0)
        k_hari = individu[d]
        
        if is_minggu:
            aktif = k_hari
        else:
            libur = [k_hari[-1]]
            aktif = k_hari[:-1]
            for l in libur: libur_count[l] += 1
        
        n = len(aktif)
        porsi = n // 3
        pagi = aktif[0:porsi]
        siang = aktif[porsi:porsi*2]
        brk = aktif[porsi*2:]
        
        for b in brk: break_count[b] += 1

        # Cek PJ per shift
        for shift in [pagi, siang, brk]:
            if not any(p in list_pj for p in shift):
                penalti += 20 

        # Aturan Jeda & Istirahat
        if d < 29:
            k_besok = individu[d+1]
            n_besok = total_k if (d+2)%7==0 else total_k-1
            p_besok = n_besok // 3
            brk_besok = k_besok[p_besok*2:n_besok]
            for k in siang:
                if k in brk_besok: penalti += 150
            for k in brk:
                if k in brk_besok: penalti += 150

    # Penalti Keadilan Libur (Wajib 3)
    for k in libur_count:
        if libur_count[k] != 3:
            penalti += abs(libur_count[k] - 3) * 500

    # Penalti Keadilan Break (Standar deviasi/perbedaan jumlah)
    vals = list(break_count.values())
    perbedaan = max(vals) - min(vals)
    if perbedaan > 2:
        penalti += perbedaan * 100

    return 1 / (1 + penalti)

# --- EKSEKUSI ---
if st.button("🚀 Buat Jadwal & Cek Keadilan"):
    total_k = len(semua_karyawan)
    if total_k < 6:
        st.error("❌ Karyawan terlalu sedikit!")
    else:
        populasi = [[random.sample(semua_karyawan, total_k) for _ in range(30)] for _ in range(populasi_size)]
        bar = st.progress(0)
        
        for g in range(generasi):
            populasi = sorted(populasi, key=lambda x: hitung_fitness(x, list_pj, semua_karyawan), reverse=True)
            bar.progress((g + 1) / generasi)
        
        best = populasi[0]
        
        # Penyiapan Data
        hasil = []
        stats = {k: {"Pagi": 0, "Siang": 0, "Break": 0, "Libur": 0} for k in semua_karyawan}
        
        for d in range(30):
            hari_ke = d + 1
            is_minggu = (hari_ke % 7 == 0)
            k = best[d]
            n_aktif = total_k if is_minggu else total_k - 1
            p = n_aktif // 3
            
            pagi, siang, brk = k[0:p], k[p:p*2], k[p*2:n_aktif]
            libur = [k[-1]] if not is_minggu else []
            
            for pers in pagi: stats[pers]["Pagi"] += 1
            for pers in siang: stats[pers]["Siang"] += 1
            for pers in brk: stats[pers]["Break"] += 1
            for pers in libur: stats[pers]["Libur"] += 1
            
            hasil.append({
                "Tanggal": f"Hari {hari_ke}",
                "Pagi": ", ".join(pagi),
                "Siang": ", ".join(siang),
                "Break": ", ".join(brk),
                "Libur": ", ".join(libur) if libur else "-"
            })

        # --- TAMPILAN DASHBOARD ---
        st.subheader("✅ Hasil Penjadwalan")
        st.dataframe(pd.DataFrame(hasil), use_container_width=True)

        st.divider()
        
        # --- ANALISIS KEADILAN ---
        st.subheader("📊 Analisis Keadilan Shift")
        df_stats = pd.DataFrame(stats).T.reset_index().rename(columns={'index': 'Nama Karyawan'})
        
        col_a, col_b = st.columns([2, 1])
        
        with col_a:
            st.write("**Tabel Akumulasi Shift (30 Hari):**")
            st.table(df_stats)
        
        with col_b:
            st.write("**Status Validasi:**")
            # Cek Libur
            salah_libur = df_stats[df_stats['Libur'] != 3]
            if salah_libur.empty:
                st.success("✅ Semua karyawan libur tepat 3x.")
            else:
                st.warning(f"⚠️ Ada {len(salah_libur)} orang jatah liburnya belum tepat.")
            
            # Cek Break
            min_brk = df_stats['Break'].min()
            max_brk = df_stats['Break'].max()
            if (max_brk - min_brk) <= 2:
                st.success(f"✅ Pembagian Break adil (Rentang: {min_brk}-{max_brk}).")
            else:
                st.error(f"❌ Pembagian Break kurang adil (Rentang: {min_brk}-{max_brk}). Coba naikkan Generasi.")

        # --- DOWNLOAD ---
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame(hasil).to_excel(writer, index=False, sheet_name='Jadwal')
            df_stats.to_excel(writer, index=False, sheet_name='Statistik_Keadilan')
        
        st.download_button(label="📥 Download Excel", data=output.getvalue(), file_name="Jadwal_Shift.xlsx")
