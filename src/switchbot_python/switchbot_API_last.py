"""
SwitchBot照明制御の統合モジュール
BLE接続を優先し、失敗した場合はWiFi API経由で制御する

このモジュールはswitchbot_API_command.pyの関数を呼び出して
より簡単に状態別の照明制御を実行できます
"""

from bleak import BleakClient
import asyncio
import sys
import requests
import json
import time
import hashlib
import hmac
import base64
import uuid

# switchbot_API_command.pyから設定をインポート
try:
    from switchbot_API_command import (
        get_awake_settings,      # 覚醒時の設定
        get_connect_settings,    # 接続時（勉強用）の設定
        get_sleeping_settings    # 睡眠検知時の設定
    )
    COMMAND_MODULE_AVAILABLE = True
    print("✅ switchbot_API_command.pyから設定をインポートしました")
except ImportError:
    COMMAND_MODULE_AVAILABLE = False
    print("⚠️  switchbot_API_command.pyが見つかりません。従来の方法で動作します。")

# --- BLE設定 ---
LIGHT_MAC_ADDRESS = "94:A9:90:76:E3:AE"
CHARACTERISTIC_UUID = "cba20002-224d-11e6-9fb8-0002a5d5c51b"

# --- WiFi API設定 ---
TOKEN = "7ce17c6269474e2f51f5061ac149d0789bacf842c2460c068de0a24da8ecdef589b8f1d7812ab4bbe73099ffa310fbc0"
SECRET = "ef95b333a2af4bc13913c1c81193706b"
TARGET_DEVICE_ID = "94A99076E3AE"
API_BASE = "https://api.switch-bot.com"

# --- BLEコマンド ---
COMMAND_ON_BLE = bytes([0x57, 0x0F, 0x20, 0x01, 0x01])
COMMAND_OFF_BLE = bytes([0x57, 0x0F, 0x20, 0x01, 0x02])
COMMAND_BASE_BLE = bytes([0x57, 0x0F, 0x20, 0x01, 0x12])

# --- WiFi API認証ヘッダー生成 ---
def generate_auth_headers(token, secret):
    """SwitchBot APIの認証ヘッダーを生成する"""
    nonce = str(uuid.uuid4())
    t = int(round(time.time() * 1000))
    string_to_sign = f'{token}{t}{nonce}'

    string_to_sign_bytes = string_to_sign.encode('utf-8')
    secret_bytes = secret.encode('utf-8')

    sign_raw = hmac.new(secret_bytes, msg=string_to_sign_bytes,
                        digestmod=hashlib.sha256).digest()
    sign = base64.b64encode(sign_raw).decode('utf-8')

    headers = {
        'Authorization': token,
        'Content-Type': 'application/json; charset=utf8',
        't': str(t),
        'sign': sign,
        'nonce': nonce
    }
    return headers


# --- WiFi API制御関数 ---
def send_command_wifi(command, parameter="default"):
    """WiFi API経由でコマンドを送信する"""
    headers = generate_auth_headers(TOKEN, SECRET)
    url = f"{API_BASE}/v1.1/devices/{TARGET_DEVICE_ID}/commands"

    payload = {
        "command": command,
        "parameter": str(parameter),
        "commandType": "command"
    }

    try:
        print(f"🌐 WiFi API: コマンド '{command}' を送信中...")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get('statusCode') == 100:
            print("✅ WiFi API: コマンド成功")
            return True
        else:
            print(f"❌ WiFi API エラー: {data.get('message')}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ WiFi API リクエストエラー: {e}")
        return False
    except json.JSONDecodeError:
        print("❌ WiFi API: 応答がJSON形式ではありません")
        return False


# --- BLE制御関数 ---
async def control_switchbot_light_ble(command: bytes):
    """
    BLE経由でSwitchBotライトを制御する
    成功時はTrue、失敗時はFalseを返す
    """
    print(f"📡 BLE: {LIGHT_MAC_ADDRESS} に接続中...")
    try:
        async with BleakClient(LIGHT_MAC_ADDRESS, timeout=10.0) as client:
            if client.is_connected:
                print("✅ BLE: 接続成功、コマンド送信中...")
                await client.write_gatt_char(CHARACTERISTIC_UUID, command, response=False)
                print("✅ BLE: コマンド送信完了")
                return True
            else:
                print("❌ BLE: 接続失敗")
                return False

    except Exception as e:
        print(f"❌ BLE エラー: {e}")
        return False


