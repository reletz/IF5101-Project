import io, random
from datetime import date, datetime, timedelta
import psycopg2
from faker import Faker

CONFIG = {
    "baseline": {
        "pemasok": 349,
        "permintaan_pengadaan": 209,
        "kontrak": 175
    },

    "stress_test": {
        "pemasok": 1000,
        "permintaan_pengadaan": 600,
        "kontrak": 500
    }
}

MODE = "baseline"

JUMLAH_DATA = CONFIG[MODE]

TODAY = date(2026, 11, 3)
random.seed(42); Faker.seed(42)
fake = Faker("id_ID")

conn = psycopg2.connect(host="192.168.0.181", dbname="telkome_baseline",
                        user="postgres", password="mandat4" , port=5432)
cur = conn.cursor()

def bulk(table, cols, rows):
    buf = io.StringIO()
    for r in rows:
        buf.write("\t".join("\\N" if v is None else str(v) for v in r) + "\n")
    buf.seek(0)
    cur.copy_expert(f"COPY {table} ({','.join(cols)}) FROM STDIN", buf)

def d(base, lo, hi):      
    return base + timedelta(days=random.randint(lo, hi))

# Contoh data
bidang = ["Telekomunikasi", "Perangkat Jaringan", "Konstruksi Sipil",
          "Kabel dan Fiber Optik", "Teknologi Informasi", "Logistik",
          "Energi dan Power", "Jasa Konsultan", "Pemeliharaan", "Alat Kerja"]
bulk("bidang_usaha", ["id_bidang", "nama_bidang"], [(i+1, n) for i, n in enumerate(bidang)])
bulk("skala_usaha", ["id_skala", "nilai_skala"], [(1, 1), (2, 2), (3, 3)])   # 1 kecil, 2 menengah, 3 besar
bulk("unit_dcs", ["id_unit", "sektor_bidang_usaha"], [(i, random.choice(bidang)) for i in range(1, 6)])
bulk("unit_pengujian", ["id_unit", "kapasitas_pengujian"], [(i, random.randint(50, 500)) for i in range(1, 6)])
bulk("unit_sustainability", ["id_unit", "versi_pedoman_esg"], [(i, i) for i in range(1, 4)])

wilayah = ["Jawa", "Sumatera", "Kalimantan", "Sulawesi", "Papua"]

bulk("unit_logistik", ["id_unit", "wilayah_operasional", "id_unit_sustainability"],
     [(i, wilayah[i-1], random.randint(1, 3)) for i in range(1, 6)])
bulk("unit_pengadaan", ["id_unit"], [(i,) for i in range(1, 6)])
bulk("status_purchase_order", ["id_status", "jenis"], [(1, "Sedang Berlangsung"), (2, "Selesai")])

N_PEM = JUMLAH_DATA["pemasok"]
pemasok, baru, jaringan = [], [], []
for i in range(1, N_PEM + 1):
    tipe = "pemasok_baru" if random.random() < 0.3 else "pemasok_jaringan"
    pemasok.append((i, fake.company()[:100], fake.numerify("##.###.###.#-###.###"),
                    fake.numerify("08##########"), random.randint(5*10**7, 5*10**10),
                    tipe, random.randint(1, 10), random.choices([1, 2, 3], [5, 3, 2])[0]))
    (baru if tipe == "pemasok_baru" else jaringan).append(i)

# constraint 1: pemasok jaringan harus memiliki sertifikasi uji mutu per pemasok
bulk("sertifikasi_uji_mutu", ["id_sertifikat_uji_mutu", "id_unit"],
     [(k+1, random.randint(1, 5)) for k in range(len(jaringan))])
bulk("pemasok", ["id_pemasok", "nama_pemasok", "npwp", "kontak_operasional",
                 "modal_dasar", "tipe_pemasok", "id_bidang", "id_skala"], pemasok)
bulk("pemasok_jaringan", ["id_pemasok", "id_sertifikat_uji_mutu"],
     [(p, k+1) for k, p in enumerate(jaringan)])

