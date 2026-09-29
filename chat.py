import os, socket, struct, sys, threading
from cipher import encrypt, decrypt

KEY = os.environ["KI_KEY"].encode()   # key tidak pernah dikirim
PORT = 5000

def recv_exact(s, n):
    buf = b""
    while len(buf) < n:
        chunk = s.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("koneksi terputus")
        buf += chunk
    return buf

def send_msg(s, data: bytes):
    s.sendall(struct.pack(">I", len(data)) + data)

def recv_msg(s) -> bytes:
    n = struct.unpack(">I", recv_exact(s, 4))[0]
    return recv_exact(s, n)

def receiver(s):
    try:
        while True:
            ct = recv_msg(s)
            print(f"\n[ciphertext diterima] {ct.hex()}")
            try:
                print(f"[plaintext] {decrypt(ct, KEY).decode(errors='replace')}")
            except ValueError as e:
                print(f"[gagal dekripsi] {e}")
    except ConnectionError:
        print("lawan terputus")
        os._exit(0)

def main():
    mode = sys.argv[1]
    if mode == "server":
        srv = socket.socket()
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", PORT))
        srv.listen(1)
        print("menunggu client...")
        s, addr = srv.accept()
        print("terhubung:", addr)
    else:
        s = socket.socket()
        s.connect((sys.argv[2], PORT))
        print("terhubung ke server")

    threading.Thread(target=receiver, args=(s,), daemon=True).start()
    while True:
        msg = input("> ").encode()
        ct = encrypt(msg, KEY)
        print(f"[ciphertext dikirim] {ct.hex()}")
        send_msg(s, ct)

main()
