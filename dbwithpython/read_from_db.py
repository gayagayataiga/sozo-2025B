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
