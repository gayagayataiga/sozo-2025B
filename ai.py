import os
import json
import time
import uuid
import sys
import numpy as np

# --- 設定項目 ---
# main.py が生成する入力ファイル
INPUT_JSON_PATH = "ai_input.json"
# このスクリプトが生成する結果ファイル (main.py が読み取る)
RESULT_JSON_PATH = "ai_result.json"
# 分析をリクエストする Colab サーバーのエンドポイント
ANALYSIS_SERVER_URL = "https://abrielle-crustal-lowell.ngrok-free.dev/upload_json"
# サーバーへの接続タイムアウト（秒）
SERVER_TIMEOUT = 10.0

# 依存ライブラリのインポートチェック
try:
    import requests  # requestsライブラリをインポート
    print("Successfully imported requests.")
except ModuleNotFoundError as e:
    print(f"---  FATAL: requests ライブラリが見つかりません ---")
    print(f"ERROR during import: {e}")
    print("pip install requests を実行してください。")
    sys.exit(1)  # 必須ライブラリがない場合は終了


# ヘルパークラス・関数
class NumpyEncoder(json.JSONEncoder):
    """ Numpy配列をJSONシリアライズ可能にするためのエンコーダー """

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()  # Numpy配列をPythonリストに変換
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        if isinstance(obj, (np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        if isinstance(obj, (np.complex_, np.complex64, np.complex128)):
            return {'real': obj.real, 'imag': obj.imag}
        return json.JSONEncoder.default(self, obj)


def get_analysis_from_server(input_payload, server_url):
    """
    Colabサーバーに分析をリクエストし、結果のJSONを返す
    """
    print(f"Sending analysis request to {server_url}...")
    try:
        # requests.post を使い、 json=... でデータを送信
        # Colab側が分析に時間がかかる可能性があるため、timeoutを設定
        response = requests.post(
            server_url,
            data=json.dumps(input_payload, cls=NumpyEncoder),
            headers={'Content-Type': 'application/json'},
            timeout=SERVER_TIMEOUT
        )
        response.raise_for_status()  # 200系以外のステータスコードならエラー

        # サーバーからのレスポンス(JSON)をパースして返す
        analysis_result = response.json()
        print(f" Analysis response received from server.")
        # print(f"   Server Response: {analysis_result}")
        return analysis_result

    except requests.exceptions.Timeout:
        print(
            f" Failed to get analysis: Server timed out ({SERVER_TIMEOUT}s)")
        return None
    except requests.exceptions.RequestException as e:
        print(f" Failed to get analysis: Request failed: {e}")
        return None
    except json.JSONDecodeError:
        print(f" Failed to get analysis: Server returned invalid JSON.")
        print(f"   Server Response (text): {response.text}")
        return None
    except Exception as e:
        print(
            f" An unexpected error occurred during server communication: {e}")
        return None


# --- ローカルの analyze_time_series 関数は削除 ---
# メイン処理
def main_process():
    """
    メインの処理フロー
    1. 入力読み込み
    2. Colabサーバーに分析をリクエスト
    3. 結果をローカル保存 (main.py用)
    """
    print("--- ai.py started ---")
    print(f"Python Executable: {sys.executable}")
    unique_id = str(uuid.uuid4())  # この実行固有のID
    print(f"Run ID: {unique_id}")

    # ---  入力JSONの読み込み ---
    if not os.path.exists(INPUT_JSON_PATH):
        print(f"---  FATAL: Input file not found: {INPUT_JSON_PATH} ---")
        return

    try:
        with open(INPUT_JSON_PATH, 'r') as f:
            input_data = json.load(f)
        print("Input JSON loaded successfully.")
    except json.JSONDecodeError:
        print(f"---  FATAL: Could not decode JSON from {INPUT_JSON_PATH} ---")
        return
    except Exception as e:
        print(
            f"---  FATAL: An unexpected error occurred during loading: {e} ---")
        return

    # --- Colabサーバーに分析をリクエスト ---
    # input_data (time_series_dataを含む) をそのままペイロードとして送信
    if not ANALYSIS_SERVER_URL:
        print("---  FATAL: ANALYSIS_SERVER_URL が設定されていません。 ---")
        return

    colab_response = get_analysis_from_server(input_data, ANALYSIS_SERVER_URL)

    # --- 最終結果データを作成 ---
    final_result_data = {}

    if colab_response:
        # サーバーからのレスポンスをそのまま結果として採用
        # (Colab側が 'analysis' や 'debug_info' のキーを持つJSONを返すと想定)
        final_result_data = colab_response

        # 必須キーを追加
        final_result_data['status'] = "processed_by_colab"
        final_result_data['colab_run_id'] = colab_response.get(
            'run_id', 'N/A')  # Colab側のID
    else:
        # サーバー分析失敗時のフォールバック (エラー通知)
        final_result_data = {
            "status": "error_colab_failed",
            "analysis": {
                "is_sleeping": False,  # デフォルト値
                "concentration": "Unknown"
            },
            "debug_info": {
                "error": "Failed to get analysis from Colab server."
            }
        }

    # この ai.py プロセス固有のIDとタイムスタンプを追加
    final_result_data['local_run_id'] = unique_id
    final_result_data['processing_timestamp'] = time.time()

    # 入力サマリーを追加 (デバッグ用)
    time_series = input_data.get('time_series_data', [])
    latest_data = time_series[-1] if time_series else {}
    final_result_data['input_summary'] = {
        "name": input_data.get("name", "N/A"),
        "latest_ear": latest_data.get('ear'),
        "latest_mar": latest_data.get('mar'),
    }

    # --- 結果をローカルファイルに書き出す ---
    try:
        with open(RESULT_JSON_PATH, 'w') as f:
            json.dump(final_result_data, f, indent=4, cls=NumpyEncoder)
        print(f"Result successfully written to {RESULT_JSON_PATH}")
    except Exception as e:
        print(f"[Error] Failed to write result JSON: {e}")
        # このエラーは致命的ではないかもしれないので、処理は続行


# --- スクリプト実行 ---
if __name__ == "__main__":
    main_process()
    print("--- ai.py finished ---")
