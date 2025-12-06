"""
データベースから過去のセッションデータを読み取る関数
AI分析時に過去のデータをColabに送るために使用
"""

import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "study_data_.db")


def get_recent_sessions(username=None, limit=10):
    """
    最近のセッションを取得する

    Args:
        username: ユーザー名（Noneの場合は全ユーザー）
        limit: 取得するセッション数（デフォルト10）

    Returns:
        list of dict: セッション情報のリスト
            [{
                'session_id': int,
                'username': str,
                'study_duration_minutes': int,
                'concentration_avg': float,
                'timestamp': str,
                'light_color': {'r': int, 'g': int, 'b': int, 'brightness': int}
            }, ...]
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if username:
        sql = '''
            SELECT id, username, study_duration_minutes,
                   concentration_avg, concentration_max, concentration_min,
                   ratio_high, ratio_medium, ratio_low, ratio_zero,
                   light_r, light_g, light_b, light_brightness,
                   timestamp
            FROM study_logs
            WHERE username = ?
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        cursor.execute(sql, (username, limit))
    else:
        sql = '''
            SELECT id, username, study_duration_minutes,
                   concentration_avg, concentration_max, concentration_min,
                   ratio_high, ratio_medium, ratio_low, ratio_zero,
                   light_r, light_g, light_b, light_brightness,
                   timestamp
            FROM study_logs
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        cursor.execute(sql, (limit,))

    rows = cursor.fetchall()
    conn.close()

    sessions = []
    for row in rows:
        sessions.append({
            'session_id': row[0],
            'username': row[1],
            'study_duration_minutes': row[2],
            'concentration_avg': row[3],
            'concentration_max': row[4],
            'concentration_min': row[5],
            'ratio_high': row[6],
            'ratio_medium': row[7],
            'ratio_low': row[8],
            'ratio_zero': row[9],
            'light_color': {
                'r': row[10],
                'g': row[11],
                'b': row[12],
                'brightness': row[13]
            },
            'timestamp': row[14]
        })

    return sessions


def get_frame_data_by_session(session_id):
    """
    特定のセッションの全フレームデータを取得する

    Args:
        session_id: セッションID

    Returns:
        list of dict: フレームデータのリスト
            [{
                'timestamp': float,
                'ear': float,
                'mar': float,
                'pose_P': float,
                'pose_Y': float,
                'pose_R': float
            }, ...]
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    sql = '''
        SELECT timestamp, ear, mar, pose_P, pose_Y, pose_R
        FROM frame_data
        WHERE session_id = ?
        ORDER BY timestamp ASC
    '''
    cursor.execute(sql, (session_id,))
    rows = cursor.fetchall()
    conn.close()

    frames = []
    for row in rows:
        frames.append({
            'timestamp': row[0],
            'ear': row[1],
            'mar': row[2],
            'pose_P': row[3],
            'pose_Y': row[4],
            'pose_R': row[5]
        })

    return frames


def get_recent_sessions_with_frames(username=None, limit=5):
    """
    最近のセッションとそのフレームデータを全て取得する

    Args:
        username: ユーザー名（Noneの場合は全ユーザー）
        limit: 取得するセッション数（デフォルト5）

    Returns:
        list of dict: セッション情報とフレームデータのリスト
            [{
                'session_id': int,
                'username': str,
                'study_duration_minutes': int,
                'concentration_avg': float,
                'timestamp': str,
                'light_color': {...},
                'frames': [{...}, {...}, ...]  # フレームデータ
            }, ...]
    """
    sessions = get_recent_sessions(username, limit)

    # 各セッションにフレームデータを追加
    for session in sessions:
        session['frames'] = get_frame_data_by_session(session['session_id'])

    return sessions


