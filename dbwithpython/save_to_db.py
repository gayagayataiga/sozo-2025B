"""
main.pyから呼び出して、5分間のデータをデータベースに保存する関数
"""

import sqlite3
import datetime
import os
import numpy as np


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "study_data_.db")


def calculate_concentration_from_ear(ear):
    """
    EAR値から集中度を計算（簡易版）

    EAR値と集中度の関係：
    - EAR < 0.15: 寝ている → 集中度 0
    - 0.15 <= EAR < 0.20: うとうと → 集中度 20-40
    - 0.20 <= EAR < 0.25: やや低い → 集中度 40-60
    - 0.25 <= EAR < 0.30: 普通 → 集中度 60-80
    - EAR >= 0.30: 高い → 集中度 80-100
    """
    if ear < 0.15:
        return np.random.randint(0, 20)  # ほぼゼロ
    elif ear < 0.20:
        return np.random.randint(20, 40)  # 低い
    elif ear < 0.25:
        return np.random.randint(40, 60)  # やや低い
    elif ear < 0.30:
        return np.random.randint(60, 80)  # 普通
    else:
        return np.random.randint(80, 100)  # 高い


def categorize_concentration(conc):
    """
    集中度を4つのカテゴリに分類
    - High: 70以上
    - Medium: 40-70
    - Low: 10-40
    - Zero: 10未満
    """
    if conc >= 70:
        return 'high'
    elif conc >= 40:
        return 'medium'
    elif conc >= 10:
        return 'low'
    else:
        return 'zero'


def save_session_to_db(username, time_series_data, light_color=None):
    """
    5分間のセッションデータをデータベースに保存（集中度はまだ書き込まない）

    Args:
        username: ユーザー名
        time_series_data: list of dict [{timestamp, ear, mar, pose_P, pose_Y, pose_R}, ...]
        light_color: dict {'r': int, 'g': int, 'b': int, 'brightness': int} (オプション)

    Returns:
        int: 保存したレコードのID（あとで集中度を更新するために使う）、失敗時はNone
    """
    if not time_series_data or len(time_series_data) == 0:
        print("データが空なので保存をスキップします。")
        return None

    # 時間を計算（最初と最後のタイムスタンプの差）
    timestamps = [d.get('timestamp', 0) for d in time_series_data]
    duration_seconds = timestamps[-1] - timestamps[0]
    duration_minutes = int(duration_seconds / 60)

    # ライト設定（デフォルト値）
    if light_color is None:
        light_r, light_g, light_b = 255, 255, 255
        light_brightness = 80
    else:
        light_r = light_color.get('r', 255)
        light_g = light_color.get('g', 255)
        light_b = light_color.get('b', 255)
        light_brightness = light_color.get('brightness', 80)

    # データベースに保存
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ユーザーが存在しない場合は登録
    try:
        cursor.execute('INSERT INTO users (username, created_at) VALUES (?, ?)', (username, now))
        print(f"新規ユーザー登録: {username}")
    except sqlite3.IntegrityError:
        pass  # 既に存在する場合は無視

    # study_logsに保存（集中度はNULLで保存）
    sql = '''
        INSERT INTO study_logs (
            username,
            study_duration_minutes,
            concentration_avg, concentration_max, concentration_min,
            ratio_high, ratio_medium, ratio_low, ratio_zero,
            light_r, light_g, light_b, light_brightness,
            timestamp
        ) VALUES (?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL, ?, ?, ?, ?, ?)
    '''

    values = (
        username,
        duration_minutes,
        light_r, light_g, light_b, light_brightness,
        now
    )

    cursor.execute(sql, values)
    session_id = cursor.lastrowid  # 保存したレコードのIDを取得
    conn.commit()
    conn.close()

    print(f"\n=== データベース保存完了（集中度は未設定） ===")
    print(f"セッションID: {session_id}")
    print(f"ユーザー: {username}")
    print(f"時間: {duration_minutes} 分")
    print(f"タイムスタンプ: {now}")
    print("集中度はAI分析後に更新されます。")
    print("=" * 30 + "\n")

    return session_id


def update_concentration(session_id, concentration_data):
    """
    AI分析結果が返ってきたら、集中度を更新する

    Args:
        session_id: 更新対象のstudy_logsのID
        concentration_data: dict {
            'concentration_avg': float,
            'concentration_max': int,
            'concentration_min': int,
            'ratio_high': float,
            'ratio_medium': float,
            'ratio_low': float,
            'ratio_zero': float
        }

    Returns:
        bool: 更新成功したらTrue
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    sql = '''
        UPDATE study_logs
        SET concentration_avg = ?,
            concentration_max = ?,
            concentration_min = ?,
            ratio_high = ?,
            ratio_medium = ?,
            ratio_low = ?,
            ratio_zero = ?
        WHERE id = ?
    '''

    values = (
        concentration_data.get('concentration_avg', 0),
        concentration_data.get('concentration_max', 0),
        concentration_data.get('concentration_min', 0),
        concentration_data.get('ratio_high', 0),
        concentration_data.get('ratio_medium', 0),
        concentration_data.get('ratio_low', 0),
        concentration_data.get('ratio_zero', 0),
        session_id
    )

    cursor.execute(sql, values)
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()

    if rows_affected > 0:
        print(f"\n=== 集中度更新完了 ===")
        print(f"セッションID: {session_id}")
        print(f"集中度: 平均={concentration_data.get('concentration_avg', 0):.1f}, "
              f"最大={concentration_data.get('concentration_max', 0)}, "
              f"最小={concentration_data.get('concentration_min', 0)}")
        print(f"分布: High={concentration_data.get('ratio_high', 0):.1%}, "
              f"Med={concentration_data.get('ratio_medium', 0):.1%}, "
              f"Low={concentration_data.get('ratio_low', 0):.1%}, "
              f"Zero={concentration_data.get('ratio_zero', 0):.1%}")
        print("=" * 30 + "\n")
        return True
    else:
        print(f"警告: セッションID {session_id} が見つかりませんでした。")
        return False


# テスト用
if __name__ == "__main__":
    # サンプルデータ
    import time
    sample_data = []
    base_time = time.time()

    # 5分間（300秒）のダミーデータを生成
    for i in range(300):
        sample_data.append({
            'timestamp': base_time + i,
            'ear': np.random.uniform(0.20, 0.30),
            'mar': np.random.uniform(0.03, 0.08),
            'pose_P': np.random.uniform(160, 175),
            'pose_Y': np.random.uniform(-20, 20),
            'pose_R': np.random.uniform(5, 20)
        })

    # テスト保存
    save_session_to_db('test_user', sample_data, {'r': 255, 'g': 128, 'b': 0, 'brightness': 80})
