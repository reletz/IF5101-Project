CREATE TABLE bidang_usaha (
    id_bidang SERIAL PRIMARY KEY,
    nama_bidang VARCHAR(100) NOT NULL
);

CREATE TABLE skala_usaha (
    id_skala SERIAL PRIMARY KEY,
    nilai_skala SMALLINT NOT NULL
);

CREATE TABLE unit_dcs (
    id_unit SERIAL PRIMARY KEY,
    sektor_bidang_usaha VARCHAR(100) NOT NULL
);

CREATE TABLE unit_pengujian (
    id_unit SERIAL PRIMARY KEY,
    kapasitas_pengujian INT NOT NULL
);

CREATE TABLE unit_sustainability (
    id_unit SERIAL PRIMARY KEY,
    versi_pedoman_esg INT NOT NULL
);

CREATE TABLE unit_pengadaan (
    id_unit SERIAL PRIMARY KEY
);

CREATE TABLE status_purchase_order (
    id_status SERIAL PRIMARY KEY,
    jenis VARCHAR(50) NOT NULL UNIQUE
        CHECK (jenis IN ('Sedang Berlangsung', 'Selesai'))
);

CREATE TABLE pemasok (
    id_pemasok SERIAL PRIMARY KEY,
    nama_pemasok VARCHAR(100) NOT NULL,
    npwp VARCHAR(20) NOT NULL,
    kontak_operasional VARCHAR(20) NOT NULL,
    modal_dasar NUMERIC(18,2),
    tipe_pemasok VARCHAR(20) NOT NULL
        CHECK (tipe_pemasok IN ('pemasok_baru', 'pemasok_jaringan')),
    id_bidang INT REFERENCES bidang_usaha(id_bidang),
    id_skala INT REFERENCES skala_usaha(id_skala)
);

CREATE TABLE unit_logistik (
    id_unit SERIAL PRIMARY KEY,
    wilayah_operasional VARCHAR(100) NOT NULL,
    id_unit_sustainability INT REFERENCES unit_sustainability(id_unit)
);

CREATE TABLE sertifikasi_uji_mutu (
    id_sertifikat_uji_mutu SERIAL PRIMARY KEY,
    id_unit INT NOT NULL REFERENCES unit_pengujian(id_unit)
);

CREATE TABLE permintaan_pengadaan (
    id_permintaan SERIAL PRIMARY KEY,
    tanggal_inisiasi TIMESTAMP NOT NULL,
    deskripsi_kebutuhan VARCHAR(255),
    estimasi_nilai_harga NUMERIC(18,2),
    id_unit INT NOT NULL REFERENCES unit_pengadaan(id_unit)
);

CREATE TABLE pengalaman (
    id_pengalaman SERIAL PRIMARY KEY,
    deskripsi VARCHAR(100),
    durasi INT,
    id_pemasok INT NOT NULL REFERENCES pemasok(id_pemasok),
    id_bidang INT REFERENCES bidang_usaha(id_bidang)
);

CREATE TABLE pemasok_baru (
    id_pemasok INT PRIMARY KEY REFERENCES pemasok(id_pemasok),
    status_verifikasi_dcs BOOLEAN
);

CREATE TABLE pemasok_jaringan (
    id_pemasok INT PRIMARY KEY REFERENCES pemasok(id_pemasok),
    id_sertifikat_uji_mutu INT NOT NULL
        REFERENCES sertifikasi_uji_mutu(id_sertifikat_uji_mutu)
);

CREATE TABLE tender (
    id_tender SERIAL PRIMARY KEY,
    judul_tender VARCHAR(100) NOT NULL,
    tanggal_buka DATE NOT NULL,
    tanggal_tutup DATE,
    status_tender VARCHAR(20) NOT NULL
        CHECK (status_tender IN ('Buka', 'Tutup', 'Batal')),
    id_permintaan INT NOT NULL REFERENCES permintaan_pengadaan(id_permintaan),
    CHECK (tanggal_tutup IS NULL OR tanggal_tutup >= tanggal_buka),
    UNIQUE (id_tender, id_permintaan)
);

CREATE TABLE proposal_penawaran (
    id_proposal SERIAL PRIMARY KEY,
    tanggal_penawaran DATE NOT NULL,
    nilai_penawaran NUMERIC(18,2),
    dokumen_proposal VARCHAR(100) NOT NULL,
    id_tender INT NOT NULL REFERENCES tender(id_tender),
    id_pemasok INT NOT NULL REFERENCES pemasok(id_pemasok)
);

CREATE TABLE kontrak (
    id_kontrak SERIAL PRIMARY KEY,
    nomor_kontrak VARCHAR(20) NOT NULL,
    tanggal_mulai DATE NOT NULL,
    tanggal_selesai DATE,
    id_tender INT UNIQUE,
    id_pemasok INT NOT NULL REFERENCES pemasok(id_pemasok),
    id_permintaan INT NOT NULL REFERENCES permintaan_pengadaan(id_permintaan),
    CHECK (tanggal_selesai IS NULL OR tanggal_selesai >= tanggal_mulai),
    FOREIGN KEY (id_tender, id_permintaan)
        REFERENCES tender(id_tender, id_permintaan),
    UNIQUE (id_kontrak, id_pemasok)
);

