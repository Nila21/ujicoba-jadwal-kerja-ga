import streamlit as st
import pandas as pd
import random
from io import BytesIO

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Generator Jadwal Shift", layout="wide")

st.title("🗓️ Generator Jadwal Shift Toko (Algoritma Genetika)")
st.markdown("""
Aplikasi ini mengatur jadwal 30 hari secara otomatis dengan aturan:
- **Minggu**: Wajib masuk semua.
- **Hari Kerja**: Maksimal 1 orang libur.
- **Shift**: Pagi, Siang, Break (Minimal 1 PJ per shift).
- **Aturan Istirahat**: Siang hari ini tidak boleh Break besok. Break tidak boleh 2 hari beruntun.
""")

# --- SIDEBAR: MANAJEMEN KARYAWAN ---
with st.sidebar:
    st.header("Konfigurasi Cabang")
    
    pj_input = st.text_area("Daftar PJ (Pisahkan dengan koma)", "Indah, Andri")
    staf_input = st.text_area("Daftar Staf (Pisahkan dengan koma)", "Tika, Firman, Elan, Nila, Novi, Alfi")
    
    list_pj = [x.strip() for x in pj_input.split(",") if x.strip()]
    list_staf = [x.strip() for x in staf_input.split(",") if x.strip()]
    semua_karyawan = list_pj + list_staf
    total_k = len(semua_karyawan)

    st.divider()
    st.header("Parameter GA")
    generasi = st.slider("Jumlah Generasi", 50, 500, 100)
    populasi_size = 20

# --- LOGIKA ALGORITMA GENETIKA ---
def hitung_fitness(individu, list_pj, semua_karyawan):
    penalti = 0
    libur_count = {k: 0 for k in semua_karyawan}
    
    for d in range(30):
        hari_ke = d + 1
        is_minggu = (hari_ke % 7 == 0)
        k_hari = individu[d]
        
        # 1. Aturan Libur & Aktif
        if is_minggu:
            aktif = k_hari
        else:
            libur = [k_hari[-1]]
            aktif = k_hari[:-1]
            for l in libur: libur_count[l] += 1
        
        # 2. Pembagian Slot (Dinamis: Pagi, Siang, Break)
        # Menjamin Pagi + Break punya orang lebih banyak di jam awal
        n = len(aktif)
        porsi = n // 3
        pagi = aktif[0:porsi]
        siang = aktif[porsi:porsi*2]
        brk = aktif[porsi*2:]

        # 3. Cek Keberadaan PJ di setiap shift
        for shift in [pagi, siang, brk]:
            if not any(p in list_pj for p in shift):
                penalti += 10 # Penalti jika shift hanya staf (staf jadi PJS)

        # 4. Aturan Jeda Istirahat (Siang -> Besok Break tidak boleh)
        if d < 29:
            k_besok = individu[d+1]
            n_besok = total_k if (d+2)%7==0 else total_k-1
            p_besok = n_besok // 3
            brk_besok = k_besok[p_besok*2:n_besok]
            
            for k in siang:
                if k in brk_besok: penalti += 100
            
            # Break tidak boleh 2 hari berturut-turut
            for k in brk:
                if k in brk_besok: penalti += 100

    # 5. Harus libur tepat 3 kali sebulan
    for k in libur_count:
        if libur_count[k] != 3:
            penalti += abs(libur_count[k] - 3) * 200

    return 1 / (1 + penalti)

# --- TOMBOL GENERATE ---
if st.button("🚀 Buat Jadwal"):
    if total_k < 6:
        st.error("Karyawan terlalu sedikit!")
    else:
        # Inisialisasi
        populasi = [[random.sample(semua_karyawan, total_k) for _ in range(30)] for _ in range(populasi_size)]
        
        bar = st.progress(0)
        for g in range(generasi):
            populasi = sorted(populasi, key=lambda x: hitung_fitness(x, list_pj, semua_karyawan), reverse=True)
            bar.progress((g + 1) / generasi)
        
        best = populasi[0]
        
        # --- PROSES DATA UNTUK TAMPILAN & EXCEL ---
        hasil = []
        for d in range(30):
            hari_ke = d + 1
            is_minggu = (hari_ke % 7 == 0)
            k = best[d]
            
            n_aktif = total_k if is_minggu else total_k - 1
            p = n_aktif // 3
            
            pagi = k[0:p]
            siang = k[p:p*2]
            brk = k[p*2:n_aktif]
            libur = [k[-1]] if not is_minggu else ["-"]
            
            hasil.append({
                "Hari": f"Hari {hari_ke}",
                "Keterangan": "Minggu" if is_minggu else "Kerja",
                "Shift Pagi": ", ".join(pagi),
                "Shift Siang": ", ".join(siang),
                "Shift Break (Pagi-Sore)": ", ".join(brk),
                "Libur": ", ".join(libur)
            })
            
        df = pd.DataFrame(hasil)
        st.success("Jadwal Berhasil Dioptimalkan!")
        st.dataframe(df, use_container_width=True)

        # --- FITUR DOWNLOAD EXCEL ---
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Jadwal_Shift')
            
            # Styling Excel
            workbook = writer.book
            worksheet = writer.sheets['Jadwal_Shift']
            header_fmt = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC', 'border': 1})
            
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_fmt)
                worksheet.set_column(col_num, col_num, 20)
        
        st.download_button(
            label="📥 Download Jadwal (.xlsx)",
            data=output.getvalue(),
            file_name="Jadwal_Shift_Toko.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
