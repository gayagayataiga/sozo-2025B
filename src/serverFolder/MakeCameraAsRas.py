import cv2
import threading
import subprocess
import time
import re
import os
import sys
from flask import Flask, Response, render_template_string

app = Flask(__name__)
PORT = 5001

# --- カメラ設定 ---
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def start_cloudflared(port):
    """
    cloudflaredトンネルをバックグラウンドで起動し、URLをコンソールに表示する
    """
    # 1. このPythonファイルがある場所のパスを取得
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. 実行ファイルのフルパスを作成 (ファイル名に合わせて修正済み)
    exe_name = "cloudflared-windows-amd64.exe"
    cloudflared_path = os.path.join(base_dir, exe_name)

    # ファイルが存在するか確認
    if not os.path.exists(cloudflared_path):
        print(f"\n[Error] {exe_name} が見つかりません！")
        print(f"探した場所: {cloudflared_path}")
        return

    # コマンド作成
    command = [cloudflared_path, "tunnel", "--url", f"http://localhost:{port}"]

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            encoding='utf-8', # Windowsでの文字化け防止
            errors='ignore'   # 読み込みエラー無視
        )

        print(f"[*] Starting Cloudflare Tunnel using {exe_name}...")
        
        # URLが出力されるまでログを監視
        url_pattern = re.compile(r"https://[-a-zA-Z0-9]+\.trycloudflare\.com")
        
        while True:
            line = process.stderr.readline()
            if not line:
                break
            
            # ログを表示したい場合はコメントアウトを外す
            # print(line.strip()) 

            match = url_pattern.search(line)
            if match:
                public_url = match.group(0)
                print("\n" + "="*50)
                print(f" >> Tunnel Live at: {public_url}")
                print("="*50 + "\n")
                break
                
    except Exception as e:
        print(f"\n[Error] Cloudflaredの起動に失敗しました: {e}\n")

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        
        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.01)

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/")
def index():
    html_content = """
    <html>
    <head><title>Windows Camera Stream</title></head>
    <body>
        <h1>Live Camera Feed</h1>
        <img src="{{ url_for('video_feed') }}" width="640" height="480">
    </body>
    </html>
    """
    return render_template_string(html_content)

if __name__ == "__main__":
    try:
        # トンネル用スレッド開始
        tunnel_thread = threading.Thread(target=start_cloudflared, args=(PORT,), daemon=True)
        tunnel_thread.start()

        # Flaskサーバー起動
        app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
        
    finally:
        if camera.isOpened():
            camera.release()
        print("Camera released.")