CREATE TABLE dokumen_pengadaan (
    id_dokumen SERIAL PRIMARY KEY,
    nomor_dokumen VARCHAR(30) NOT NULL,
    deskripsi_dokumen VARCHAR(255),
    metode_pengadaan VARCHAR(50),
    tanggal_penyusunan DATE,
    id_tender INT NOT NULL REFERENCES tender(id_tender)
);

CREATE TABLE verifikasi_dcs (
    id_verifikasi SERIAL PRIMARY KEY,
    tanggal_verifikasi DATE NOT NULL,
    id_unit INT NOT NULL REFERENCES unit_dcs(id_unit),
    id_pemasok INT NOT NULL REFERENCES pemasok_baru(id_pemasok)
);

CREATE TABLE evaluasi_qcds (
    id_evaluasi_qcds SERIAL PRIMARY KEY,
    skor_quality REAL CHECK (skor_quality BETWEEN 0 AND 25),
    skor_cost REAL CHECK (skor_cost BETWEEN 0 AND 25),
    skor_delivery REAL CHECK (skor_delivery BETWEEN 0 AND 25),
    skor_service REAL CHECK (skor_service BETWEEN 0 AND 25),
    skor_total REAL GENERATED ALWAYS AS (
        COALESCE(skor_quality, 0) + COALESCE(skor_cost, 0)
        + COALESCE(skor_delivery, 0) + COALESCE(skor_service, 0)
    ) STORED,
    id_pemasok INT NOT NULL,
    id_kontrak INT NOT NULL,
    id_unit_pengujian INT NOT NULL REFERENCES unit_pengujian(id_unit),
    FOREIGN KEY (id_kontrak, id_pemasok)
        REFERENCES kontrak(id_kontrak, id_pemasok),
    UNIQUE (id_evaluasi_qcds, id_kontrak)
);

CREATE TABLE nilai_esg (
    id_penilaian_esg SERIAL PRIMARY KEY,
    tanggal_penilaian TIMESTAMP,
    skor_lingkungan REAL CHECK (skor_lingkungan BETWEEN 0 AND 20),
    skor_kesetaraan_gender REAL CHECK (skor_kesetaraan_gender BETWEEN 0 AND 20),
    skor_ham REAL CHECK (skor_ham BETWEEN 0 AND 20),
    skor_k3 REAL CHECK (skor_k3 BETWEEN 0 AND 20),
    skor_tata_kelola REAL CHECK (skor_tata_kelola BETWEEN 0 AND 20),
    skor_keseluruhan REAL GENERATED ALWAYS AS (
        COALESCE(skor_lingkungan, 0) + COALESCE(skor_kesetaraan_gender, 0)
        + COALESCE(skor_ham, 0) + COALESCE(skor_k3, 0)
        + COALESCE(skor_tata_kelola, 0)
    ) STORED,
    status_pakta_integritas BOOLEAN,
    id_pemasok INT NOT NULL,
    id_kontrak INT NOT NULL,
    id_unit_logistik INT NOT NULL REFERENCES unit_logistik(id_unit),
    FOREIGN KEY (id_kontrak, id_pemasok)
        REFERENCES kontrak(id_kontrak, id_pemasok),
    UNIQUE (id_penilaian_esg, id_kontrak)
);

CREATE TABLE purchase_order (
    id_po SERIAL PRIMARY KEY,
    nomor_po VARCHAR(30) NOT NULL,
    tanggal_terbit DATE NOT NULL,
    nilai_nominal NUMERIC(18,2),
    tanggal_tenggat_pengiriman DATE NOT NULL,
    id_status INT NOT NULL REFERENCES status_purchase_order(id_status),
    id_kontrak INT NOT NULL REFERENCES kontrak(id_kontrak),
    CHECK (tanggal_tenggat_pengiriman >= tanggal_terbit)
);

CREATE TABLE evaluasi_akhir (
    id_evaluasi_akhir SERIAL PRIMARY KEY,
    hasil_akhir VARCHAR(20) NOT NULL
        CHECK (hasil_akhir IN ('Blacklist', 'Beberapa Masalah', 'Baik', 'Sangat Baik')),
    id_kontrak INT NOT NULL,
    id_penilaian_esg INT NOT NULL,
    id_evaluasi_qcds INT NOT NULL,
    FOREIGN KEY (id_penilaian_esg, id_kontrak)
        REFERENCES nilai_esg(id_penilaian_esg, id_kontrak),
    FOREIGN KEY (id_evaluasi_qcds, id_kontrak)
        REFERENCES evaluasi_qcds(id_evaluasi_qcds, id_kontrak)
);