# contoh case: terdapat 65% pemasok baru yang lolos, 3% gagal, dan sisanya belum terverifikasi
random.shuffle(baru)
n_ok, n_gagal = int(len(baru)*0.65), int(len(baru)*0.03)
lolos, gagal, belum = baru[:n_ok], baru[n_ok:n_ok+n_gagal], baru[n_ok+n_gagal:]
status = {**{p: True for p in lolos}, **{p: False for p in gagal}, **{p: None for p in belum}}
bulk("pemasok_baru", ["id_pemasok", "status_verifikasi_dcs"], [(p, status[p]) for p in baru])
bulk("verifikasi_dcs", ["id_verifikasi", "tanggal_verifikasi", "id_unit", "id_pemasok"],
     [(k+1, d(TODAY, -300, -10), random.randint(1, 5), p) for k, p in enumerate(lolos + gagal)])

# setiap pemasok memiliki pengalaman 1 - 4 tahun
peng, pid = [], 1
for p in range(1, N_PEM + 1):
    for _ in range(random.randint(1, 4)):
        peng.append((pid, fake.sentence(nb_words=5)[:100], random.randint(1, 15), p, random.randint(1, 10)))
        pid += 1
bulk("pengalaman", ["id_pengalaman", "deskripsi", "durasi", "id_pemasok", "id_bidang"], peng)

pemasok_valid = [p for p in range(1, N_PEM + 1) if p not in set(gagal)]

# contoh permintaan, tender, dokumen, dan proposal
N_REQ = JUMLAH_DATA["permintaan_pengadaan"]
req, tender, estimasi = [], [], {}
for i in range(1, N_REQ + 1):
    ini = d(TODAY, -365, -3)
    est = random.randint(5*10**7, 5*10**9); estimasi[i] = est
    req.append((i, datetime.combine(ini, datetime.min.time()) + timedelta(hours=random.randint(7, 17)),
                fake.sentence(nb_words=8)[:255], est, random.randint(1, 5)))
    buka = d(ini, 1, 3); tutup = d(buka, 10, 21)
    if random.random() < 0.05:        st = "Batal"
    elif tutup >= TODAY:              st = "Buka"
    else:                             st = "Buka" if random.random() < 0.03 else "Tutup"   # 3% basi, untuk W6
    tender.append((i, f"Tender {fake.bs()[:60]}", buka, tutup, st, i))
bulk("permintaan_pengadaan", ["id_permintaan", "tanggal_inisiasi", "deskripsi_kebutuhan",
                              "estimasi_nilai_harga", "id_unit"], req)
bulk("tender", ["id_tender", "judul_tender", "tanggal_buka", "tanggal_tutup",
                "status_tender", "id_permintaan"], tender)

metode = ["Tender Terbuka", "Tender Terbatas", "Penunjukan Langsung", "Pemilihan Langsung"]
dok, did = [], 1
for t in tender:
    for _ in range(random.randint(1, 3)):
        dok.append((did, f"DOK-{did:07d}", fake.sentence(nb_words=6)[:255],
                    random.choice(metode), d(t[2], -10, -1), t[0]))
        did += 1
bulk("dokumen_pengadaan", ["id_dokumen", "nomor_dokumen", "deskripsi_dokumen",
                           "metode_pengadaan", "tanggal_penyusunan", "id_tender"], dok)

props, list_proposal, prid = [], {}, 1
for t in tender:
    for p in random.sample(pemasok_valid, random.randint(2, 8)):        
        tgl = d(t[2], 0, max(0, (min(t[3], TODAY) - t[2]).days))
        nilai = round(estimasi[t[0]] * random.uniform(0.8, 1.1), 2)
        props.append((prid, tgl, nilai, f"https://example.com/proposal/{prid}.pdf", t[0], p))
        list_proposal.setdefault(t[0], []).append((p, nilai))
        prid += 1
bulk("proposal_penawaran", ["id_proposal", "tanggal_penawaran", "nilai_penawaran",
                            "dokumen_proposal", "id_tender", "id_pemasok"], props)

