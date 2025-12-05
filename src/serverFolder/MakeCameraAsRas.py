import cv2
from flask import Flask, Response, render_template_string

# Flask アプリの初期化
app = Flask(__name__)

# --- 変更点: Picamera2 ではなく OpenCV の VideoCapture を使用 ---
# 引数の 0 は「標準カメラ」を意味します。
# 複数のカメラがある場合や認識しない場合は 1, 2 と変更してください。
# cv2.CAP_DSHOW は Windows でのカメラ起動を高速化・安定化させるためのフラグです。
camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# 解像度の設定 (640x480)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

def generate_frames():
    while True:
        # --- 変更点: camera.read() でフレームを取得 ---
        # success: 読み込み成功フラグ (True/False)
        # frame: 画像データ (BGR形式)
        success, frame = camera.read()

        if not success:
            break
        
        # OpenCVの VideoCapture はデフォルトで BGR 形式で取得するため、
        # 色変換 (RGB -> BGR) は不要になりました。

        # フレームをJPEG形式にエンコード
        # ret: エンコード成功フラグ, buffer: エンコード済みデータ
        ret, buffer = cv2.imencode(".jpg", frame)

        if not ret:
            continue

        # バイト列に変換して送信
        frame_bytes = buffer.tobytes()
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# ブラウザで /video_feed にアクセスした時のルート
@app.route("/video_feed")
def video_feed():
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

# ブラウザでルート (/) にアクセスした時のルート
@app.route("/")
def index():
    html_content = """
    <html>
    <head><title>Windows PC Camera Stream</title></head>
    <body>
        <h1>Live Camera Feed (Windows)</h1>
        <img src="{{ url_for('video_feed') }}" width="640" height="480">
    </body>
    </html>
    """
    return render_template_string(html_content)

# サーバー起動
if __name__ == "__main__":
    try:
        # Windows上での開発用として実行
        app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
    finally:
        # アプリ終了時にカメラを開放する
        camera.release()