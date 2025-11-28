from bleak import BleakClient
import asyncio
import sys # sysモジュールをインポート

# --- 設定 ---
LIGHT_MAC_ADDRESS = "94:A9:90:76:E3:AE"
CHARACTERISTIC_UUID = "cba20002-224d-11e6-9fb8-0002a5d5c51b"

# --- 基本コマンド ---
COMMAND_ON = bytes([0x57, 0x0F, 0x47, 0x01, 0x01]) # オン
COMMAND_OFF = bytes([0x57, 0x0F, 0x47, 0x01, 0x02]) # オフ
# 輝度と色を設定するコマンドの基本形式: [0x57, 0x0F, 0x47, 0x01, 0x12, Brightness, R, G, B]
COMMAND_BASE = bytes([0x57, 0x0F, 0x47, 0x01, 0x12])


# --- 実行関数 (接続確認のフィードバックを追加) ---
async def control_switchbot_light(mac_address: str, command: bytes, uuid: str):
    """
    SwitchBotライトにBLE経由でコマンドを送信する
    """
    print(f" connecting to {mac_address}...")
    try:
        # 接続
        async with BleakClient(mac_address, timeout=10.0) as client:
            if client.is_connected:
                print("✅ BLE-successfully-connected, sent command")
                # コマンド送信
                await client.write_gatt_char(uuid, command, response=False)
            else:
                print("❌ Failed-connecting-BLE: Failed connecting to BLE.")

    except Exception as e:
        print(f"❌ Error at connecting-BLE: {e}")
        print("💡 To check your Bluetooth on and right MAC ADDRESS")


# --- ユーティリティ関数 ---
async def set_light_color_brightness(brightness: int, r: int, g: int, b: int):
    """
    指定された輝度と色 (R, G, B) でライトを設定する
    :param brightness: 輝度 (0-100)
    """
    # 輝度を16進数に変換し、コマンドを構築
    brightness_byte = max(0, min(100, brightness)) # 0-100の範囲に制限
    command = COMMAND_BASE + bytes([brightness_byte, r, g, b])
    await control_switchbot_light(LIGHT_MAC_ADDRESS, command, CHARACTERISTIC_UUID)


# --- 3. メイン制御関数 (4つの引数に対応) ---

async def main_controller(condition: str):
    """
    ターミナル引数に基づいてライトの制御を実行する (瞬時切り替え)
    """
    print(f"\n[メイン制御] 条件: '{condition}' に基づいてパターンを選択します。")
    
    if condition == "on":
        # 要件: 照度70%, 色 白色
        print("--- 💡 ON: 照度70%, 白色に設定 (瞬時) ---")
        await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_ON, CHARACTERISTIC_UUID)
        await set_light_color_brightness(
            brightness=100, 
            r=255, 
            g=255, 
            b=255
        )
        
    elif condition == "off":
        # 要件: 消灯
        print("--- 🔌 OFF: 消灯 (瞬時) ---")
        await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_OFF, CHARACTERISTIC_UUID)
        
    elif condition == "study":
        # 要件: 照度70%, 色 少し黄色が混ざった白色 (RGB: 255, 255, 200)
        print("--- 📚 STUDY: 照度70%, 黄色味のある白色に設定 (瞬時) ---")
        await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_ON, CHARACTERISTIC_UUID)
        await set_light_color_brightness(
            brightness=70, 
            r=255, 
            g=255, 
            b=200 # Bを下げて黄色味を出す
        )
        
    elif condition == "wake":
        # 要件: 照度100%, 色 赤色 (RGB: 255, 0, 0)
        print("--- ☀️ WAKE: 照度100%, 赤色に設定 (瞬時) ---")
        await control_switchbot_light(LIGHT_MAC_ADDRESS, COMMAND_ON, CHARACTERISTIC_UUID)
        await set_light_color_brightness(
            brightness=100, 
            r=255, 
            g=0, 
            b=0
        )
        
    else:
        print("⚠️ 未知の条件が指定されました。使用可能な条件: 'on', 'off', 'study', 'wake'")


# --- 4. 実行部分 (元の正しいロジックに訂正) ---
if __name__ == "__main__":
    
    # スクリプト名のみ (引数なし) の場合、エラーメッセージを表示
    if len(sys.argv) < 2:
        print("エラー: 実行するパターンをターミナル引数で指定してください。")
        print("使用法: python your_script_name.py [on | off | study | wake]")
    else:
        # 最初の引数 (sys.argv[1]) を取得し、小文字に変換して使用
        pattern = sys.argv[1].lower()
        print(f"指定されたパターン: {pattern}")
        
        # 非同期シーケンス関数を実行
        asyncio.run(main_controller(pattern))