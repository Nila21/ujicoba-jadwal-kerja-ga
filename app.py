import streamlit as st
import pandas as pd
import random

# --- LOGIKA UTAMA ---

def generator_jadwal_pintar(list_karyawan):
    # 1. Inisialisasi Libur (Kunci 3 hari per orang, max 1 orang libur/hari)
    hari_kerja = [d for d in range(1, 31) if d % 7 != 0]
    random.shuffle(hari_kerja)
    
    jadwal_libur = {k: [] for k in list_karyawan}
    for i, tgl in enumerate(hari_kerja[:len(list_karyawan)*3]):
        karyawan = list_karyawan[i % len(list_karyawan)]
        jadwal_libur[karyawan].append(tgl)

    # 2. Susun Jadwal Harian
    hasil_jadwal = []
    shift_kemarin = {k: None for k in list_karyawan}
    
    for hari in range(1, 31):
        is_minggu = (hari % 7 == 0)
        # Tentukan siapa yang libur
        yang_libur = [k for k, tgl in jadwal_libur.items() if hari in tgl]
        aktif = [k for k in list_karyawan if k not in yang_libur]
        random.shuffle(aktif) # Rotasi harian
        
        # Logika pembagian shift dengan pengecekan aturan B
        pagi, siang, brk = [], [], []
        n = len(aktif)
        size = n // 3
        
        for k in aktif:
            # Cek aturan: Siang -> Besok tidak boleh Break
            # Cek aturan: Break -> Besok tidak boleh Break
            boleh_break = shift_kemarin[k] not in ["Siang", "Break"]
            
            if len(pagi) < size:
                pagi.append(k)
                shift_kemarin[k] = "Pagi"
            elif len(siang) < size:
                siang.append(k)
                shift_kemarin[k] = "Siang"
            elif boleh_break:
                brk.append(k)
                shift_kemarin[k] = "Break"
            else:
                # Jika tidak boleh break tapi slot lain penuh, tukar ke pagi/siang
                pagi.append(k)
                shift_kemarin[k] = "Pagi"

        hasil_jadwal.append({
            "Hari": f"Hari {hari}",
            "Pagi": ", ".join(pagi),
            "Siang": ", ".join(siang),
            "Break": ", ".join(brk),
            "Libur": ", ".join(yang_libur) if not is_minggu else "Minggu (Masuk Semua)"
        })
        
    return hasil_jadwal

# --- INTERFACE STREAMLIT ---
st.title("🗓️ Generator Jadwal Skripsi")
karyawan_input = st.text_input("Daftar Karyawan (koma)", "Indah, Andri, Tika, Firman, Elan, Nila, Novi, Alfi")
list_k = [x.strip() for x in karyawan_input.split(",")]

if st.button("Generate Jadwal"):
    hasil = generator_jadwal_pintar(list_k)
    st.table(pd.DataFrame(hasil))
