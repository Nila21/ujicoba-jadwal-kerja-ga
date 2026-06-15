import streamlit as st
import pandas as pd
import numpy as np
import random
import io

# ==========================================
# 1. KONFIGURASI HALAMAN STREAMLIT
# ==========================================
st.set_page_config(page_title="Optimasi Jadwal Shift", layout="wide")

st.title("🏬 Aplikasi Penjadwalan Shift Kerja WSS")
st.markdown("""
Aplikasi ini menggunakan **Algoritma Genetika** untuk menyusun jadwal shift selama 30 hari berdasarkan batasan (constraints) berikut:
- **Karyawan:** 8 orang (2 PJ, 6 Staf).
- **Shift:** Pagi (1), Siang (2), Break (3), Libur (0).
- **Aturan Libur:** Max 1 orang libur per hari (kecuali Minggu wajib masuk semua). Sebulan tiap karyawan jatah libur 3 kali.
- **Aturan Rotasi:** Shift Siang hari ini **tidak boleh** lanjut Shift Break besok. Shift Break **tidak boleh** 2 hari berturut-turut.
- **Komposisi:** Harus ada pemerataan shift, saat ada 1 yang libur, shift Pagi terisi 2 orang (1 PJ pengganti/asli, 1 Staf).
""")

# ==========================================
# 2. SIDEBAR - PENGATURAN & NAMA KARYAWAN
# ==========================================
st.sidebar.header("👥 Manajemen Karyawan")
st.sidebar.write("Silakan ubah nama jika diperlukan:")

# Menggunakan parameter 'key' yang unik agar tidak terjadi DuplicateElementId
pj1 = st.sidebar.text_input("Nama PJ 1", value="Indah", key="pj1_input")
pj2 = st.sidebar.text_input("Nama PJ 2", value="Andri", key="pj2_input")

staf1 = st.sidebar.text_input("Nama Staf 1", value="Tika", key="staf1_input")
staf2 = st.sidebar.text_input("Nama Staf 2", value="Firman", key="staf2_input")
staf3 = st.sidebar.text_input("Nama Staf 3", value="Elan", key="staf3_input")
staf4 = st.sidebar.text_input("Nama Staf 4", value="Nila", key="staf4_input")
staf5 = st.sidebar.text_input("Nama Staf 5", value="Alfi", key="staf5_input")
staf6 = st.sidebar.text_input("Nama Staf 6", value="Novi", key="staf6_input")

karyawan = [pj1, pj2, staf1, staf2, staf3, staf4, staf5, staf6]

st.sidebar.header("⚙️ Pengaturan Algoritma")
pop_size = st.sidebar.slider("Populasi (Kombinasi Jadwal)", 10, 100, 50, key="pop_slider")
generations = st.sidebar.slider("Generasi (Lama Mesin Berpikir)", 50, 500, 200, key="gen_slider")
mutation_rate = 0.1

# ==========================================
# 3. FUNGSI ALGORITMA GENETIKA
# ==========================================
# Shift Code: 0 = Libur, 1 = Pagi, 2 = Siang, 3 = Break

def create_individual():
    """Membuat 1 jadwal (kromosom) acak yang masuk akal secara logis."""
    # Kromosom: [karyawan][hari] = shift
    ind = [[1 for _ in range(30)] for _ in range(8)]
    for d in range(30):
        is_sunday = (d % 7 == 6) # Anggap hari ke-6, 13, 20, 27 adalah Minggu
        
        # Penentuan siapa yang libur (kecuali hari Minggu)
        off_employee = -1
        if not is_sunday and random.random() < 0.8: # 80% peluang ada 1 orang libur di hari biasa
            off_employee = random.randint(0, 7)
            ind[off_employee][d] = 0
            
        # Distribusi shift untuk yang masuk
        working_emps = [e for e in range(8) if e != off_employee]
        random.shuffle(working_emps)
        
        # Pastikan tiap shift (1, 2, 3) terisi minimal 2 orang
        for i, emp in enumerate(working_emps):
            ind[emp][d] = (i % 3) + 1 # Akan membagi rata shift 1, 2, 3
            
    return ind

def calculate_fitness(ind):
    """Menghitung nilai kesesuaian jadwal. Makin tinggi makin baik. Pinalti jika melanggar aturan."""
    score = 10000 
    
    # Cek per hari
    for d in range(30):
        is_sunday = (d % 7 == 6)
        shifts_today = [ind[e][d] for e in range(8)]
        
        off_count = shifts_today.count(0)
        pagi_count = shifts_today.count(1)
        siang_count = shifts_today.count(2)
        break_count = shifts_today.count(3)
        
        # Hard Constraint: Minggu wajib masuk
        if is_sunday and off_count > 0:
            score -= 1000 * off_count
            
        # Hard Constraint: Sehari maks 1 orang libur
        if not is_sunday and off_count > 1:
            score -= 800 * (off_count - 1)
            
        # Constraint: Jika 1 libur, shift Pagi terisi 2 orang (Pagi harus 2 orang)
        if off_count == 1:
            if pagi_count != 2:
                score -= 300
        
        # Penalti jika ada shift kosong atau kurang dari 2 (selain aturan Pagi saat ada yang libur)
        if pagi_count < 2: score -= 200
        if siang_count < 2: score -= 200
        if break_count < 2: score -= 200
            
    # Cek per karyawan
    for e in range(8):
        shifts_emp = ind[e]
        off_days = shifts_emp.count(0)
        
        # Constraint: Sebulan jatah libur 3 kali
        if off_days > 3:
            score -= 500 * (off_days - 3)
        elif off_days < 3:
            score -= 200 * (3 - off_days) # Usahakan adil dapat libur 3 hari
            
        # Cek transisi shift dari hari ke hari
        for d in range(29):
            today = shifts_emp[d]
            tomorrow = shifts_emp[d+1]
            
            # Constraint: Siang -> Break esok hari TIDAK BOLEH
            if today == 2 and tomorrow == 3:
                score -= 800
                
            # Constraint: Break -> Break berurutan TIDAK BOLEH
            if today == 3 and tomorrow == 3:
                score -= 800
                
    return score

def crossover(parent1, parent2):
    """Pertukaran silang jadwal antar karyawan secara acak."""
    child1, child2 = [], []
    for e in range(8):
        if random.random() > 0.5:
            child1.append(parent1[e].copy())
            child2.append(parent2[e].copy())
        else:
            child1.append(parent2[e].copy())
            child2.append(parent1[e].copy())
    return child1, child2

def mutate(ind):
    """Mutasi acak untuk mencari kombinasi baru."""
    for e in range(8):
        if random.random() < mutation_rate:
            day = random.randint(0, 29)
            # Ganti shift secara acak (0, 1, 2, atau 3)
            ind[e][day] = random.randint(0, 3)
    return ind

# ==========================================
# 4. TAMPILAN UTAMA & EKSEKUSI
# ==========================================
if st.sidebar.button("🚀 BUAT JADWAL 1 BULAN", key="run_btn"):
    with st.spinner("Mesin Genetika sedang merakit jadwal terbaik..."):
        # Inisialisasi Populasi
        population = [create_individual() for _ in range(pop_size)]
        
        # Proses Evolusi
        progress_bar = st.progress(
