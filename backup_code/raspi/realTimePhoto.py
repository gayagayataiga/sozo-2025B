import cv2
import time
import threading
from flask import Flask, Response, render_template_string
from picamera2 import Picamera2

# Flask アプリの初期化
app = Flask(__name__)

# Picamera2 の初期化
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

# グローバル変数で最新フレームを保持
latest_frame = None
frame_lock = threading.Lock()
frame_available = threading.Event()

# カメラから連続的にフレームを取得するスレッド
def capture_thread():
    global latest_frame
    while True:
        try:
            # カメラからフレームを1枚取得
            frame = picam2.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            with frame_lock:
                latest_frame = frame.copy()
                frame_available.set()
            
            time.sleep(0.033)
        except Exception as e:
            print(f"Capture error: {e}")
            time.sleep(0.1)

def generate_frames():
    frame_available.wait()
    
    while True:
        with frame_lock:
            if latest_frame is None:
                continue
            frame = latest_frame.copy()
        
        (flag, encodedImage) = cv2.imencode(".jpg", frame)
        
        if not flag:
            continue
        
        # エンコードされた画像をバイト列として送信 (MJPEG形式)
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
              bytearray(encodedImage) + b'\r\n')
        
        time.sleep(0.033)

@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/")
def index():
    html_content = """
    <html>
    <head><title>Raspberry Pi Camera Stream</title></head>
    <body>
        <h1>Live Camera Feed (Raw)</h1>
        <img src="{{ url_for('video_feed') }}" width="640" height="480">
    </body>
    </html>
    """
    return render_template_string(html_content)

if __name__ == "__main__":
    capture_thread_instance = threading.Thread(target=capture_thread, daemon=True)
    capture_thread_instance.start()
    
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
    # cloudflared tunnel --url http://localhost:5001