def get_ai_analysis_results(session_id=None, limit=10):
    """
    AI分析結果を取得する

    Args:
        session_id: セッションID（Noneの場合は全セッション）
        limit: 取得する結果数（デフォルト10）

    Returns:
        list of dict: AI分析結果のリスト
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if session_id:
        sql = '''
            SELECT id, session_id, status, is_sleeping, concentration,
                   local_run_id, colab_run_id, processing_timestamp,
                   raw_response, created_at
            FROM ai_analysis_results
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        '''
        cursor.execute(sql, (session_id, limit))
    else:
        sql = '''
            SELECT id, session_id, status, is_sleeping, concentration,
                   local_run_id, colab_run_id, processing_timestamp,
                   raw_response, created_at
            FROM ai_analysis_results
            ORDER BY created_at DESC
            LIMIT ?
        '''
        cursor.execute(sql, (limit,))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            'id': row[0],
            'session_id': row[1],
            'status': row[2],
            'is_sleeping': bool(row[3]),
            'concentration': row[4],
            'local_run_id': row[5],
            'colab_run_id': row[6],
            'processing_timestamp': row[7],
            'raw_response': row[8],
            'created_at': row[9]
        })

    return results


def get_weekly_study_stats(username=None, days=7):
    """
    過去N日間の日別勉強統計を取得する

    Args:
        username: ユーザー名（Noneの場合は全ユーザー）
        days: 取得する日数（デフォルト7日間）

    Returns:
        list of dict: 日別の統計情報
            [{
                'date': str,  # 'YYYY-MM-DD'
                'total_minutes': int,
                'session_count': int,
                'avg_concentration': float
            }, ...]
    """
    import sqlite3
    from datetime import datetime, timedelta
    from collections import defaultdict

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 過去N日間の開始日を計算
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days-1)
    start_date_str = start_date.strftime("%Y-%m-%d 00:00:00")

    if username:
        sql = '''
            SELECT timestamp, study_duration_minutes, concentration_avg
            FROM study_logs
            WHERE username = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        '''
        cursor.execute(sql, (username, start_date_str))
    else:
        sql = '''
            SELECT timestamp, study_duration_minutes, concentration_avg
            FROM study_logs
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        '''
        cursor.execute(sql, (start_date_str,))

    rows = cursor.fetchall()
    conn.close()

    # 日付ごとに集計
    stats_by_date = defaultdict(lambda: {
        'total_minutes': 0,
        'session_count': 0,
        'concentration_sum': 0,
        'concentration_count': 0
    })

    for row in rows:
        timestamp_str = row[0]
        duration = row[1] or 0
        concentration = row[2]

        # 日付を取得（YYYY-MM-DD形式）
        date_str = timestamp_str.split(' ')[0]

        stats_by_date[date_str]['total_minutes'] += duration
        stats_by_date[date_str]['session_count'] += 1

        if concentration is not None:
            stats_by_date[date_str]['concentration_sum'] += concentration
            stats_by_date[date_str]['concentration_count'] += 1

    # 過去N日分の結果を作成（データがない日も含める）
    result = []
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")

        stats = stats_by_date.get(date_str, {
            'total_minutes': 0,
            'session_count': 0,
            'concentration_sum': 0,
            'concentration_count': 0
        })

        avg_concentration = None
        if stats['concentration_count'] > 0:
            avg_concentration = stats['concentration_sum'] / stats['concentration_count']

        result.append({
            'date': date_str,
            'total_minutes': stats['total_minutes'],
            'session_count': stats['session_count'],
            'avg_concentration': avg_concentration
        })

    return result


# テスト用
if __name__ == "__main__":
    print("=== 最近のセッション（統計のみ） ===")
    sessions = get_recent_sessions(limit=3)
    for s in sessions:
        print(f"セッションID: {s['session_id']}, ユーザー: {s['username']}, "
              f"時間: {s['study_duration_minutes']}分, 集中度平均: {s['concentration_avg']}")

    print("\n=== 最近のセッション（フレームデータ付き） ===")
    sessions_with_frames = get_recent_sessions_with_frames(limit=2)
    for s in sessions_with_frames:
        print(f"セッションID: {s['session_id']}, ユーザー: {s['username']}, "
              f"フレーム数: {len(s['frames'])}")
        if len(s['frames']) > 0:
            print(f"  最初のフレーム: {s['frames'][0]}")
            print(f"  最後のフレーム: {s['frames'][-1]}")

    print("\n=== AI分析結果 ===")
    ai_results = get_ai_analysis_results(limit=3)
    for r in ai_results:
        print(f"結果ID: {r['id']}, セッションID: {r['session_id']}, "
              f"集中度: {r['concentration']}, 作成日時: {r['created_at']}")