async def set_light_color_brightness_ble(brightness: int, r: int, g: int, b: int):
    """
    BLE経由で輝度と色を設定する
    """
    brightness_byte = max(0, min(100, brightness))
    command = COMMAND_BASE_BLE + bytes([brightness_byte, r, g, b])
    return await control_switchbot_light_ble(command)


# --- 統合制御関数（BLE優先、失敗時はWiFi API） ---
async def control_light_with_fallback(condition: str):
    """
    BLE接続を試み、失敗した場合はWiFi APIにフォールバックする

    Args:
        condition: 'on', 'off', 'study', 'wake' のいずれか
    """
    print(f"\n{'='*60}")
    print(f"[照明制御] 条件: '{condition}'")
    print(f"{'='*60}")

    ble_success = False

    if condition == "on":
        print("--- 💡 ON: 照度100%, 白色 ---")
        # BLEを試す
        ble_success = await control_switchbot_light_ble(COMMAND_ON_BLE)
        if ble_success:
            await asyncio.sleep(0.5)
            ble_success = await set_light_color_brightness_ble(100, 255, 255, 255)

        # BLE失敗時はWiFi APIを使用
        if not ble_success:
            print("\n⚠️  BLE失敗、WiFi APIにフォールバック...")
            send_command_wifi("turnOn")
            time.sleep(0.5)
            send_command_wifi("setColor", "255:255:255")
            time.sleep(0.5)
            send_command_wifi("setBrightness", "100")

    elif condition == "off":
        print("--- 🔌 OFF: 消灯 ---")
        # BLEを試す
        ble_success = await control_switchbot_light_ble(COMMAND_OFF_BLE)

        # BLE失敗時はWiFi APIを使用
        if not ble_success:
            print("\n⚠️  BLE失敗、WiFi APIにフォールバック...")
            send_command_wifi("turnOff")

    elif condition == "study":
        print("--- 📚 STUDY: 照度70%, 黄色味のある白色 ---")
        # BLEを試す
        ble_success = await control_switchbot_light_ble(COMMAND_ON_BLE)
        if ble_success:
            await asyncio.sleep(0.5)
            ble_success = await set_light_color_brightness_ble(70, 255, 255, 200)

        # BLE失敗時はWiFi APIを使用
        if not ble_success:
            print("\n⚠️  BLE失敗、WiFi APIにフォールバック...")
            send_command_wifi("turnOn")
            time.sleep(0.5)
            send_command_wifi("setColor", "255:255:200")
            time.sleep(0.5)
            send_command_wifi("setBrightness", "70")

    elif condition == "wake":
        print("--- ☀️ WAKE: 照度100%, 赤色 ---")
        # BLEを試す
        ble_success = await control_switchbot_light_ble(COMMAND_ON_BLE)
        if ble_success:
            await asyncio.sleep(0.5)
            ble_success = await set_light_color_brightness_ble(100, 255, 0, 0)

        # BLE失敗時はWiFi APIを使用
        if not ble_success:
            print("\n⚠️  BLE失敗、WiFi APIにフォールバック...")
            send_command_wifi("turnOn")
            time.sleep(0.5)
            send_command_wifi("setColor", "255:0:0")
            time.sleep(0.5)
            send_command_wifi("setBrightness", "100")

    else:
        print(f"⚠️  未知の条件: '{condition}'")
        print("使用可能な条件: 'on', 'off', 'study', 'wake'")
        return

    print(f"{'='*60}")
    print("✅ 制御完了")
    print(f"{'='*60}\n")


# --- カスタム色・明るさ設定関数 ---
async def set_custom_light(brightness: int, r: int, g: int, b: int):
    """
    カスタムの明るさと色でライトを設定する（BLE優先、フォールバック付き）

    Args:
        brightness: 0-100
        r: 0-255
        g: 0-255
        b: 0-255
    """
    print(f"\n{'='*60}")
    print(f"[カスタム照明] 明るさ: {brightness}%, RGB: ({r}, {g}, {b})")
    print(f"{'='*60}")

    # BLEを試す
    ble_success = await control_switchbot_light_ble(COMMAND_ON_BLE)
    if ble_success:
        await asyncio.sleep(0.5)
        ble_success = await set_light_color_brightness_ble(brightness, r, g, b)

    # BLE失敗時はWiFi APIを使用
    if not ble_success:
        print("\n⚠️  BLE失敗、WiFi APIにフォールバック...")
        send_command_wifi("turnOn")
        time.sleep(0.5)
        send_command_wifi("setColor", f"{r}:{g}:{b}")
        time.sleep(0.5)
        send_command_wifi("setBrightness", str(brightness))

    print(f"{'='*60}")
    print("✅ カスタム照明設定完了")
    print(f"{'='*60}\n")


