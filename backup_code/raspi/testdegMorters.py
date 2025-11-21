#!/usr/bin/env python3
from flask import Flask, request, jsonify
import socket
import json
import sys
import time
from src import config

app = Flask(__name__)

COMMAND_TO_SEND = "A:90:50"


def send_command(command):
    """
    指定されたコマンドをEV3に1回だけ送信する関数
    """
    # 引数チェックを削除したため、sysはここで不要になる場合があるが、
    # エラー時の sys.exit() のために残してもよい

    print(f"Connecting to EV3 at {config.EV3_HOST}:{config.EV3_PORT}...")

    try:
        # ソケットを作成し、EV3に接続
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # タイムアウトを設定（例: 5秒）
            s.settimeout(5.0)

            s.connect((config.EV3_HOST, config.EV3_PORT))
            print(f"Connected! Sending command: '{command}'")

            # コマンドをUTF-8バイトにエンコードして送信
            s.sendall(command.encode('utf-8'))

            print("Command sent successfully. Disconnecting.")
        return True, None

    except ConnectionRefusedError:
        msg = f"Error: Connection refused. Check EV3 server and IP ({config.EV3_HOST})."
        print(msg)
        return False, msg  # 失敗をAPIに通知
    except socket.timeout:
        msg = "Error: Connection timed out. EV3 is not responding."
        print(msg)
        return False, msg  # 失敗をAPIに通知
    except socket.error as e:
        msg = f"Error: A socket error occurred: {e}"
        print(msg)
        return False, msg  # 失敗をAPIに通知
    except Exception as e:
        msg = f"An unexpected error occurred: {e}"
        print(msg)
        return False, msg  # 失敗をAPIに通知


# Web APIエンドポイント (ローカルPCからのリクエストを処理)
@app.route('/api/control_ev3', methods=['POST'])
def control_ev3():
    try:
        data = request.get_json()
        if not data or 'ev3_command' not in data:
            return jsonify({"status": "error", "message": "Missing 'ev3_command' in JSON payload"}), 400

        # ローカルPCから送られてきたコマンドを取得
        received_command = data.get("ev3_command")

        # 受け取ったコマンドをEV3送信関数に渡す
        success, error_message = send_command(received_command)

        if success:
            response_data = {
                "status": "success",
                "message": "Command successfully relayed to EV3.",
                "executed_command": received_command
            }
            return jsonify(response_data), 200
        else:
            response_data = {
                "status": "ev3_error",
                "message": "Failed to send command to EV3.",
                "error_detail": error_message
            }
            return jsonify(response_data), 503  # Service Unavailable

    except Exception as e:
        print(f"Flaskサーバーエラー: {e}")
        return jsonify({"status": "error", "message": f"Internal server error: {e}"}), 500


if __name__ == '__main__':
    # サーバーを常時起動 (このスクリプトをラズパイで起動し続ける必要があります)
    print("EV3ゲートウェイサーバーをポート5002で起動中...")
    print(f"EV3への接続先: {config.EV3_HOST}:{config.EV3_PORT}")
    app.run(host='0.0.0.0', port=5002, debug=False)
    # 引数(sys.argv)のチェックをすべて削除

    # スクリプトの先頭で定義した固定コマンド(COMMAND_TO_SEND)を送信
    send_command(COMMAND_TO_SEND)
