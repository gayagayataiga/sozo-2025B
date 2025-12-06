import time
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading  # バックグラウンドでデータを送るために使用
import re
import socket
import json
import os
import sys

# データベース読み取りモジュールをインポート
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from dbwithpython.read_from_db import get_recent_sessions

DATA_JSON_PATH = "data.json"

# 1. FlaskとSocketIOの初期化
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # 実際にはランダムな文字列に
CORS(app)  # すべてのオリジンからのリクエストを許可
socketio = SocketIO(app, cors_allowed_origins="*")

# 集中度レベルのダミーデータ
CONCENTRATION_LEVELS = ["低", "中", "高", "ゾーン"]


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 外部へ接続せずにローカルIPを取得するトリック
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'  # 失敗したらローカルホストを使用
    finally:
        s.close()
    return IP


@app.route('/')
def serve_index():
    """ トップページへのアクセス時にHTMLを生成して返す """
    # 1. PCのIPアドレスを取得
    host_ip = get_local_ip()
    print(f"クライアントに渡すIPアドレス: {host_ip}")

    # 2. 'index.html' テンプレートをレンダリングし、IPアドレスを渡す
    return render_template('index.html', local_ip=host_ip)


# ------------------------------------------------------------------
# 2. ブラウザからの「操作」を受け取る (API)
# (JavaScriptの sendCommand 関数がここにアクセスする)
# ------------------------------------------------------------------


@app.route('/api/control', methods=['POST'])
def handle_control():
    """ ブラウザからのPOSTリクエストを受け取る """
    data = request.json
    action = data.get('action')
    value = data.get('value')

    #  サーバーPCのターミナルに、ブラウザからの入力を表示
    print(f"✅ ブラウザから受信: アクション={action}, 値={value}")

    if action == 'power_toggle':
        # 電源ON/OFFの処理 (value は 'on' または 'off')
        print(f"--- 電源を {value} にします ---")
        # (ここに実際のロボットの電源制御コードを書く)

    elif action == 'set_brightness':
        # 明るさ変更の処理 (value は 0〜100 の数値)
        print(f"--- 明るさを {value} にします ---")
        # (ここに実際のロボットの明るさ制御コードを書く)

    elif action == 'set_color_wheel':
        #  新しく追加した色相環の処理
        # value は "rgb(R, G, B)" という文字列
        print(f"--- 新しい色 {value} を設定します ---")

        # (例：RGB値を取り出してロボットに送る処理)
        try:
            # "rgb(255, 100, 20)" から数値だけを取り出す
            r, g, b = map(int, re.findall(r'\d+', value))
            print(f"--- R={r}, G={g}, B={b} として処理 ---")
            # (ここに実際のロボットのRGB制御コードを書く)
        except Exception as e:
            print(f"色の値の解析に失敗: {e}")

    elif action == 'move_arm':
        # アームを動かす処理
        print(f"--- アームを {value} に動かします ---")

    elif action == 'set_mode_elbow':
        try:
            angle = int(value)
            print(f"--- アームの角度を {angle} 度に設定します ---")
        except ValueError:
            print(f"[エラー] 角度の値が数値ではありません: {value}")
        except Exception as e:
            print(f"[エラー] モーター制御中に予期せぬエラー: {e}")
    elif action == 'set_angle_wrist':
        try:
            angle = int(value)
            print(f"--- 手首の角度を {angle} 度に設定します ---")

        except ValueError:
            print(f"[エラー] 手首の角度の値が数値ではありません: {value}")

    else:
        # 未知のアクション
        print(f"--- 未知のアクション {action} です ---")
    # ブラウザに「正常に受け取った」ことを伝える
    return jsonify({"status": "success", "received_action": action})


@app.route('/api/study-logs', methods=['GET'])
def get_study_logs():
    """ 勉強記録を取得するAPIエンドポイント """
    try:
        # クエリパラメータからユーザー名と取得件数を取得
        username = request.args.get('username', None)
        limit = int(request.args.get('limit', 10))

        # データベースから勉強記録を取得
        sessions = get_recent_sessions(username=username, limit=limit)

        # 成功レスポンスを返す
        return jsonify({
            "status": "success",
            "data": sessions,
            "count": len(sessions)
        })
    except Exception as e:
        print(f"[エラー] 勉強記録の取得に失敗: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ------------------------------------------------------------------
# 3. サーバーPCの情報をブラウザに「送信」する (WebSocket)
# (JavaScriptの socket.on('status_update', ...) がこれを受信する)
# ------------------------------------------------------------------


def send_status_updates():
    """
    バックグラウンドで実行され、data.json を読み込み、
    その情報をクライアントに送信する関数 (2秒ごと)
    """
    while True:
        # --- デフォルト値を設定 ---
        current_concentration = "Unknown"
        is_sleeping_now = False  # 睡眠状態も取得する例
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        try:
            # --- data.json を読み込む ---
            if os.path.exists(DATA_JSON_PATH):
                with open(DATA_JSON_PATH, 'r', encoding='utf-8') as f:
                    try:
                        shared_data = json.load(f)

                        ai_analysis_data = shared_data.get('ai_analysis', {})
                        analysis_results = ai_analysis_data.get('analysis', {})
                        current_concentration = analysis_results.get(
                            'concentration', 'Unknown')
                        is_sleeping_now = analysis_results.get(
                            'is_sleeping', False)  # 睡眠状態も取得

                    except json.JSONDecodeError:
                        print(f"[警告] {DATA_JSON_PATH} のJSON形式が正しくありません。")
                    except Exception as e:
                        print(f"[警告] {DATA_JSON_PATH} の読み込み中に予期せぬエラー: {e}")
            else:
                print(f"[情報] {DATA_JSON_PATH} が見つかりません。デフォルト値を送信します。")

            # --- 送信するデータを作成 ---
            data_to_send = {
                #  JavaScript側が期待するキー名に合わせる
                'concentration_level': current_concentration,
                'is_sleeping': is_sleeping_now,  # 睡眠状態も追加
                'timestamp': timestamp
            }

            #  'status_update' イベントで送信
            socketio.emit('status_update', data_to_send)

            print(
                f"🚀 ブラウザへ送信: 集中度={current_concentration}, 睡眠={is_sleeping_now}")

        except Exception as e:
            print(f"[エラー] send_status_updates ループ中にエラー: {e}")

        # --- 2秒待機 ---
        socketio.sleep(2)


@socketio.on('connect')
def handle_connect():
    """ ブラウザがWebSocketに接続したときに呼ばれる """
    print("✅ ブラウザがWebSocketに接続しました。")


@socketio.on('disconnect')
def handle_disconnect():
    """ ブラウザが切断したときに呼ばれる """
    print("❌ ブラウザが切断されました。")


# ------------------------------------------------------------------
# 4. サーバーの起動
# ------------------------------------------------------------------
if __name__ == '__main__':
    print("サーバーを http://0.0.0.0:5001 で起動します...")

    # バックグラウンドタスク（send_status_updates）を開始
    threading.Thread(target=send_status_updates, daemon=True).start()

    # Flask-SocketIOサーバーを起動
    # host='0.0.0.0' は、ローカルネットワーク内（スマホなど）からアクセス可能にする設定
    socketio.run(app, host='0.0.0.0', port=5001,
                 debug=True, allow_unsafe_werkzeug=True)
