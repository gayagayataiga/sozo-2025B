import cv2
import time
from flask import Flask, Response, render_template_string

# Flask アプリの初期化
app = Flask(__name__)

# OpenCV を使ってカメラを初期化 (0 はデフォルトのカメラを意味します)
# USBカメラが複数接続されている場合、0, 1, 2... と試してください
cap = cv2.VideoCapture(0)

# 解像度を低め(640x480)に設定
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# カメラが正常に開いたか確認
if not cap.isOpened():
    print("エラー: カメラを開けませんでした。")
    exit()

# 映像を連続的に生成するジェネレータ関数


def generate_frames():
    while True:
        # カメラからフレームを1枚取得
        success, frame = cap.read()  # success (True/False) と frame (画像データ) が返る

        if not success:
            print("フレームの読み取りに失敗しました。")
            break
        else:
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
    <head><title>Windows Camera Stream</title></head>
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
    app.run(host="0.0.0.0", port=5000, debug=False,
            threaded=True)
