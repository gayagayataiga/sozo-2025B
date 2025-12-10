import json
import os
import sys
import time
import requests
import numpy as np

# --- 設定項目 ---
# main.py から渡される入力ファイル
INPUT_JSON_PATH = "ai_input.json"
# main.py に渡す結果ファイル
RESULT_JSON_PATH = "ai_result.json"

# ★ここをColabのngrok URLに変更してください
# (末尾に /upload_json などのエンドポイントが必要かはColab側のコード次第ですが、通常は必要です)
COLAB_SERVER_URL = "https://abrielle-crustal-lowell.ngrok-free.dev/upload_json"

# タイムアウト設定 (秒)
TIMEOUT_SECONDS = 10.0

class NumpyEncoder(json.JSONEncoder):
    """ Numpy配列をJSONで送れるようにするおまじない """
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        if isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        return json.JSONEncoder.default(self, obj)

def main():
    print("--- ai.py (Bridge to Colab) Started ---")

    # 1. main.py が作ったデータを読み込む
    if not os.path.exists(INPUT_JSON_PATH):
        print(f"[Error] Input file not found: {INPUT_JSON_PATH}")
        return

    try:
        with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        print(" -> Data loaded from ai_input.json")
    except Exception as e:
        print(f"[Error] Failed to load input JSON: {e}")
        return

    # 2. Colabにデータを送信して分析を依頼
    print(f" -> Sending data to Colab: {COLAB_SERVER_URL}")
    
    result_data = {}
    try:
        # POSTリクエストで送信
        response = requests.post(
            COLAB_SERVER_URL,
            json=input_data, # 読み込んだデータをそのまま転送
            headers={'Content-Type': 'application/json'},
            timeout=TIMEOUT_SECONDS
        )
        
        # ステータスコードの確認
        response.raise_for_status()
        
        # 3. Colabからの結果を受け取る
        result_data = response.json()
        print(" -> Received response from Colab")
        
        # 成功フラグなどを念のため追加
        result_data["status"] = "success"

    except requests.exceptions.Timeout:
        print(f"[Error] Connection timed out ({TIMEOUT_SECONDS}s)")
        result_data = {"status": "error", "message": "Colab timeout"}
        
    except requests.exceptions.ConnectionError:
        print(f"[Error] Could not connect to Colab. Check URL or ngrok status.")
        result_data = {"status": "error", "message": "Connection failed"}
        
    except Exception as e:
        print(f"[Error] Unexpected error: {e}")
        # レスポンスがJSONじゃなかった場合など
        if 'response' in locals():
             print(f"Server response text: {response.text}")
        result_data = {"status": "error", "message": str(e)}

    # 4. 結果を main.py が読める形（ファイル）で保存
    try:
        with open(RESULT_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=4, ensure_ascii=False, cls=NumpyEncoder)
        print(f" -> Result saved to {RESULT_JSON_PATH}")
        
    except Exception as e:
        print(f"[Error] Failed to save result JSON: {e}")

    print("--- ai.py Finished ---")

if __name__ == "__main__":
    main()