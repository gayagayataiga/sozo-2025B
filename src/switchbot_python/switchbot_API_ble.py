from bleak import BleakClient
import asyncio


# --- 設定 ---
LIGHT_MAC_ADDRESS = "94:A9:90:76:E3:AE"

# 2. SwitchBot Color BulbのGATT通信用UUID (これが正しい)
CHARACTERISTIC_UUID = "cba20002-224d-11e6-9fb8-0002a5d5c51b"

# 3. ライトの操作コマンドバイト列
# オンコマンド: REQ 0x570f470101
COMMAND_ON = bytes([0x57, 0x0F, 0x47, 0x01, 0x01])

# オフコマンド: REQ 0x570f470102
COMMAND_OFF = bytes([0x57, 0x0F, 0x47, 0x01, 0x02])

# 4. 色設定コマンド (新しい拡張コマンド形式)
# 青色 100% (Type 0x12: Lvl + RGB 変更)
# コマンド: [0x57, 0x0F, 0x47, 0x01, 0x12, Brightness, R, G, B]
COMMAND_BLUE = bytes([0x57, 0x0F, 0x47, 0x01, 0x12, 0x64, 0x00, 0x00, 0xFF])

# 緑色 100% (R=0, G=255, B=0)
COMMAND_GREEN = bytes([0x57, 0x0F, 0x47, 0x01, 0x12, 0x64, 0x00, 0xFF, 0x00])

# 赤色 100% (R=255, G=0, B=0)
COMMAND_RED = bytes([0x57, 0x0F, 0x47, 0x01, 0x12, 0x64, 0xFF, 0x00, 0x00])


# --- 実行関数 (変更なし) ---
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
                # ドキュメントの仕様では応答 (response=True) は必須ではないが、念のため残す
                await client.write_gatt_char(CHARACTERISTIC_UUID, command, response=False)
                print("Command sent. Light should respond.")
            else:
                print("Failed to connect.")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("💡 エラーが発生した場合、PCのBluetoothがONか、MACアドレスが正しいか確認してください。")


# --- メインシーケンス関数 (色変更を追加) ---
async def main_sequence():

    # 1. 初期点灯 (コマンド変更)
    print("--- 1. 初期点灯を実行 ---")
    await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_ON, CHARACTERISTIC_UUID)
    await asyncio.sleep(2)

    # 2. 青色に変更 (コマンド変更)
    print("\n--- 2. 青色に変更を実行 (新形式) ---")
    await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_BLUE, CHARACTERISTIC_UUID)
    await asyncio.sleep(2)

    # 3. 緑色に変更 (コマンド変更)
    print("\n--- 3. 緑色に変更を実行 (新形式) ---")
    await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_GREEN, CHARACTERISTIC_UUID)
    await asyncio.sleep(2)

    # 4. 赤色に変更 (コマンド追加)
    print("\n--- 4. 赤色に変更を実行 (新形式) ---")
    await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_RED, CHARACTERISTIC_UUID)
    await asyncio.sleep(2)

    # 5. 消灯 (コマンド変更)
    print("\n--- 5. 消灯を実行 (シーケンス終了) ---")
    await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_OFF, CHARACTERISTIC_UUID)


# --- メイン処理 ---
if __name__ == "__main__":

    # 非同期シーケンス関数を実行
    asyncio.run(main_sequence())
