import streamlit as st
import numpy as np
import pandas as pd
import random
import time
from io import BytesIO

# ==========================================
# 1. KONFIGURASI HALAMAN & UI
# ==========================================
st.set_page_config(page_title="Sistem Optimasi Jadwal WSS", layout="wide")

st.sidebar.title("👥 Manajemen Karyawan")
st.sidebar.write("Silakan ubah nama karyawan jika diperlukan:")

# Input Nama Karyawan Dinamis di Sidebar
pj1 = st.sidebar.text_input("Nama PJ 1", value="Indah")
pj2 = st.sidebar.text_input("Nama PJ 2", value="Andri")
stf1 = st.sidebar.text_input("Nama Staf 1", value="Tika")
stf2 = st.sidebar.text_input("Nama Staf 2", value="Firman")
stf3 = st.sidebar.text_input("Nama Staf 3", value="Elan")
stf4 = st.sidebar.text_input("Nama Staf 4", value="Nila")
stf5 = st.sidebar.text_input("Nama Staf 5", value="Alfi")
stf6 = st.sidebar.text_input("Nama Staf 6", value="Novi")

KARYAWAN = [
    {"nama": pj1, "role": "PJ"},
    {"nama": pj2, "role": "PJ"},
    {"nama": stf1, "role": "Staf"},
    {"nama": stf2, "role": "Staf"},
    {"nama": stf3, "role": "Staf"},
    {"nama": stf4, "role": "Staf"},
    {"nama": stf5, "role": "Staf"},
    {"nama": stf6, "role": "Staf"}
]

NUM_KARYAWAN = len(KARYAWAN)
NUM_HARI = 30  # Jadwal 1 Bulan

# Kode: 0=Libur, 1=Pagi, 2=Siang, 3=Break
KODE_SHIFT = [0, 1, 2, 3]
NAMA_SHIFT = {0: "Libur ❌", 1: "Pagi 🌅", 2: "Siang ☀️", 3: "Break 🔄"}

# ==========================================
# 2. FUNGSI FITNESS & PENALTI (Sesuai Skripsi)
# ==========================================
def hitung_fitness(jadwal):
    penalti = 0
    log_pelanggaran = []
    
    # Evaluasi Aturan Harian (Per Kolom)
    for h in range(NUM_HARI):
        hari_ke = h + 1
        is_minggu = (h % 7 == 6) # Asumsi hari ke-7, 14, 21, 28 adalah Minggu
        
        c_pagi = sum(1 for k in range(NUM_KARYAWAN) if jadwal[k][h] == 1)
        c_siang = sum(1 for k in range(NUM_KARYAWAN) if jadwal[k][h] == 2)
        c_break = sum(1 for k in range(NUM_KARYAWAN) if jadwal[k][h] == 3)
        c_libur = sum(1 for k in range(NUM_KARYAWAN) if jadwal[k][h] == 0)
        
        # [span_0](start_span)[span_1](start_span)P4: Minggu dilarang libur (Bobot 100) -[span_0](end_span)[span_1](end_span)
        if is_minggu and c_libur > 0:
            penalti += 100
            log_pelanggaran.append(f"H-{hari_ke} (Minggu): Dilarang ada yang libur! (+100)")
            
        # [span_2](start_span)[span_3](start_span)P4: Maksimal 1 libur di hari biasa (Bobot 100) -[span_2](end_span)[span_3](end_span)
        if not is_minggu and c_libur > 1:
            penalti += 100
            log_pelanggaran.append(f"H-{hari_ke}: Terlalu banyak yang libur ({c_libur} orang). Maksimal 1! (+100)")

        # [span_4](start_span)[span_5](start_span)P2: Minimal komposisi staf per shift (Bobot 100) -[span_4](end_span)[span_5](end_span)
        # Aturan operasional WSS: Normalnya Pagi(3), Siang(2/3), Break(2).
        if c_break < 2: 
            penalti += 100
            log_pelanggaran.append(f"H-{hari_ke}: Shift Break kekurangan personel (< 2 orang) (+100)")
        if c_siang < 2: 
            penalti += 100
            log_pelanggaran.append(f"H-{hari_ke}: Shift Siang kekurangan personel (< 2 orang) (+100)")
            
        # Jika ada 1 yang libur, shift pagi diizinkan 2 orang (1 PJ pengganti + 1 Staf)
        if c_libur == 1:
            if c_pagi < 2:
                penalti += 100
                log_pelanggaran.append(f"H-{hari_ke}: Shift Pagi kekurangan personel (< 2 orang saat ada libur) (+100)")
        else:
            if c_pagi < 3:
                penalti += 100
                log_pelanggaran.append(f"H-{hari_ke}: Shift Pagi kekurangan personel (< 3 orang normal) (+100)")
                
        # [span_6](start_span)P5: Tidak boleh ada 2 PJ dalam shift yang persis sama (Bobot 80) -[span_6](end_span)
        shift_pj1 = jadwal[0][h]
        shift_pj2 = jadwal[1][h]
        if shift_pj1 != 0 and shift_pj2 != 0 and shift_pj1 == shift_pj2:
            penalti += 80
            log_pelanggaran.append(f"H-{hari_ke}: Dua PJ berada di shift yang sama ({NAMA_SHIFT[shift_pj1]}) (+80)")

    # Evaluasi Aturan Per Karyawan (Per Baris)
    for k in range(NUM_KARYAWAN):
        nama = KARYAWAN[k]['nama']
        
        # [span_7](start_span)P4: Jatah Libur harus tepat 3 hari per bulan (Bobot 100) -[span_7](end_span)
        jumlah_libur_sebulan = sum(1 for h in range(NUM_HARI) if jadwal[k][h] == 0)
        if jumlah_libur_sebulan != 3:
            penalti += 100
            log_pelanggaran.append(f"{nama}: Jumlah libur tidak sama dengan 3 hari (dapat {jumlah_libur_sebulan} hari) (+100)")
            
        # Transisi Antar Hari
        for h in range(NUM_HARI - 1):
            hari_ini = jadwal[k][h]
            besok = jadwal[k][h+1]
            
            # [span_8](start_span)[span_9](start_span)P1: Tidak boleh Break berturut-turut (Bobot 50) -[span_8](end_span)[span_9](end_span)
            if hari_ini == 3 and besok == 3:
                penalti += 50
                log_pelanggaran.append(f"P1 - {nama}: Shift Break 2 hari berturut-turut (H-{h+1} & H-{h+2}) (+50)")
                
            # [span_10](start_span)[span_11](start_span)P6: Siang hari ini, besok tidak boleh Break (Bobot 50) -[span_10](end_span)[span_11](end_span)
            if hari_ini == 2 and besok == 3:
                penalti += 50
                log_pelanggaran.append(f"P6 - {nama}: Shift Siang lanjut Break (H-{h+1} & H-{h+2}) (+50)")

    fitness = 1 / (1 + penalti)
    return fitness, penalti, log_pelanggaran

