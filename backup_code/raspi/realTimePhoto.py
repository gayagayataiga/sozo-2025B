import cv2
import time
from flask import Flask, Response, render_template_string
from picamera2 import Picamera2

# Flask アプリの初期化
app = Flask(__name__)

# Picamera2 の初期化
picam2 = Picamera2()
# 解像度を低め(640x480)に設定（処理負荷とネットワーク負荷を下げるため）
config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

# 映像を連続的に生成するジェネレータ関数


def generate_frames():
    while True:
        # カメラからフレームを1枚取得
        frame = picam2.capture_array()

        # --- AI処理はここで行わない ---

        # フレームをJPEG形式にエンコード
        (flag, encodedImage) = cv2.imencode(".jpg", frame)

        # エンコードが成功しなかったらスキップ
        if not flag:
            continue

        # エンコードされた画像をバイト列として送信 (MJPEG形式)
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
               bytearray(encodedImage) + b'\r\n')

# ブラウザで /video_feed にアクセスした時のルート


@app.route("/video_feed")
def video_feed():
    # generate_frames関数を呼び出し、レスポンスとしてストリームを返す
    return Response(generate_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

# ブラウザでルート (/) にアクセスした時のルート


@app.route("/")
def index():
    # /video_feed を表示するだけのシンプルなHTMLを返す
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


# スクリプトが直接実行されたらサーバーを起動
if __name__ == "__main__":
    # '0.0.0.0' を指定することで、ローカルネットワーク内の他のPCからアクセス可能になる
    app.run(host="0.0.0.0", port=5001, debug=False,
            threaded=True)  # debug=True は負荷が上がるので False に変更
