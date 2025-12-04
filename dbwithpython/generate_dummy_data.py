import sqlite3
import datetime
import random
import os

# DBファイルの保存場所
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "study_data_.db")


def generate_dummy_logs(username="takahashi", count=100):
    """
    指定されたユーザー名で大量のダミーデータを生成する

    Args:
        username: ユーザー名（デフォルト: takahashi）
        count: 生成するログの数（デフォルト: 100）
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ユーザーが存在するか確認
    cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
    if cursor.fetchone() is None:
        # ユーザーが存在しなければ登録
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('INSERT INTO users (username, created_at) VALUES (?, ?)', (username, now))
        print(f"新規ユーザー登録: {username}")

    # 過去3ヶ月分のデータを生成
    base_time = datetime.datetime.now()

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

    logs_inserted = 0

    for i in range(count):
        # ランダムな日付を過去3ヶ月以内で生成
        days_ago = random.randint(0, 90)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        timestamp = base_time - datetime.timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # 勉強時間: 15分〜180分（3時間）
        duration = random.randint(15, 180)

        # 集中度の平均: 30〜100
        conc_avg = round(random.uniform(30.0, 100.0), 2)

        # 最大値は平均より高く
        conc_max = random.randint(int(conc_avg), 100)

        # 最小値は平均より低く
        conc_min = random.randint(0, int(conc_avg))

        # 集中度の割合（合計が1.0になるように）
        ratio_high = round(random.uniform(0.1, 0.7), 2)
        ratio_medium = round(random.uniform(0.1, 1.0 - ratio_high), 2)
        ratio_low = round(random.uniform(0.0, 1.0 - ratio_high - ratio_medium), 2)
        ratio_zero = round(1.0 - ratio_high - ratio_medium - ratio_low, 2)

        # ライト設定: RGB各0〜255、明るさ0〜100
        light_r = random.randint(0, 255)
        light_g = random.randint(0, 255)
        light_b = random.randint(0, 255)
        light_brightness = random.randint(20, 100)

        values = (
            username,
            duration,
            conc_avg, conc_max, conc_min,
            ratio_high, ratio_medium, ratio_low, ratio_zero,
            light_r, light_g, light_b, light_brightness,
            timestamp_str
        )

        cursor.execute(sql, values)
        logs_inserted += 1

        # 進捗表示（10件ごと）
        if (i + 1) % 10 == 0:
            print(f"進捗: {i + 1}/{count} 件のログを生成中...")

    conn.commit()
    conn.close()

    print(f"\n完了！ {logs_inserted} 件のダミーログを生成しました。")
    print(f"ユーザー名: {username}")


def show_stats():
    """データベースの統計情報を表示"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 総ユーザー数
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]

    # 総ログ数
    cursor.execute('SELECT COUNT(*) FROM study_logs')
    log_count = cursor.fetchone()[0]

    # ユーザーごとのログ数
    cursor.execute('''
        SELECT username, COUNT(*) as log_count
        FROM study_logs
        GROUP BY username
        ORDER BY log_count DESC
    ''')
    user_logs = cursor.fetchall()

    conn.close()

    print("\n=== データベース統計 ===")
    print(f"総ユーザー数: {user_count}")
    print(f"総ログ数: {log_count}")
    print("\nユーザー別ログ数:")
    for username, count in user_logs:
        print(f"  - {username}: {count} 件")


if __name__ == "__main__":
    print("=== ダミーデータ生成スクリプト ===\n")

    # 生成前の統計を表示
    print("【生成前】")
    show_stats()

    # ダミーデータを生成（takahashiさんで100件）
    print("\n" + "="*50)
    print("ダミーデータを生成します...")
    print("="*50 + "\n")

    # ここで件数を変更できます
    generate_dummy_logs(username="takahashi", count=100)

    # 生成後の統計を表示
    print("\n【生成後】")
    show_stats()
