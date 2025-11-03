import requests
import json
import time
import hashlib
import hmac
import base64
import uuid

# --- 設定項目 ---
TOKEN = "7ce17c6269474e2f51f5061ac149d0789bacf842c2460c068de0a24da8ecdef589b8f1d7812ab4bbe73099ffa310fbc0"
SECRET = "ef95b333a2af4bc13913c1c81193706b"
# 参考になった公式github
# https://github.com/OpenWonderLabs/SwitchBotAPI?tab=readme-ov-f

TARGET_DEVICE_ID = "94A99076E3AE"

# APIのベースURL
api_base = "https://api.switch-bot.com"


def _generate_auth_headers(token, secret):
    """SwitchBot APIの認証ヘッダーを生成する"""
    nonce = str(uuid.uuid4())
    t = int(round(time.time() * 1000))
    string_to_sign = f'{token}{t}{nonce}'

    # 文字列とシークレットをバイト型に変換
    string_to_sign_bytes = string_to_sign.encode('utf-8')
    secret_bytes = secret.encode('utf-8')

    # HMAC-SHA256で署名を生成
    sign_raw = hmac.new(secret_bytes, msg=string_to_sign_bytes,
                        digestmod=hashlib.sha256).digest()

    # Base64でエンコード
    sign = base64.b64encode(sign_raw).decode('utf-8')

    # ヘッダーを構築
    headers = {
        'Authorization': token,
        'Content-Type': 'application/json; charset=utf8',
        't': str(t),
        'sign': sign,
        'nonce': nonce
    }
    return headers


