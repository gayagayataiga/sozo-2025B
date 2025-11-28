from flask import Flask, request, jsonify
import os
from werkzeug.utils import secure_filename
import datetime

# --- 設定項目 ---
# 受信した画像を保存するフォルダ
OUTPUT_DIR = "./received_images/"
# ----------------

# Flaskアプリケーションの準備
app = Flask(__name__)

# Raspberry Piからの画像アップロードを受け付けるエンドポイント


@app.route('/upload_image', methods=['POST'])
def handle_image_upload():
    print("\n Raspberry Piからリクエストを受信しました！")

    # リクエストに'image_file'というキーでファイルが含まれているかチェック
    if 'image_file' not in request.files:
        print(" エラー: リクエストに 'image_file' が含まれていません。")
        return jsonify({"status": "Error", "message": "Image file not found"}), 400

    image_file = request.files['image_file']

    # ファイル名が空でないことを確認
    if image_file.filename == '':
        print(" エラー: ファイルが選択されていません。")
        return jsonify({"status": "Error", "message": "No selected file"}), 400

    # 安全なファイル名に変換
    filename = secure_filename(image_file.filename)

    try:
        # # 保存先フォルダがなければ作成
        # os.makedirs(OUTPUT_DIR, exist_ok=True)

        # 1. 現在の日時を取得
        now = datetime.datetime.now()
        # 2. ファイル名として使える形式の文字列に変換
        timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S")

        # 3. 元のファイルの拡張子を取得
        original_filename = secure_filename(image_file.filename)
        _, extension = os.path.splitext(original_filename)

        # 4. 新しいファイル名を生成 (例: 2025-10-10_14-02-30.jpg)
        new_filename = f"{timestamp_str}{extension}"

        # ファイルを保存するパスを生成
        save_path = os.path.join(OUTPUT_DIR, new_filename)

        # 画像ファイルを指定したパスに保存
        image_file.save(save_path)

        print(f" 画像 '{filename}' を '{save_path}' に保存しました。")

        # Raspberry Piに成功の応答を返す
        return jsonify({"status": "OK", "message": f"File '{filename}' saved successfully."})

    except Exception as e:
        print(f" ファイル保存中にエラーが発生しました: {e}")
        return jsonify({"status": "Error", "message": "Failed to save file on server"}), 500


if __name__ == '__main__':
    print(" 画像受信サーバーを起動します... (Ctrl+Cで停止)")
    print(f"Raspberry Piからの画像データ受信を http://<YOUR_IP>:5000/upload_image で待ち受けます。")
    # 同じネットワーク上の他のデバイスからアクセスできるように host='0.0.0.0' を指定
    app.run(host='0.0.0.0', port=5000)
