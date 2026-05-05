import streamlit as st
import pandas as pd
import random

# 1. Judul dan Keterangan (Sesuai Gambar 2)
st.title("🗓️ Generator Jadwal Skripsi")

# 2. Input Nama Karyawan (Agar bisa diubah saat rotasi cabang)
# Kamu bisa mengisi nilai default agar tidak perlu mengetik dari awal setiap saat
input_karyawan = st.text_input(
    "Daftar Karyawan (pisahkan dengan koma)", 
    "Indah, Andri, Tika, Firman, Elan, Nila, Novi, Alfi"
)

# Tombol untuk menjalankan sistem
if st.button("Generate Jadwal"):
    # Membersihkan data input
    list_karyawan = [nama.strip() for nama in input_karyawan.split(",") if nama.strip()]
    
    if len(list_karyawan) < 6:
        st.error("Jumlah karyawan minimal 6 orang agar shift bisa terbagi adil.")
    else:
        # --- LOGIKA SKRIPSI (Kunci Libur & Cek Riwayat) ---
        # (Bagian ini menggunakan logika yang kita diskusikan sebelumnya)
        
        # Contoh sederhana untuk menampilkan tabel seperti Gambar 2:
        # Kita buat tabel dengan kolom: Hari, Pagi, Siang, Break, Libur
        hasil_jadwal = [] 
        # ... proses perhitungan algoritma di sini ...
        
        # Menampilkan hasil dalam bentuk tabel Streamlit yang bersih
        df_hasil = pd.DataFrame(hasil_jadwal)
        st.table(df_hasil)