# --- デモ実行関数 ---
async def demo_sequence():
    """
    引数なしで実行された場合のデモシーケンス
    全てのパターンを順番に試す

    switchbot_API_command.pyが利用可能な場合はそちらの関数を使用
    """
    print("\n" + "="*60)
    print("🎬 SwitchBot照明制御デモを開始します")
    print("="*60 + "\n")

    # switchbot_API_command.pyの設定を使用する場合
    if COMMAND_MODULE_AVAILABLE:
        print("📦 switchbot_API_command.pyの設定を使用します\n")

        demos = [
            ("connect", get_connect_settings()),
            ("awake", get_awake_settings()),
            ("sleeping", get_sleeping_settings()),
            ("off", None)
        ]

        for i, (mode, settings) in enumerate(demos, 1):
            if mode == "off":
                print(f"\n[{i}/{len(demos)}] 消灯モード")
                print("-" * 60)
                await control_light_with_fallback("off")
            else:
                print(f"\n[{i}/{len(demos)}] {settings['description']}")
                print("-" * 60)
                # 設定を使ってカスタム制御
                await set_custom_light(
                    settings['brightness'],
                    settings['r'],
                    settings['g'],
                    settings['b']
                )

            # 最後以外は待機
            if i < len(demos):
                print(f"⏳ 次のデモまで3秒待機...")
                await asyncio.sleep(3)

    # 従来の方法を使用する場合
    else:
        print("⚙️  従来の制御方法を使用します\n")

        demos = [
            ("study", "📚 勉強モード（照度70%、黄色味のある白色）"),
            ("wake", "☀️ 起床モード（照度100%、赤色）"),
            ("on", "💡 ONモード（照度100%、白色）"),
            ("off", "🔌 OFFモード（消灯）")
        ]

        for i, (mode, description) in enumerate(demos, 1):
            print(f"\n[{i}/{len(demos)}] {description}")
            print("-" * 60)
            await control_light_with_fallback(mode)

            # 最後以外は待機
            if i < len(demos):
                print(f"\n⏳ 次のデモまで3秒待機...")
                await asyncio.sleep(3)

    print("\n" + "="*60)
    print("✅ デモシーケンス完了")
    print("="*60 + "\n")


# --- メイン実行部分 ---
if __name__ == "__main__":
    # 引数なしで実行された場合はデモモード
    if len(sys.argv) < 2:
        print("\n💡 引数なしで実行されました。デモモードを開始します。")
        print("（特定のモードで実行する場合は引数を指定してください）")
        print("\n使用法:")
        print("  python switchbot_API_last.py [on|off|study|wake]")
        print("  python switchbot_API_last.py custom <brightness> <r> <g> <b>")
        print("  例: python switchbot_API_last.py custom 80 255 200 150")
        print()

        # ユーザーに確認
        try:
            response = input("デモを開始しますか？ (y/n): ").lower().strip()
            if response == 'y' or response == 'yes':
                asyncio.run(demo_sequence())
            else:
                print("キャンセルしました。")
        except KeyboardInterrupt:
            print("\n\nキャンセルしました。")
        sys.exit(0)

    command = sys.argv[1].lower()

    # カスタムモード
    if command == "custom":
        if len(sys.argv) != 6:
            print("エラー: カスタムモードには brightness, r, g, b の4つの値が必要です")
            print("例: python switchbot_API_last.py custom 80 255 200 150")
            sys.exit(1)

        try:
            brightness = int(sys.argv[2])
            r = int(sys.argv[3])
            g = int(sys.argv[4])
            b = int(sys.argv[5])

            asyncio.run(set_custom_light(brightness, r, g, b))
        except ValueError:
            print("エラー: brightness, r, g, b は整数で指定してください")
            sys.exit(1)

    # プリセットモード
    elif command in ["on", "off", "study", "wake"]:
        asyncio.run(control_light_with_fallback(command))

    else:
        print(f"エラー: 未知のコマンド '{command}'")
        print("使用可能なコマンド: on, off, study, wake, custom")
        sys.exit(1)
