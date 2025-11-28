import hashlib
import json
import os

# 前回のハッシュ値を保存するファイル（スクリプトと同じ場所に作られます）
HASH_STORAGE_FILE = "_internal_file_hashes.json"


def get_file_hash(filepath):
    """ファイルからSHA256ハッシュ値を計算する"""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None  # ファイルが見つからない
    except Exception as e:
        print(f"ハッシュ計算エラー ({filepath}): {e}")
        return None


def load_previous_hashes():
    """保存されている前回のハッシュ値を読み込む"""
    if not os.path.exists(HASH_STORAGE_FILE):
        return {}  # ファイルがなければ空の辞書
    try:
        with open(HASH_STORAGE_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}  # ファイルが壊れていたら空の辞書
    except Exception as e:
        print(f"ハッシュ読み込みエラー: {e}")
        return {}


def save_current_hashes(hashes_dict):
    """今回のハッシュ値をファイルに保存する"""
    try:
        with open(HASH_STORAGE_FILE, "w") as f:
            json.dump(hashes_dict, f, indent=2)
    except Exception as e:
        print(f"ハッシュ保存エラー: {e}")


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


def check_json_changes(input_json_paths: list) -> dict:
    """
    JSONファイルのリストを受け取り、前回からの変更をチェックする。
    変更があればJSONの中身を、なければ "NoChanges" を返す。
    """

    # 1. 前回のハッシュ値データを読み込む
    previous_hashes = load_previous_hashes()

    # 2. 今回のハッシュ値と、返す結果を格納する辞書を準備
    current_hashes = previous_hashes.copy()  # 基本は前回のを引き継ぐ
    result_changes = {}

    # 3. 入力された各ファイルをチェック
    for filepath in input_json_paths:

        # 4. 現在のファイルのハッシュ値を取得
        current_hash = get_file_hash(filepath)

        if current_hash is None:
            # ファイルが存在しない場合
            result_changes[filepath] = "File Not Found"
            if filepath in current_hashes:
                # 以前は存在したが、削除された
                del current_hashes[filepath]
            continue

        # 5. 前回のハッシュ値と比較
        previous_hash = previous_hashes.get(filepath)

        if previous_hash == current_hash:
            # --- 変更なし ---
            result_changes[filepath] = "NoChanges"
            # current_hashes はそのままでOK

        else:
            # --- 変更あり (または新規ファイル) ---
            print(f"変更を検出: {filepath}")
            # JSONファイルの中身を読み込んで結果に入れる
            json_content = read_json_file(filepath)
            result_changes[filepath] = json_content

            # 今回のハッシュ値を更新
            current_hashes[filepath] = current_hash

    # 7. 次回のために、今回のハッシュ値を保存
    save_current_hashes(current_hashes)

    # 8. 結果を返す
    return result_changes

# --- 実行例 ---


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


input_files = ["moveMorter.json", "aaa.json", "bbb.json", "non_existent.json"]

print("\n--- 1回目の実行 (すべて新規として検出) ---")
result_1 = check_json_changes(input_files)
print(json.dumps(result_1, indent=2, ensure_ascii=False))

print("\n--- 2回目の実行 (変更なし) ---")
result_2 = check_json_changes(input_files)
print(json.dumps(result_2, indent=2, ensure_ascii=False))

# 3. 1つのファイルの中身を変更してみる
try:
    with open("aaa.json", "w") as f:
        json.dump({"morter": 999, "new_key": "added"}, f)
    print("\n'aaa.json' の中身を変更しました。")
except Exception as e:
    print(f"ファイル変更エラー: {e}")

print("\n--- 3回目の実行 (aaa.json のみ変更検出) ---")
result_3 = check_json_changes(input_files)
print(json.dumps(result_3, indent=2, ensure_ascii=False))
