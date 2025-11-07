import hashlib
import json
import os


# --- ヘルパー関数群 ---
def get_file_hash(filepath):
    """ファイルからSHA256ハッシュ値を計算する"""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"ハッシュ計算エラー ({filepath}): {e}")
        return None


def load_previous_hashes(hash_storage_file: str) -> dict:  # 引数を追加
    """保存されている前回のハッシュ値を読み込む"""
    if not os.path.exists(hash_storage_file):
        return {}
    try:
        with open(hash_storage_file, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}  # ファイルが壊れていても空の辞書を返す
    except Exception as e:
        print(f"ハッシュ読み込みエラー ({hash_storage_file}): {e}")
        return {}


def save_current_hashes(hashes_dict: dict, hash_storage_file: str):  # 引数を追加
    """今回のハッシュ値をファイルに保存する"""
    try:
        with open(hash_storage_file, "w") as f:
            json.dump(hashes_dict, f, indent=2)
    except Exception as e:
        print(f"ハッシュ保存エラー ({hash_storage_file}): {e}")


def read_json_file(filepath):
    """JSONファイルの中身を読み込んで辞書として返す"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"JSONデコードエラー: {filepath}")
        return {"error": "Invalid JSON format"}
    except FileNotFoundError:
        return {"error": "File Not Found during read"}
    except Exception as e:
        print(f"JSON読み込みエラー ({filepath}): {e}")
        return {"error": str(e)}


# --- メインの関数 ---
def check_json_changes(
    input_json_paths: list,
    hash_file: str = "_internal_file_hashes.json"  # 引数を追加 (デフォルト値付き)
) -> dict:
    """
    JSONファイルのリストを受け取り、前回からの変更をチェックする。
    変更があればJSONの中身を、なければ "NoChanges" を返す。

    Args:
        input_json_paths (list): チェック対象のJSONファイルパスのリスト
        hash_file (str): 前回のハッシュ値を保存/読み込みするファイル名

    Returns:
        dict: 各ファイルパスをキーとし、変更内容または "NoChanges" を値とする辞書
    """

    #  前回のハッシュ値データを読み込む (引数を使用)
    previous_hashes = load_previous_hashes(hash_file)

    current_hashes = previous_hashes.copy()
    result_changes = {}

    for filepath in input_json_paths:
        current_hash = get_file_hash(filepath)

        if current_hash is None:
            # ファイルが存在しない
            result_changes[filepath] = "File Not Found"
            if filepath in current_hashes:
                del current_hashes[filepath]  # 削除されたことを記録
            continue

        previous_hash = previous_hashes.get(filepath)

        if previous_hash == current_hash:
            # 変更なし
            result_changes[filepath] = "NoChanges"
        else:
            # 変更あり (または新規)
            print(f"変更を検出: {filepath}")
            json_content = read_json_file(filepath)
            result_changes[filepath] = json_content
            current_hashes[filepath] = current_hash  # ハッシュ値を更新

    #  次回のために、今回のハッシュ値を保存 (引数を使用)
    save_current_hashes(current_hashes, hash_file)

    return result_changes


# --- 実行例（このファイルが直接実行された時だけ動く） ---
if __name__ == "__main__":

    print("--- モジュール単体テスト開始 ---")

    # 1. テスト用のダミーJSONファイルを作成
    try:
        with open("moveMorter.json", "w") as f:
            json.dump({"morter": 50, "speed": 10}, f)
        with open("aaa.json", "w") as f:
            json.dump({"morter": 70}, f)
        with open("bbb.json", "w") as f:
            json.dump({"r": 255, "b": 0, "g": 89}, f)
        print("テストファイルを作成しました。")
    except Exception as e:
        print(f"ファイル作成エラー: {e}")

    input_files = ["moveMorter.json", "aaa.json",
                   "bbb.json", "non_existent.json"]

    # テスト用のハッシュファイル名を指定
    test_hash_file = "_test_hashes.json"

    print("\n--- 1回目の実行 (すべて新規として検出) ---")
    result_1 = check_json_changes(input_files, hash_file=test_hash_file)
    print(json.dumps(result_1, indent=2, ensure_ascii=False))

    print("\n--- 2回目の実行 (変更なし) ---")
    result_2 = check_json_changes(input_files, hash_file=test_hash_file)
    print(json.dumps(result_2, indent=2, ensure_ascii=False))

    # 3. 1つのファイルの中身を変更
    try:
        with open("aaa.json", "w") as f:
            json.dump({"morter": 999, "new_key": "added"}, f)
        print("\n'aaa.json' の中身を変更しました。")
    except Exception as e:
        print(f"ファイル変更エラー: {e}")

    print("\n--- 3回目の実行 (aaa.json のみ変更検出) ---")
    result_3 = check_json_changes(input_files, hash_file=test_hash_file)
    print(json.dumps(result_3, indent=2, ensure_ascii=False))

    # 4. クリーンアップ
    print("\n--- クリーンアップ ---")
    try:
        os.remove("moveMorter.json")
        os.remove("aaa.json")
        os.remove("bbb.json")
        os.remove(test_hash_file)  # テスト用ハッシュファイルも削除
        print("テストファイルとハッシュファイルを削除しました。")
    except Exception as e:
        print(f"クリーンアップエラー: {e}")