# contoh kontrak, po, dan evaluasi
tender_tutup = [t for t in tender if t[4] == "Tutup"]
random.shuffle(tender_tutup)
kontrak, po, qcds, esg, akhir, k_nilai = [], [], [], [], [], {}
poid = 1
for kid, t in enumerate(tender_tutup[:JUMLAH_DATA["kontrak"]], start=1):
    ps = list_proposal[t[0]]
    win = min(ps, key=lambda x: x[1]) if random.random() < 0.6 else random.choice(ps)
    mulai = d(t[3], 7, 20)
    selesai = None if random.random() < 0.1 else d(mulai, 180, 540)
    kontrak.append((kid, f"K-{mulai.year}-{kid:06d}", mulai, selesai, t[0], win[0], t[5]))
    n_po = random.randint(2, 6)
    for _ in range(n_po):
        terbit = d(mulai, 1, 30); tenggat = d(terbit, 14, 60)
        sts = 2 if (tenggat < TODAY and random.random() < 0.7) else 1
        po.append((poid, f"PO-{poid:08d}", terbit, round(win[1] / n_po, 2), tenggat, sts, kid))
        poid += 1
    q = [round(random.triangular(10, 25, 19), 2) for _ in range(4)]
    e = [round(random.triangular(8, 20, 16), 2) for _ in range(5)]
    pakta = random.random() < 0.95
    qcds.append((kid, *q, win[0], kid, random.randint(1, 5)))
    esg.append((kid, datetime.combine(d(mulai, 30, 120), datetime.min.time()), *e, pakta,
                win[0], kid, random.randint(1, 5)))
    if random.random() < 0.7:       
        s_esg, s_q = sum(e), sum(q)
        if (not pakta) or s_esg < 50:   h = "Blacklist"
        elif (s_esg + s_q) / 2 < 70:    h = "Beberapa Masalah"
        elif (s_esg + s_q) / 2 < 85:    h = "Baik"
        else:                           h = "Sangat Baik"
        akhir.append((kid, h, kid, kid, kid))

bulk("kontrak", ["id_kontrak", "nomor_kontrak", "tanggal_mulai", "tanggal_selesai",
                 "id_tender", "id_pemasok", "id_permintaan"], kontrak)
bulk("evaluasi_qcds", ["id_evaluasi_qcds", "skor_quality", "skor_cost", "skor_delivery",
                       "skor_service", "id_pemasok", "id_kontrak", "id_unit_pengujian"], qcds)
bulk("nilai_esg", ["id_penilaian_esg", "tanggal_penilaian", "skor_lingkungan",
                   "skor_kesetaraan_gender", "skor_ham", "skor_k3", "skor_tata_kelola",
                   "status_pakta_integritas", "id_pemasok", "id_kontrak", "id_unit_logistik"], esg)
bulk("purchase_order", ["id_po", "nomor_po", "tanggal_terbit", "nilai_nominal",
                        "tanggal_tenggat_pengiriman", "id_status", "id_kontrak"], po)
bulk("evaluasi_akhir", ["id_evaluasi_akhir", "hasil_akhir", "id_kontrak",
                        "id_penilaian_esg", "id_evaluasi_qcds"],
     [(a[0], a[1], a[2], a[3], a[4]) for a in akhir])

#sinkronisasi sequence dan statistik
for tbl, col in [("bidang_usaha", "id_bidang"), ("skala_usaha", "id_skala"),
                 ("unit_dcs", "id_unit"), ("unit_pengujian", "id_unit"),
                 ("unit_sustainability", "id_unit"), ("unit_logistik", "id_unit"),
                 ("unit_pengadaan", "id_unit"), ("status_purchase_order", "id_status"),
                 ("pemasok", "id_pemasok"), ("sertifikasi_uji_mutu", "id_sertifikat_uji_mutu"),
                 ("verifikasi_dcs", "id_verifikasi"), ("pengalaman", "id_pengalaman"),
                 ("permintaan_pengadaan", "id_permintaan"), ("tender", "id_tender"),
                 ("dokumen_pengadaan", "id_dokumen"), ("proposal_penawaran", "id_proposal"),
                 ("kontrak", "id_kontrak"), ("evaluasi_qcds", "id_evaluasi_qcds"),
                 ("nilai_esg", "id_penilaian_esg"), ("purchase_order", "id_po"),
                 ("evaluasi_akhir", "id_evaluasi_akhir")]:
    cur.execute(f"SELECT setval(pg_get_serial_sequence('{tbl}','{col}'), "
                f"(SELECT MAX({col}) FROM {tbl}))")
conn.commit()
conn.autocommit = True
cur.execute("ANALYZE")
print("selesai")