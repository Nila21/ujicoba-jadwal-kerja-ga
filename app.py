import streamlit as st
import pandas as pd
import random

# --- FUNGSI LOGIKA UTAMA ---

def inisialisasi_libur(daftar_karyawan):
    """Mengunci 3 hari libur per orang tanpa bentrok (max 1 orang libur/hari)"""
    hari_kerja = [d for d in range(1, 31) if d % 7 != 0] # Lewati hari Minggu
    random.shuffle(hari_kerja)
    
    jadwal_libur = {k: [] for k in daftar_karyawan}
    # Ambil 24 slot libur (8 orang * 3 hari)
    slot_terpakai = hari_kerja[:len(daftar_karyawan) * 3]
    
    for i, tgl in enumerate(slot_terpakai):
        karyawan = daftar_karyawan[i % len(daftar_karyawan)]
        jadwal_libur[karyawan].append(tgl)
    return jadwal_libur

def buat_jadwal(daftar_karyawan):
    jadwal_libur = inisialisasi_libur(daftar_karyawan)
    hasil_jadwal = []
    shift_kemarin = {k: None for k in daftar_karyawan}
    
    for hari in range(1, 31):
        is_minggu = (hari % 7 == 0)
        
        if is_minggu:
            hasil_jadwal.append({
                "Hari": f"Hari {hari}",
                "Pagi": ", ".join(daftar_karyawan[:4]),
                "Siang": ", ".join(daftar_karyawan[4:]),
                "Break": "-",
                "Libur": "MINGGU (Masuk Semua)"
            })
            continue

        # Siapa yang libur hari ini?
        yang_libur = [k for k, tgl in jadwal_libur.items() if hari in tgl]
        aktif = [k for k in daftar_karyawan if k not in yang_libur]
        random.shuffle(aktif) # Rotasi agar adil
        
        pagi, siang, brk = [], [], []
        
        for k in aktif:
            # ATURAN KESEHATAN: Cek riwayat kemarin
            boleh_break = shift_kemarin[k] not in ["Siang", "Break"]
            
            if len(pagi) < 3: # Misal slot pagi 3 orang
                pagi.append(k)
                shift_kemarin[k] = "Pagi"
            elif len(siang) < 2: # Misal slot siang 2 orang
                siang.append(k)
                shift_kemarin[k] = "Siang"
            elif boleh_break and len(brk) < 2: # Slot break
                brk.append(k)
                shift_kemarin[k] = "Break"
            else:
                # Jika tidak boleh break, paksa masuk pagi/siang yang sisa
                pagi.append(k) 
                shift_kemarin[k] = "Pagi"

        hasil_jadwal.append({
            "Hari": f"Hari {hari}",
            "Pagi": ", ".join(pagi),
            "Siang": ", ".join(siang),
            "Break": ", ".join(brk),
            "Libur": ", ".join(yang_libur)
        })
    return hasil_jadwal

# --- TAMPILAN INTERFACE (STREAMLIT) ---

st.set_page_config(layout="wide") # Agar tabel terlihat luas di HP
st.title("🗓️ Generator Jadwal Toko (Versi Skripsi)")

# Input Karyawan (Fleksibel untuk rotasi cabang)
input_nama = st.text_input("Input Nama Karyawan (Pisahkan dengan koma):", 
                           "Indah, Andri, Tika, Firman, Elan, Nila, Novi, Alfi")

if st.button("Buat Jadwal Baru"):
    list_k = [n.strip() for n in input_nama.split(",") if n.strip()]
    
    if len(list_k) < 8:
        st.warning("⚠️ Masukkan minimal 8 nama untuk hasil optimal.")
    else:
        data = buat_jadwal(list_k)
        df = pd.DataFrame(data)
        st.table(df) # Menampilkan tabel seperti Gambar 1
