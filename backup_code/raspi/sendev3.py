#!/usr/bin/env python3

import socket
import time

# --- 接続先情報 ---
EV3_IP = '192.168.2.1'  # EV3のIPアドレス
PORT = 65432              # EV3のサーバーで設定したポート番号


def send_command(sock, command):
    """コマンドを送信する"""
    print(f"Sending command: '{command}'")
    # コマンドをバイト列に変換して送信
    sock.sendall(f"{command}\n".encode('utf-8'))


# --- メイン処理 ---
try:
    # サーバーへ接続を試みる
    print(f"Connecting to EV3 server at {EV3_IP}:{PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((EV3_IP, PORT))
        print("Successfully connected!")

        # --- ここにEV3にさせたい一連の動作を記述 ---
        send_command(s, "forward")
        time.sleep(2)
        send_command(s, "stop")
        time.sleep(1)
        send_command(s, "backward")
        time.sleep(2)
        send_command(s, "stop")

except ConnectionRefusedError:
    print("Connection failed. Is the server program running on the EV3?")
except Exception as e:
    print(f"An error occurred: {e}")

print("Client program finished.")
