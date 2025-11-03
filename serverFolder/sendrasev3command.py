import requests
import json
import time
import urllib3  # HTTPSの警告を非表示にするためにインポート（verify=Falseを使う場合）

# 自己署名証明書使用時の警告を無効化
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 設定情報 ---
# 1. ラズパイのIPアドレス
RASPBERRY_PI_IP = "10.27.75.121"

# 2. ラズパイサーバーのポートとエンドポイント
# ラズパイ側コードの定義に合わせて、HTTPとポート5000、エンドポイント '/api/control_ev3' を使用
ENDPOINT = f"http://{RASPBERRY_PI_IP}:5000/api/control_ev3"

# 3. 送信するEV3コマンドデータ (ラズパイ側のサーバーが期待する形式に合わせる)
# サーバー側は JSONペイロード内の "ev3_command" キーを期待しています。
# ここでは例として、モーターAを90度、速度50で動かすコマンドを直接文字列として定義します。
EV3_COMMAND_TO_SEND = "A:90:50"

data_to_send = {
    # サーバー側（raspi_ev3_gateway.py）が期待するキー名 "ev3_command" を使用
    "ev3_command": EV3_COMMAND_TO_SEND,
    "client_timestamp": time.time()
}
# ----------------


# --- リクエスト送信 ---
def send_request_to_raspberry_pi(data):
    # headersはJSON形式を伝えるために必須
    headers = {'Content-Type': 'application/json'}

    try:
        print(f"[{time.strftime('%H:%M:%S')}] ラズパイへPOSTリクエストを送信中: {ENDPOINT}")

        response = requests.post(
            ENDPOINT,
            data=json.dumps(data),
            headers=headers,
            # HTTPSは使用しないため 'verify' は不要ですが、もし使用する場合は True にしてください
            # verify=False は不要（HTTP接続のため）
        )

        # 応答の確認
        response.raise_for_status()  # 200番台以外なら例外を発生させる

        print("✅ リクエスト成功！")
        print(f"ステータスコード: {response.status_code}")
        print("ラズパイからの応答データ:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"❌ リクエスト失敗: {e}")
        if 'response' in locals() and response is not None:
            print(f"エラー応答内容: {response.text}")
        print("ヒント: ラズパイのIPアドレスとポート5000が正しいか、ラズパイ側サーバーが起動しているか確認してください。")


if __name__ == "__main__":
    send_request_to_raspberry_pi(data_to_send)