# ==========================================
# 3. ALGORITMA GENETIKA CORE
# ==========================================
def buat_kromosom_cerdas():
    # Inisialisasi awal dibantu kecerdasan matematis agar cepat konvergen
    jadwal = np.ones((NUM_KARYAWAN, NUM_HARI), dtype=int)
    
    # Acak 3 hari libur per karyawan (tanpa hari minggu)
    hari_kerja_biasa = [d for d in range(NUM_HARI) if d % 7 != 6]
    random.shuffle(hari_kerja_biasa)
    
    # Bagikan jatah libur agar rata 1 orang per hari
    idx_libur = 0
    for k in range(NUM_KARYAWAN):
        for _ in range(3):
            if idx_libur < len(hari_kerja_biasa):
                jadwal[k][hari_kerja_biasa[idx_libur]] = 0
                idx_libur += 1
                
    # Isi sisanya dengan shift secara acak
    for k in range(NUM_KARYAWAN):
        for h in range(NUM_HARI):
            if jadwal[k][h] != 0:
                jadwal[k][h] = random.choice([1, 2, 3])
    return jadwal

def jalankan_ga(pop_size, max_gen):
    waktu_mulai = time.time()
    populasi = [buat_kromosom_cerdas() for _ in range(pop_size)]
    riwayat_fitness = []
    
    jadwal_terbaik = None
    fitness_terbaik = 0
    penalti_terbaik = 9999
    pelanggaran_terbaik = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for gen in range(max_gen):
        skor_populasi = [hitung_fitness(ind) for ind in populasi]
        
        for i, (fit, pen, pel) in enumerate(skor_populasi):
            if fit > fitness_terbaik:
                fitness_terbaik = fit
                penalti_terbaik = pen
                jadwal_terbaik = populasi[i]
                pelanggaran_terbaik = pel
                
        riwayat_fitness.append(fitness_terbaik)
        
        # Update UI loading
        progress_bar.progress((gen + 1) / max_gen)
        status_text.text(f"Sedang mengkalkulasi... Generasi {gen+1}/{max_gen} | Sisa Penalti: {penalti_terbaik}")
        
        if penalti_terbaik == 0:
            riwayat_fitness.extend([fitness_terbaik] * (max_gen - gen - 1))
            break
            
        # Seleksi, Crossover, Mutasi
        populasi_baru = []
        for _ in range(pop_size):
            k1, k2 = random.choice(populasi), random.choice(populasi)
            f1, _, _ = hitung_fitness(k1)
            f2, _, _ = hitung_fitness(k2)
            populasi_baru.append(np.copy(k1 if f1 > f2 else k2))
            
        for i in range(0, pop_size, 2):
            if i+1 < pop_size and random.random() < 0.8:
                titik = random.randint(1, NUM_HARI - 1)
                populasi_baru[i][:, titik:], populasi_baru[i+1][:, titik:] = \
                populasi_baru[i+1][:, titik:], np.copy(populasi_baru[i][:, titik:])
                
            if random.random() < 0.2:
                # Mutasi: ubah shift kerja secara acak
                k_acak, h_acak = random.randint(0, NUM_KARYAWAN-1), random.randint(0, NUM_HARI-1)
                if populasi_baru[i][k_acak][h_acak] != 0: # Jaga agar libur tidak tergeser
                    populasi_baru[i][k_acak][h_acak] = random.choice([1, 2, 3])
                
        populasi = populasi_baru
        
    waktu_selesai = time.time()
    waktu_komputasi = round(waktu_selesai - waktu_mulai, 2)
    progress_bar.empty()
    status_text.empty()
    
    return jadwal_terbaik, fitness_terbaik, penalti_terbaik, pelanggaran_terbaik, riwayat_fitness, waktu_komputasi

