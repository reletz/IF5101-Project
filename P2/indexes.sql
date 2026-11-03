CREATE INDEX idx_pengalaman_pemasok ON pengalaman(id_pemasok);
CREATE INDEX idx_tender_permintaan ON tender(id_permintaan);
CREATE INDEX idx_proposal_tender ON proposal_penawaran(id_tender);
CREATE INDEX idx_proposal_pemasok ON proposal_penawaran(id_pemasok);
CREATE INDEX idx_kontrak_pemasok ON kontrak(id_pemasok);
CREATE INDEX idx_po_kontrak ON purchase_order(id_kontrak);
CREATE INDEX idx_qcds_pemasok ON evaluasi_qcds(id_pemasok);
CREATE INDEX idx_esg_pemasok ON nilai_esg(id_pemasok);
