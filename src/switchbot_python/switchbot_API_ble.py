import asyncio
from bleak import BleakClient

# --- 1. 定数・設定の定義 ---
# 他のファイルから import LIGHT_MAC_ADDRESS 等で参照できるようにします
LIGHT_MAC_ADDRESS = "94:A9:90:76:E3:AE"
CHARACTERISTIC_UUID = "cba20002-224d-11e6-9fb8-0002a5d5c51b"

# 操作コマンド (外部から参照しやすい名前に変更)
COMMAND_ON_BLE = bytes([0x57, 0x0F, 0x47, 0x01, 0x01])
COMMAND_OFF_BLE = bytes([0x57, 0x0F, 0x47, 0x01, 0x02])


# --- 2. 汎用的な送信関数 ---
async def control_switchbot_light_ble(command: bytes, mac_address: str = LIGHT_MAC_ADDRESS):
    """
    指定されたバイト列コマンドをSwitchBotライトに送信する関数
    デフォルト引数で MACアドレスを指定しているので、呼び出し時はコマンドだけでOKです。
    """
    # 接続確認用のログ（必要に応じてコメントアウトしてください）
    # print(f"[BLE] Connecting to {mac_address}...")

    try:
        async with BleakClient(mac_address, timeout=5.0) as client:
            if client.is_connected:
                # print("[BLE] Connected.")
                
                # コマンド送信
                await client.write_gatt_char(CHARACTERISTIC_UUID, command, response=False)
                print(f"[BLE] Command sent: {command.hex()}")
                return True
            else:
                print("[BLE] Failed to connect.")
                return False
    except Exception as e:
        print(f"[BLE Error] {e}")
        return False


# --- 3. 色と明るさを指定して送信する関数 ---
async def set_light_color_brightness_ble(brightness: int, r: int, g: int, b: int, mac_address: str = LIGHT_MAC_ADDRESS):
    """
    RGB(0-255)と明るさ(0-100)を指定してライトを制御する関数
    コマンド列を自動生成して control_switchbot_light_ble に渡します。
    """
    # 値の範囲制限 (バリデーション)
    brightness = max(0, min(100, brightness))
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))

    # コマンド生成: [0x57, 0x0F, 0x47, 0x01, 0x12, Brightness, R, G, B]
    command = bytes([0x57, 0x0F, 0x47, 0x01, 0x12, brightness, r, g, b])
    
    # 送信
    await control_switchbot_light_ble(command, mac_address)


# --- 4. 単体テスト用 (このファイルを直接実行した時だけ動く) ---
async def _main_test_sequence():
    print("--- テスト開始 ---")
    
    print("ON")
    await control_switchbot_light_ble(COMMAND_ON_BLE)
    await asyncio.sleep(2)
    
    print("赤 (明るさ50%)")
    await set_light_color_brightness_ble(50, 255, 0, 0)
    await asyncio.sleep(2)
    
    print("青 (明るさ100%)")
    await set_light_color_brightness_ble(100, 0, 0, 255)
    await asyncio.sleep(2)
    
    print("OFF")
    await control_switchbot_light_ble(COMMAND_OFF_BLE)

if __name__ == "__main__":
    # このファイルを直接 'python switchbot_API_ble.py' で実行した時のみここが動く
    # import された時は動きません
    asyncio.run(_main_test_sequence())