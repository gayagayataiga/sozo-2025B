# --- ⚙️ Flaskサーバーによるサーボ制御コード (Raspberry Pi側) ---

import json
from flask import Flask, request, jsonify
from gpiozero import AngularServo
from gpiozero.pins.pigpio import PiGPIOFactory
import time

# --- 1. 設定 ---
# 💡 デューティ比から角度への変換ロジックをシンプルにするため、
#    ここではサーボ制御を「角度」ではなく「デューティ比のパーセンテージ」で扱うように変更します。
#    ただし、gpiozeroのAngularServoは角度ベースなので、
#    「デューティ比のパーセンテージ」を「角度」に変換する処理が必要です。

# ⚠️ ローカルPC側のコードに合わせて、デューティ比のパーセンテージ(%)を角度にマッピングします。
# ローカルPC側のコードのデューティ比の範囲は、例として 2.5%〜12.0% のようです。
# 一般的なサーボ(SG90など)では、2.5%が約0度、12.0%が約180度に対応します。
MIN_DUTY_CYCLE_PERCENT = 2.5  # 0度に対応するデューティ比のパーセンテージ
MAX_DUTY_CYCLE_PERCENT = 12.0  # 180度に対応するデューティ比のパーセンテージ
MIN_ANGLE_DEG = 0
MAX_ANGLE_DEG = 180

# --- 2. サーボ初期化 ---
# 提示されたコードと同じ設定を使用 (ピン4, pigpioを使用)
try:
    factory = PiGPIOFactory()
    # AngularServoはデフォルトで50Hz (20ms周期)です。
    # min_pulse_width, max_pulse_width はコメントアウトされていた元のコードと同じ値を使います。
    # 0.0004s (400us) -> 2.0% duty cycle @ 50Hz
    # 0.0024s (2400us) -> 12.0% duty cycle @ 50Hz
    # 💡 ただし、ローカルPC側のコードは 3.5%〜12.0% を使っているため、
    #    デューティ比と角度のマッピングを調整しやすいよう、
    #    min/max_pulse_widthは一旦デフォルト（min_angle/max_angleで調整）として、
    #    角度で制御するのが簡単です。

    # サーボ制御を「角度」で行うように再設定
    servo1 = AngularServo(
        4,
        min_angle=MIN_ANGLE_DEG,
        max_angle=MAX_ANGLE_DEG,
        min_pulse_width=0.0005,  # 一般的なサーボの 0度
        max_pulse_width=0.0025,  # 一般的なサーボの 180度
        pin_factory=factory
    )
    print("✅ AngularServoの初期化が完了しました。")

except Exception as e:
    print(f"❌ AngularServoの初期化中にエラーが発生しました: {e}")
    # サーボの初期化に失敗した場合は、サーバーを終了することも検討

# --- 3. Flask アプリケーション ---
app = Flask(__name__)
PORT = 5000  # ローカルPC側の設定と一致させる

# デューティ比のパーセンテージを角度に変換するヘルパー関数


def duty_cycle_to_angle(duty_cycle_percent):
    """
    ローカルPCから送られてきたデューティ比のパーセンテージを角度に線形変換する
    """
    # 範囲チェック
    if duty_cycle_percent < MIN_DUTY_CYCLE_PERCENT:
        print(f"⚠️ 最小デューティ比 {MIN_DUTY_CYCLE_PERCENT}% を下回っています。")
        duty_cycle_percent = MIN_DUTY_CYCLE_PERCENT
    elif duty_cycle_percent > MAX_DUTY_CYCLE_PERCENT:
        print(f"⚠️ 最大デューティ比 {MAX_DUTY_CYCLE_PERCENT}% を上回っています。")
        duty_cycle_percent = MAX_DUTY_CYCLE_PERCENT

    # 線形補間（リマップ）の計算
    # 角度 = MIN_ANGLE + (MAX_ANGLE - MIN_ANGLE) * (入力DC - MIN_DC) / (MAX_DC - MIN_DC)
    angle = MIN_ANGLE_DEG + (MAX_ANGLE_DEG - MIN_ANGLE_DEG) * \
        (duty_cycle_percent - MIN_DUTY_CYCLE_PERCENT) / \
        (MAX_DUTY_CYCLE_PERCENT - MIN_DUTY_CYCLE_PERCENT)

    # 角度を整数に丸める（必要に応じて）
    return round(angle)

# サーボを動かすエンドポイント


@app.route('/servo/move', methods=['POST'])
def move_servo():
    """
    ローカルPCから送られたJSONデータ ({"duty_cycle": <float>}) を受け取り、
    サーボモーターを動かす。
    """
    if not request.is_json:
        return jsonify({"message": "リクエストボディはJSON形式である必要があります"}), 400

    data = request.get_json()

    if 'duty_cycle' not in data:
        return jsonify({"message": "'duty_cycle' フィールドが必要です"}), 400

    try:
        # 1. デューティ比のパーセンテージを取得
        duty_cycle = float(data['duty_cycle'])

        # 2. 角度に変換
        target_angle = duty_cycle_to_angle(duty_cycle)

        # 3. サーボを動かす
        servo1.angle = target_angle

        # 💡 デバッグ用: 動作が確認できたらコメントアウトしても良い
        print(f"✨ 受信DC: {duty_cycle:.2f}% -> 設定角度: {target_angle}°")

        return jsonify({
            "message": "サーボ移動コマンドを受け付けました",
            "angle": target_angle,
            "duty_cycle_received": duty_cycle
        }), 200

    except ValueError:
        return jsonify({"message": "'duty_cycle' は数値でなければなりません"}), 400
    except Exception as e:
        print(f"❌ サーボ制御中に予期せぬエラー: {e}")
        return jsonify({"message": f"サーバーエラー: {e}"}), 500


# サーバーの起動
if __name__ == '__main__':
    # ⚠️ host='0.0.0.0' にすることで、外部ネットワークからアクセス可能になります。
    #    ラズパイの実際のIPアドレスにアクセスする際に必須です。
    app.run(host='0.0.0.0', port=PORT)