def _send_command(token, secret, device_id, command, parameter="default"):
    """指定したデバイスにコマンドを送信する"""
    headers = _generate_auth_headers(token, secret)
    url = f"{api_base}/v1.1/devices/{device_id}/commands"

    payload = {
        "command": command,
        "parameter": str(parameter),
        "commandType": "command"
    }

    try:
        print(f"コマンド '{command}' を送信中...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        data = response.json()
        if data.get('statusCode') == 100:
            print("コマンド成功！")
            return True
        else:
            print(f"APIエラー: {data.get('message')}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"リクエストエラーが発生しました: {e}")
        return False
    except json.JSONDecodeError:
        print("APIからの応答がJSON形式ではありませんでした。")
        print(f"応答内容: {response.text}")
        return False


def _send_get_request(endpoint_url, token, secret):
    """
    APIにGETリクエストを送信する共通関数
    成功時はレスポンスの 'body' を、失敗時は None を返す
    """
    headers = _generate_auth_headers(token, secret)
    try:
        response = requests.get(endpoint_url, headers=headers)
        response.raise_for_status()  # HTTPエラーがあれば例外発生
        data = response.json()

        if data.get('statusCode') == 100:
            return data.get('body')
        else:
            print(f"APIエラー (GET): {data.get('message')}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"リクエストエラーが発生しました: {e}")
        return None
    except json.JSONDecodeError:
        print("APIからの応答がJSON形式ではありませんでした。")
        print(f"応答内容: {response.text}")
        return None


def check_api_connection(token, secret):
    """
    API認証情報（Token, Secret）が正しいかを確認する
    デバイス一覧取得を試行し、成功すれば True を返す
    """
    print("APIへの接続確認中...")
    url = f"{api_base}/v1.1/devices"
    body = _send_get_request(url, token, secret)

    if body is not None:
        print("API認証成功。")
        return True
    else:
        print("API認証失敗。")
        return False


class SwitchBotLight:
    """
    一台のSwitchBotライトデバイスを管理するクラス。
    状態（キャッシュ）を内部に保持し、コマンド送信と同期を行います。
    """

    def __init__(self, device_id, token, secret):
        """
        ライトのオブジェクトを作成（初期化）します。

        Args:
            device_id (str): 対象デバイスのID
            token (str): APIトークン
            secret (str): APIシークレット
        """
        # 認証情報とIDを「自分専用の変数(self)」として保持
        self.device_id = device_id
        self.token = token
        self.secret = secret

        # 内部キャッシュの初期値
        self.on_off = "off"
        self.r = 0
        self.g = 0
        self.b = 0
        self.brightness = 0
        self.mode = "api"

        print(f"--- デバイス {self.device_id} の初期化を開始 ---")
        # 起動時に一度、APIから最新の状態を取得してキャッシュを同期
        if not self.sync_from_api():
            # API同期に失敗した場合、BLEモードに切り替え
            print("API同期に失敗したため、BLEモードにフォールバックします。")
            self.mode = "ble"
        else:
            print("API同期に成功しました。")

    def sync_from_api(self):
        """
        デバイスの現在の状態をAPIから取得し、
        内部のキャッシュ（self.on_offなど）を更新します。
        """
        print(f"APIから {self.device_id} のステータスを同期中...")
        url = f"{api_base}/v1.1/devices/{self.device_id}/status"

        # 内部関数を呼び出し、自分のトークン等を渡す
        body = _send_get_request(url, self.token, self.secret)

        if body:
            print("ステータス取得成功。内部キャッシュを更新します。")
            try:
                # APIの戻り値をパースして、selfの変数に格納
                self.on_off = body.get('power', 'off')
                self.brightness = body.get('brightness', 0)

                # 色情報のパース (例: "255:0:0")
                r_str, g_str, b_str = body.get('color', '0:0:0').split(':')
                self.r = int(r_str)
                self.g = int(g_str)
                self.b = int(b_str)

                print(f"同期後の状態: {self.get_status()}")
                return True
            except Exception as e:
                print(f"ステータスのパースに失敗しました: {e}")
                return False
        else:
            print("ステータス取得失敗。キャッシュは更新されません。")
            self.mode = "ble"
            print("モードを 'ble' に切り替えました。")
            return False

    def get_status(self):
        """
        現在のキャッシュ（内部状態）を辞書で返します。
        """
        return {
            "mode": self.mode,
            "OnOff": self.on_off,
            "r": self.r,
            "g": self.g,
            "b": self.b,
            "brightness": self.brightness
        }

    def _execute_command(self, command, parameter, on_success_action):
        """
        コマンド実行の共通ロジック
        (モード判定、API/BLE実行、成功時のキャッシュ更新、失敗時のモード切替)

        Args:
            command (str): "turnOn", "setColor" などのコマンド名
            parameter (str): "default", "255:0:0" などのパラメータ
            on_success_action (function): 成功した場合にのみ実行するコールバック関数
        """
        success = False

        if self.mode == "api":
            print(f"APIモードで {command} を実行します。")
            success = _send_command(
                self.token, self.secret, self.device_id, command, parameter
            )

        elif self.mode == "ble":
            print(f"BLEモードで {command} を実行します (現在未実装)。")
            # --- ここにBLE送信コードを実装 ---
            # success = _send_ble_command(...)
            success = True  # ダミーで成功したことにする

        # --- 共通の判定ロジック ---
        if success:
            # 成功したら、引数で渡された「キャッシュ更新処理」を実行
            on_success_action()
            print(f"コマンド成功。キャッシュ更新後の状態: {self.get_status()}")
        else:
            # 失敗したら、モードを切り替える
            if self.mode == "api":
                print(f"APIコマンド ({command}) が失敗しました。BLEモードに切り替えます。")
                self.mode = "ble"
            else:
                # BLEも失敗した場合、APIモードに戻してみる（再試行のため）
                print(f"BLEコマンド ({command}) が失敗しました。APIモードに戻します。")
                self.mode = "api"

    def set_on_off(self, on="On"):
        """
        ライトの電源をON/OFFに設定します。
        成功した場合のみ、内部キャッシュを更新します。
        """
        if type(on) is not str:
            print("パラメータは文字列で指定してください。")
            return
        on_lower = on.lower()
        if on_lower not in ["on", "off"]:
            print("onパラメータは 'On' または 'Off' に設定してください。")
            return

        command = "turnOn" if on_lower == "on" else "turnOff"
        parameter = "default"

        def on_success_action():
            self.on_off = on_lower

        # 共通メソッドに丸投げ
        self._execute_command(command, parameter, on_success_action)

    def change_color(self, r, g, b):
        """
        ライトの色を設定します。
        成功した場合のみ、内部キャッシュを更新します。
        """
        if not all(isinstance(color, int) for color in [r, g, b]):
            print("r, g, bの値は整数で指定してください。")
            return
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        parameter = f"{r}:{g}:{b}"
        command = "setColor"

        def on_success_action():
            self.r = r
            self.g = g
            self.b = b

        self._execute_command(command, parameter, on_success_action)

    def change_brightness(self, brightness_level):
        """
        ライトの明るさを設定します。
        成功した場合のみ、内部キャッシュを更新します。
        """
        if not isinstance(brightness_level, int):
            print("brightness_levelの値は整数で指定してください。")
            return
        brightness_level = max(0, min(100, brightness_level))

        command = "setBrightness"
        parameter = str(brightness_level)

        def on_success_action():
            self.brightness = brightness_level

        self._execute_command(command, parameter, on_success_action)


# --- このファイルが直接実行された場合のデモ ---
def main():
    """
    クラスを使った場合のデモ動作
    """

    # API自体の接続確認 (クラスの外の関数を呼ぶ)
    #    (TOKEN, SECRETはモジュール上部のデフォルト値を使用)
    if not check_api_connection(TOKEN, SECRET):
        print("APIに接続できません。TokenやSecretを確認してください。")
        return

    #  SwitchBotLight クラスの「インスタンス（実体）」を作成
    #    TARGET_DEVICE_ID と TOKEN, SECRET を渡す
    print("\n=== ライトのインスタンスを作成します ===")
    my_light = SwitchBotLight(TARGET_DEVICE_ID, TOKEN, SECRET)

    print(f"\n初期状態 (キャッシュから): {my_light.get_status()}")

    # --- デモ動作 ---
    print("\n=== デモ動作開始 ===")

    # グローバル関数ではなく、`my_light` オブジェクトのメソッドを呼ぶ
    my_light.set_on_off("On")
    time.sleep(3)

    my_light.change_color(255, 0, 0)
    time.sleep(3)

    # キャッシュ（API通信なし）で現在の状態を確認
    print(f"現在の状態 (キャッシュ): {my_light.get_status()}")

    my_light.change_color(0, 255, 0)
    time.sleep(3)

    my_light.change_brightness(20)
    time.sleep(3)

    my_light.set_on_off("Off")
    time.sleep(1)

    print(f"\n最終状態 (キャッシュ): {my_light.get_status()}")
    print("=== デモ動作終了 ===")


if __name__ == "__main__":
    main()
