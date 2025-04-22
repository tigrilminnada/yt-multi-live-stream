
# Youtube Multi Live Stream ( windows Edition )

📥 Langkah 1: Instal Prasyarat
1. Install Python 3.10+
- Download Python dari python.org
- Pilih "Add Python to PATH" selama instalasi
- Verifikasi instalasi dengan buka CMD dan ketik: ``python --version``

2. Install FFmpeg
- Download FFmpeg dari https://ffmpeg.org/download.html
- Ekstrak zip ke C:\ffmpeg
Tambahkan ke PATH:

- Buka Control Panel > System > Advanced system - settings > Environment Variables
- Edit Path di bagian "System variables"
- Tambahkan path: C:\ffmpeg\bin
- Verifikasi di CMD: ``ffmpeg -version``

⚙️ Langkah 2: Setup Tool
1. Download Script
```
https://github.com/tigrilminnada/yt-multi-live-stream/archive/refs/heads/main.zip
```

2. Install Dependencies
```
pip install windows-curses
```
3. Konfigurasi Awal
- Jalankan tool pertama kali:
```
python main.py
```

🎥 Langkah 3: Menjalankan Multi-Streaming

1. Tambah Akun YouTube
`` 1. Pilih menu Account Management > Add New Account``
*Masukkan:*

- ``Stream Key: Dapatkan dari YouTube Studio > Go Live``
- ``Video Source: Path file (e.g., D:\video.mp4) atau URL stream``

- ``Label: Nama untuk identifikasi``

2. Atur Preset Kualitas
- Pilih menu Preset Management untuk ubah kualitas:
  - ``low (480p), medium (720p), high (1080p), ultra (1440p)``

3. Mulai Streaming
- Single Stream:
- ``Pilih Stream Control > Start Stream for Account``
- ``Pilih ID akun dan aktifkan looping (opsional)``

- Multi-Stream:
- ``Pilih Start All Streams untuk mulai semua akun sekaligus``

4. Monitor Status
- ``Pilih View Streaming Status untuk lihat uptime dan status real-time:``

```
ID  Label           Preset    Status      Uptime    PID       Video Source
1   Channel Gaming  medium    streaming   01:23:45  12345     D:\game.mp4
2   Music Live      high      stopped     00:00:00  N/A       http://stream.url
```

📌 Catatan Penting
- Tool ini tidak mendukung streaming ke platform selain YouTube.

## Authors

- [@masanto](https://www.facebook.com/@scht.id)

