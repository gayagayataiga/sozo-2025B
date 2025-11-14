import requests
import json
import time
import urllib3

# 自己署名証明書使用時の警告を無効化
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class EV3Commander:
    """
    ラズパイ上のEV3制御サーバーと通信するためのクライアントクラス
    """

    def __init__(self, raspberry_pi_ip, port=5000, endpoint_path="/api/control_ev3", timeout_sec=10.0):
        """
        EV3Commanderを初期化します。

        Args:
            raspberry_pi_ip (str): 接続先ラズパイのIPアドレス (例: "10.27.75.121")
            port (int, optional): サーバーのポート番号. Defaults to 5000.
            endpoint_path (str, optional): APIのエンドポイントパス. Defaults to "/api/control_ev3".
            timeout_sec (float, optional): リクエストのタイムアウト秒数. Defaults to 10.0.
        """
        self.ip = raspberry_pi_ip
        self.port = port
        self.endpoint_url = f"http://{self.ip}:{self.port}{endpoint_path}"
        self.timeout = timeout_sec
        self.headers = {'Content-Type': 'application/json'}

        print(f"--- EV3Commander初期化 ---")
        print(f" ターゲット: {self.endpoint_url}")
        print(f" タイムアウト: {self.timeout}秒")
        print("-------------------------")

    def send_request(self, data):
        """
        初期化時に設定されたエンドポイントにJSONデータをPOSTリクエストで送信する

        Args:
            data (dict): 送信するデータ (JSONとしてシリアライズされます)

        Returns:
            bool: 送信と応答の確認が成功した場合は True、失敗した場合は False
        """

        try:
            print(f"[{time.strftime('%H:%M:%S')}] ラズパイへPOSTリクエストを送信中...")

            response = requests.post(
                self.endpoint_url,  # 初期化時に設定したURLを使用
                data=json.dumps(data),
                headers=self.headers,
                timeout=self.timeout,
            )

            # 応答の確認
            response.raise_for_status()  # 200番台以外なら例外を発生させる

            print("リクエスト成功！")
            print(f"ステータスコード: {response.status_code}")
            # print("ラズパイからの応答データ:")
            # print(json.dumps(response.json(), indent=2, ensure_ascii=False))
            return True

        except requests.exceptions.RequestException as e:
            print(f"リクエスト失敗: {e}")
            if 'response' in locals() and response is not None:
                print(f"エラー応答内容: {response.text}")
            print(f"ヒント: IP ({self.ip}) が正しいか、サーバーが起動しているか確認してください。")
            return False


# --- リクエスト送信 ---
# classの方がうまくいかないときの保険
def send_request_to_raspberry_pi(data, RASPBERRY_PI_IP):
    # headersはJSON形式を伝えるために必須
    headers = {'Content-Type': 'application/json'}
    ENDPOINT = f"http://{RASPBERRY_PI_IP}:5000/api/control_ev3"

    try:
        print(f"[{time.strftime('%H:%M:%S')}] ラズパイへPOSTリクエストを送信中: {ENDPOINT}")

        response = requests.post(
            ENDPOINT,
            data=json.dumps(data),
            headers=headers,
            timeout=10,  # タイムアウト10秒
        )

        # 応答の確認
        response.raise_for_status()  # 200番台以外なら例外を発生させる

        print("リクエスト成功！")
        print(f"ステータスコード: {response.status_code}")
        print("ラズパイからの応答データ:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"リクエスト失敗: {e}")
        if 'response' in locals() and response is not None:
            print(f"エラー応答内容: {response.text}")
        print("ヒント: ラズパイのIPアドレスとポート5000が正しいか、ラズパイ側サーバーが起動しているか確認してください。")


if __name__ == "__main__":
    EV3_COMMAND_TO_SEND = "A:180:50"
    TEST_IP = "10.27.72.135"  # ここをその日のIPに変えてテストする

    data_to_send = {
        # サーバー側（raspi_ev3_gateway.py）が期待するキー名 "ev3_command" を使用
        "ev3_command": EV3_COMMAND_TO_SEND,
        "client_timestamp": time.time()
    }
    send_request_to_raspberry_pi(data_to_send, TEST_IP)

    print("--- ev3_commander.py (クラス版) 単体テスト実行 ---")

    # --- 単体テスト用の設定 ---

    # クラスの「実体（インスタンス）」を作成
    commander_for_test = EV3Commander(TEST_IP)

    # 作成した実体の「メソッド（send_request）」を呼び出す
    commander_for_test.send_request(data_to_send)
