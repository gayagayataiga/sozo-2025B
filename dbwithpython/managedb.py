import sqlite3
import datetime
import os

# DBファイルの保存場所（現在のファイルと同じ場所）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "study_data_.db")


def init_db():
    """ データベースとテーブルを初期化する """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. ユーザー管理テーブル（名前を主キーにする）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            created_at TEXT
        )
    ''')

    # 2. 勉強ログ保存テーブル
    # 名前(username)で紐付けますが、ログ自体は何度も保存するため
    # ログ固有のIDを主キーとしています。
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            
            -- 時間と集中度データ
            study_duration_minutes INTEGER,
            concentration_avg REAL,
            concentration_max INTEGER,
            concentration_min INTEGER,
            
            -- 集中度の割合 (High, Medium, Low, Zero)
            ratio_high REAL,
            ratio_medium REAL,
            ratio_low REAL,
            ratio_zero REAL,
            
            -- ライトの設定
            light_r INTEGER,
            light_g INTEGER,
            light_b INTEGER,
            light_brightness INTEGER,
            
            timestamp TEXT,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')
    conn.commit()
    conn.close()
    print("データベース初期化完了")


def register_user(username):
    """ ユーザーを登録する（存在しない場合のみ） """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute(
            'INSERT INTO users (username, created_at) VALUES (?, ?)', (username, now))
        conn.commit()
        print(f"新規ユーザー登録: {username}")
    except sqlite3.IntegrityError:
        # 既に存在する場合は何もしない
        pass
    finally:
        conn.close()


def add_detailed_log(data):
    """ 詳細なログを保存する """
    # ユーザーが登録されていなければ先に登録
    register_user(data['username'])

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sql = '''
        INSERT INTO study_logs (
            username, 
            study_duration_minutes, 
            concentration_avg, concentration_max, concentration_min,
            ratio_high, ratio_medium, ratio_low, ratio_zero,
            light_r, light_g, light_b, light_brightness,
            timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    values = (
        data['username'],
        data['duration'],
        data['conc_avg'], data['conc_max'], data['conc_min'],
        data['ratio_high'], data['ratio_med'], data['ratio_low'], data['ratio_zero'],
        data['light_r'], data['light_g'], data['light_b'], data['light_brightness'],
        now
    )

    cursor.execute(sql, values)
    conn.commit()
    conn.close()
    print(f"詳細ログ保存完了: {data['username']} - {now}")

# --- 実行テスト ---


if __name__ == "__main__":
    init_db()

    # サンプルデータ（辞書形式で渡すと管理しやすいです）
    sample_data = {
        "username": "takahashi",
        "duration": 60,             # 60分
        "conc_avg": 85.5,           # 平均集中度
        "conc_max": 98,             # 最大
        "conc_min": 40,             # 最小
        "ratio_high": 0.6,          # 60%
        "ratio_med": 0.3,           # 30%
        "ratio_low": 0.05,          # 5%
        "ratio_zero": 0.05,         # 5%
        "light_r": 255,             # 赤
        "light_g": 128,             # 緑
        "light_b": 0,               # 青
        "light_brightness": 80      # 明るさ80%
    }

    add_detailed_log(sample_data)
