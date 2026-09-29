# Chat Terenkripsi DES

Aplikasi chat dua arah berbasis TCP. Setiap pesan dienkripsi dengan **DES (mode CBC)** sebelum dikirim, lalu didekripsi di sisi penerima. Algoritma DES diimplementasikan sendiri tanpa library kriptografi.

## Struktur File

| File | Isi |
|---|---|
| `cipher.py` | Implementasi algoritma DES serta fungsi `encrypt()` dan `decrypt()` |
| `chat.py` | Program chat socket TCP (mode server dan client) yang memakai `cipher.py` |

## `cipher.py` — Algoritma DES

DES adalah block cipher yang mengenkripsi data per blok **64 bit (8 byte)** dengan key **64 bit** (56 bit efektif).

**1. Pembentukan key**
- `derive_key()`: key dari user (panjangnya bebas) diulang atau dipotong menjadi 8 byte.
- `subkeys()`: key schedule DES. Key dipermutasi dengan **PC1** (64 → 56 bit) lalu dibagi menjadi dua bagian C dan D. Di setiap ronde, C dan D dirotasi ke kiri, lalu dipermutasi dengan **PC2** (56 → 48 bit). Hasilnya **16 subkey**.

**2. Enkripsi satu blok (`des_block()`)**
- **Initial Permutation (IP)**, lalu blok dibagi menjadi L dan R (masing-masing 32 bit).
- **16 ronde Feistel**: `L_i = R_(i-1)`, `R_i = L_(i-1) XOR f(R_(i-1), K_i)`.
- **Final Permutation (FP)**, yaitu kebalikan dari IP.

**3. Fungsi ronde `f()`**
- Ekspansi **E** (32 → 48 bit), lalu XOR dengan subkey.
- Substitusi **8 S-box** (6 bit → 4 bit per S-box), yaitu bagian non-linear DES.
- Permutasi **P** (32 bit).

**4. Dekripsi**: memakai fungsi `des_block()` yang sama dengan urutan subkey dibalik (K16 → K1).

**5. Padding PKCS#7** (`pad()` / `unpad()`): menggenapkan panjang pesan menjadi kelipatan 8 byte. Jika key salah, padding tidak valid dan dekripsi gagal.

**6. Mode CBC** (`encrypt()` / `decrypt()`)
- Enkripsi: `C_i = DES(P_i XOR C_(i-1))`, dengan `C_0` = IV acak 8 byte.
- Karena IV acak, pesan yang sama menghasilkan ciphertext yang berbeda setiap kali dikirim.
- Output: `IV (8 byte) || ciphertext`.

Implementasi sudah diverifikasi dengan test vector standar DES:
key `133457799BBCDFF1`, plaintext `0123456789ABCDEF` → ciphertext `85E813540F0AB405`.

## `chat.py` — Program Chat

- **Key** diambil dari environment variable `KI_KEY` dan **tidak pernah dikirim** lewat jaringan. Kedua pihak harus memakai key yang sama.
- **Mode server**: listen di port `5000` dan menunggu satu client.
- **Mode client**: terhubung ke IP server di port `5000`.
- **Format pesan**: `[panjang 4 byte][IV 8 byte][ciphertext]`. Prefix panjang dipakai supaya penerima tahu batas setiap pesan pada stream TCP (`send_msg()` / `recv_msg()`).
- **Thread penerima** (`receiver()`) berjalan di latar belakang: menerima ciphertext, menampilkannya dalam hex, lalu mendekripsi dan menampilkan plaintext.
- **Thread utama** membaca input user, mengenkripsinya, menampilkan ciphertext dalam hex, lalu mengirimkannya.

## Cara Menjalankan

**Server (VM):**
```bash
KI_KEY=rahasia python3 chat.py server
```

**Client (Windows PowerShell):**
```powershell
$env:KI_KEY="rahasia"; python chat.py client 20.2.91.159
```

Port 5000 harus dibuka di firewall server (misalnya NSG di Azure).

## Melihat Ciphertext di Wireshark

1. Capture di interface jaringan yang dipakai, dengan filter `tcp.port == 5000`.
2. Wireshark mengenali port 5000 sebagai protokol IPA/RSL. Nonaktifkan lewat **Analyze → Enabled Protocols → IPA** agar paket terbaca sebagai TCP biasa.
3. Pilih paket `[PSH, ACK]`. Bagian **Data** berisi panjang pesan, IV, dan ciphertext yang sama dengan output `[ciphertext dikirim]` di terminal. Plaintext tidak terlihat di jaringan.