# ==========================================
# 4. KONVERSI EXCEL
# ==========================================
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Jadwal Shift WSS')
    processed_data = output.getvalue()
    return processed_data

# ==========================================
# 5. TAMPILAN DASHBOARD
# ==========================================
st.title("🏪 Aplikasi Penjadwalan Shift Kerja WSS Dawuhan")
st.markdown("Algoritma Genetika Otomatis - Periode 30 Hari Kerja")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Pengaturan Komputer")
pop_size = st.sidebar.slider("Populasi (Kombinasi Jadwal)", 20, 100, 50)
max_gen = st.sidebar.slider("Generasi (Lama Mesin Berpikir)", 100, 1000, 300)

if st.sidebar.button("🚀 BUAT JADWAL 1 BULAN", type="primary"):
    
    js_akhir, fit_akhir, pen_akhir, pel_akhir, riwayat, waktu = jalankan_ga(pop_size, max_gen)
    
    # ------------------ HASIL ------------------
    st.markdown("### 🏆 Hasil Algoritma")
    if pen_akhir == 0:
        st.success(f"**JADWAL SEMPURNA!** Seluruh aturan WSS berhasil dipenuhi dalam waktu {waktu} detik.")
    else:
        st.warning(f"**Mendekati Optimal.** Waktu kalkulasi: {waktu} detik. Terdapat {pen_akhir} sisa poin penalti yang terpaksa dilanggar (Silakan tambah nilai *Generasi* untuk hasil lebih baik).")
        with st.expander("Lihat Sisa Pelanggaran Aturan"):
            for p in pel_akhir: st.write(f"- {p}")

    # Render Tabel
    hari_cols = [f"Hari-{i+1}" for i in range(NUM_HARI)]
    df_akhir = pd.DataFrame(js_akhir, columns=hari_cols)
    df_akhir.insert(0, "Jabatan", [k["role"] for k in KARYAWAN])
    df_akhir.insert(0, "Nama Karyawan", [k["nama"] for k in KARYAWAN])
    
    df_tampil = df_akhir.copy()
    for col in hari_cols:
        df_tampil[col] = df_tampil[col].map(NAMA_SHIFT)
        
    st.dataframe(df_tampil, use_container_width=True)

    # Tombol Download Excel
    excel_data = to_excel(df_tampil)
    st.download_button(
        label="📥 Download Jadwal sebagai File Excel (.xlsx)",
        data=excel_data,
        file_name='Jadwal_Kerja_WSS.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    
    # Grafik untuk Bab 4
    st.markdown("---")
    with st.expander("📈 Tampilkan Grafik Analisis Akademis (Bahan Skripsi)"):
        st.write("Grafik Peningkatan Nilai Fitness (*Convergence Tracker*):")
        df_chart = pd.DataFrame({"Generasi": range(len(riwayat)), "Fitness": riwayat}).set_index("Generasi")
        st.line_chart(df_chart)

else:
    st.info("💡 Pastikan nama-nama karyawan di panel kiri sudah sesuai, lalu klik tombol **BUAT JADWAL 1 BULAN** untuk menjalankan komputasi Algoritma Genetika.")
