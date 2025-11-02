import requests
import json
import time
import hashlib
import hmac
import base64
import uuid

# --- 設定項目 ---
# アプリから取得したトークンとクライアントシークレットを貼り付けてください
TOKEN = "7ce17c6269474e2f51f5061ac149d0789bacf842c2460c068de0a24da8ecdef589b8f1d7812ab4bbe73099ffa310fbc0"
SECRET = "ef95b333a2af4bc13913c1c81193706b"
# 参考になった公式github
# https://github.com/OpenWonderLabs/SwitchBotAPI?tab=readme-ov-f
# --- 設定はここまで ---

TARGET_DEVICE_ID = "94A99076E3AE"

# APIのベースURL
api_base = "https://api.switch-bot.com"


def generate_auth_headers(token, secret):
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


def send_command(device_id, command, parameter="default"):
    """指定したデバイスにコマンドを送信する"""
    headers = generate_auth_headers(TOKEN, SECRET)
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
        else:
            print(f"APIエラー: {data.get('message')}")

    except requests.exceptions.RequestException as e:
        print(f"リクエストエラーが発生しました: {e}")
    except json.JSONDecodeError:
        print("APIからの応答がJSON形式ではありませんでした。")
        print(f"応答内容: {response.text}")


def setOnOff(on="On"):
    """
    ライトの電源をON/OFFに設定する

    device_id: デバイスID(TARGET_DEVICE_IDを使用)
    on: "On"または"Off"
    """
    if type(on) is not str:
        print("パラメータは文字列で指定してください。")
        return
    if on not in ["On", "Off", "on", "off"]:
        print("onパラメータは 'On' または 'Off' に設定してください。")
        return
    command = "turnOn" if on == "On" or on == "on" else "turnOff"
    send_command(TARGET_DEVICE_ID, command)


def changeColor(r, g, b):
    """
    ライトの色を設定する

    device_id: デバイスID(TARGET_DEVICE_IDを使用)
    r, g, b: 0から255の範囲で指定
    """
    # r,g,bはint型であることを確認
    if not all(isinstance(color, int) for color in [r, g, b]):
        print("r, g, bの値は整数で指定してください。")
        return
    # r, g, bは0から255の範囲で指定
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    parameter = f"{r}:{g}:{b}"
    send_command(TARGET_DEVICE_ID, "setColor", parameter)


def changeBrightness(brightness_level):
    """
    ライトの明るさを設定する

    device_id: デバイスID(TARGET_DEVICE_IDを使用)
    brightness_level: 0から100の範囲で指定
    """

    # brightness_levelは0から100の範囲で指定（0: 0%, 100: 100%）
    # 0~100の範囲を外れてたら、クリップする
    if not isinstance(brightness_level, int):
        print("brightness_levelの値は整数で指定してください。")
        return
    brightness_level = max(0, min(100, brightness_level))
    send_command(TARGET_DEVICE_ID, "setBrightness", str(brightness_level))


def main():
    """ライトの色と明るさを順番に変更する"""
    # 電源をON
    setOnOff(TARGET_DEVICE_ID, "On")
    time.sleep(3)

    # 色を赤に設定
    changeColor(TARGET_DEVICE_ID, 255, 0, 0)
    time.sleep(3)

    # 色を緑に設定
    changeColor(TARGET_DEVICE_ID, 0, 255, 0)
    time.sleep(3)

    # 色を青に設定
    changeColor(TARGET_DEVICE_ID, 0, 0, 255)
    time.sleep(3)

    # 明るさを10%に設定
    changeBrightness(TARGET_DEVICE_ID, 10)
    time.sleep(3)

    # 明るさを20%に設定
    changeBrightness(TARGET_DEVICE_ID, 20)
    time.sleep(3)

    # 電源をOFF
    setOnOff(TARGET_DEVICE_ID, "Off")


if __name__ == "__main__":
    main()
