# wifi mac: 94:A9:90:76:E3:AC
# ble mac: 94:A9:90:76:E3:AE
import asyncio
from bleak import BleakClient

# --- 設定 ---
# あなたのSwitchBotライトのMACアドレスに置き換えてください
LIGHT_MAC_ADDRESS = "94:A9:90:76:E3:AE"

# SwitchBot Color BulbのGATT通信用UUID
CHARACTERISTIC_UUID = "cba20002-224d-11e6-9fb8-0002a5d5c51b"

# ライトの操作コマンドバイト列
# 点灯（オン）コマンド: [0x57, 0x01, 0x01]
COMMAND_ON = bytes([0x57, 0x01, 0x01])

# 消灯（オフ）コマンド: [0x57, 0x01, 0x02]
COMMAND_OFF = bytes([0x57, 0x01, 0x02])

# 明るさ100%設定コマンド（例: 0x05は明るさ設定、0x64は100(0x64)）
# COMMAND_BRIGHTNESS_100 = bytes([0x57, 0x05, 0x64])

# 色設定コマンド
# コマンド形式: bytes([0x57, 0x01, r,g,b])
# 赤 (R=255, G=0, B=0)
COMMAND_RED = bytes([0x57, 0x01, 0x09, 255, 0, 0])
# 緑 (R=0, G=255, B=0)
COMMAND_GREEN = bytes([0x57, 0x01, 0x09, 0, 255, 0])
# 青 (R=0, G=0, B=255)
COMMAND_BLUE = bytes([0x57, 0x01, 0x09, 0, 0, 255])


# --- 実行関数 ---
async def control_switchbot_light(mac_address: str, command: bytes, CHARACTERISTIC_UUID: str):
    """
    SwitchBotライトにBLE経由でコマンドを送信する
    """
    print(f"Connecting to {mac_address}...")

    try:
        # BleakClientを使ってデバイスに接続
        async with BleakClient(mac_address, timeout=10.0) as client:
            if client.is_connected:
                print("Connected successfully.")

                # キャラクタリスティックにコマンドを書き込む
                print(f"Writing command: {command.hex()}")
                await client.write_gatt_char(CHARACTERISTIC_UUID, command, response=True)
                print("Command sent. Light should respond.")
            else:
                print("Failed to connect.")

    except Exception as e:
        print(f"An error occurred: {e}")
        # WindowsやLinuxではBLEエラーが起きやすいので、エラーメッセージを出す
        print("💡 エラーが発生した場合、PCのBluetoothがONか、MACアドレスが正しいか確認してください。")


# --- メインシーケンス関数 ---
async def main_sequence():
    """
    ライトを点灯させ、待機後に消灯、さらに待機後に再点灯し、最後に色を変更する一連の動作
    """

    # 1. 初期点灯
    print("--- 1. 初期点灯を実行 ---")
    await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_ON, CHARACTERISTIC_UUID)

    # 2. 1秒待機
    print("\n--- 1秒間待機 ---")
    await asyncio.sleep(1)

    # 3. 消灯
    print("\n--- 3. 消灯を実行 ---")
    await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_OFF, CHARACTERISTIC_UUID)

    # 4. 1秒待機
    print("\n--- 4. 1秒間待機 ---")
    await asyncio.sleep(1)

    # 5. 再点灯
    print("\n--- 5. 再点灯を実行 ---")
    await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_ON, CHARACTERISTIC_UUID)

    # 6. 2秒待機
    print("\n--- 2秒間待機 ---")
    await asyncio.sleep(2)

    # 7. 青色に変更
    print("\n--- 7. 青色に変更を実行 ---")
    await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_BLUE, CHARACTERISTIC_UUID)

    # 8. 緑色に変更
    print("\n--- 8. 緑色に変更を実行 ---")
    await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_GREEN, CHARACTERISTIC_UUID)

    # 9. 消灯 (シーケンスの終了として)
    print("\n--- 9. 消灯を実行 (シーケンス終了) ---")
    await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_OFF, CHARACTERISTIC_UUID)


# --- メイン処理 ---
if __name__ == "__main__":

    # 非同期シーケンス関数を実行
    asyncio.run(main_sequence())
