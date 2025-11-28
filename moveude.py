import requests 
import time
import math # 小数点の計算に必要

# --- 設定 (変更なし) ---
RASPBERRY_PI_IP = '10.27.74.138' 
PORT = 5000
SERVER_URL = f"http://{RASPBERRY_PI_IP}:{PORT}/servo/move"
# --------------------

# --- 制御関数 (変更なし) ---
def send_servo_command(duty_cycle):
    """ラズパイのサーバーにサーボ制御の命令を送信する"""
    
    payload = {
        "duty_cycle": duty_cycle
    }

    try:
        response = requests.post(SERVER_URL, json=payload, timeout=0.5) 

        if response.status_code == 200:
            # pass
            pass
        else:
            print(f"❌ Error: サーバーから {response.status_code} が返されました。")
            print(f"   詳細: {response.json().get('message', 'N/A')}")

    except requests.exceptions.Timeout:
        pass 
    except requests.exceptions.ConnectionError:
        print("❌ Error: 接続エラー。ラズパイのサーバーが起動していません。")
        raise
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

# --- 💡 滑らかに動かすための新しい関数 (修正版) ---
def smooth_move_servo(start_dc, end_dc, duration_sec, step_size_dc=0.01):
    """
    サーボモーターを滑らかに動かす。指定されたデューティ比の刻み幅を使用する。
    
    :param start_dc: 開始デューティ比 (%)
    :param end_dc: 終了デューティ比 (%)
    :param duration_sec: 動作にかける時間 (秒)
    :param step_size_dc: デューティ比の1ステップあたりの変化量 (%)
    """
    
    total_change = abs(end_dc - start_dc)
    
    # 1. 必要なステップ数を計算
    # 小数点以下の切り上げを行い、最後のステップで目標値に到達するようにする
    steps = math.ceil(total_change / step_size_dc)
    
    if steps == 0:
        print("🔄 開始と終了のデューティ比が同じです。移動しません。")
        return

    # 2. 実際のステップサイズ (丸め誤差対策)
    actual_step_size = (end_dc - start_dc) / steps
    
    # 3. 1ステップあたりの待機時間
    delay_time = duration_sec / steps
    
    current_dc = start_dc
    
    print(f"\n🐢 スムーズ移動開始: {start_dc:.2f}% から {end_dc:.2f}% へ ({duration_sec}秒で)")
    print(f"   - 総ステップ数: {steps} 回")
    print(f"   - 1ステップの変化量: {actual_step_size:.4f}% DC")
    print(f"   - 1ステップの待機時間: {delay_time:.4f}秒")


    # 💡 範囲関数を使って、開始から終了まで指定したステップで反復処理を行う
    for i in range(steps + 1): # 最後のステップ (end_dc) を含めるため steps + 1
        
        if i == steps:
            # 最終ステップでは目標値に正確に合わせる
            current_dc = end_dc
        else:
            # 次のステップのデューティ比を計算
            current_dc = start_dc + actual_step_size * i
            
        # ラズパイへ命令を送信
        send_servo_command(current_dc)
        
        # 最終ステップの後の待機は不要（一時停止時間で対応）
        if i < steps:
            # 短い時間待機
            time.sleep(delay_time)
            
    print("✅ スムーズ移動完了。")


# --- 💡 ローカルPCの他のコードとの接続例 (実行部分) ---

if __name__ == '__main__':
    print("ラズパイのサーボ制御を開始します。")
    
    # 往復運動のシミュレーション（ローカルPCから指示を送る）
    # デューティ比のパーセンテージに設定
    ANGLE_A = 2.5
    ANGLE_B = 3.3 # 2.5% から 2.8% までの狭い範囲を滑らかに動かす例
    
    # 動作速度の設定
    MOVE_DURATION_SEC = 0.3 # AからBへの移動にかける時間（3秒）
    PAUSE_DURATION_SEC = 1.0 # 角度に到達した後、一時停止する時間（1秒）
    
    # 💡 刻み幅の設定
    # 0.01% DC ずつ動かすように指定
    SMOOTHNESS_STEP_DC = 0.1
    
    # 処理が停止しないように、エラーが発生してもループは継続させる
    while True:
        try:
            # 1. AからBへゆっくり移動
            smooth_move_servo(ANGLE_A, ANGLE_B, MOVE_DURATION_SEC, step_size_dc=SMOOTHNESS_STEP_DC)
            time.sleep(PAUSE_DURATION_SEC) # Bで一時停止
            
            # 2. BからAへゆっくり移動（往復）
            smooth_move_servo(ANGLE_B, ANGLE_A, MOVE_DURATION_SEC, step_size_dc=SMOOTHNESS_STEP_DC)
            time.sleep(PAUSE_DURATION_SEC) # Aで一時停止
            
        except requests.exceptions.ConnectionError:
            # 接続エラーで終了した場合、少し待って再試行
            print("再接続を試みます...")
            time.sleep(5)
        except Exception as e:
            print(f"メインループで予期せぬエラーが発生しました: {e}")
            time.sleep(5)