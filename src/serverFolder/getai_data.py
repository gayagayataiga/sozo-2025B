from flask import Flask, request, jsonify
from datetime import datetime
import sqlite3
import os
import json

app = Flask(__name__)

DB_NAME = "../../dbwithpython/study_data_.db"
MOVE_MOTORS_PATH = "../../data/moveMotors.json"
DATA_JSON_PATH = "../../data/data.json"
LOG_FILE_PATH = "../../data/colab_received_data.log"

def get_username_from_data_json():
    """
    data.jsonからユーザー名を取得
    """
    try:
        if os.path.exists(DATA_JSON_PATH):
            with open(DATA_JSON_PATH, 'r', encoding='utf-8') as f:
                data_json = json.load(f)
                return data_json.get('username', 'Gayagaya')
    except Exception as e:
        print(f" ユーザー名取得エラー: {e}")

    # デフォルト値
    return 'Gayagaya'

def get_current_light_values():
    """
    moveMotors.jsonから現在のライト設定値を読み取る
    """
    try:
        if os.path.exists(MOVE_MOTORS_PATH):
            with open(MOVE_MOTORS_PATH, 'r', encoding='utf-8') as f:
                motor_data = json.load(f)
                color = motor_data.get('color', {})
                return {
                    'r': color.get('r', 0),
                    'g': color.get('g', 0),
                    'b': color.get('b', 0),
                    'brightness': motor_data.get('brightness', 0)
                }
    except Exception as e:
        print(f" ライト情報取得エラー: {e}")

    # デフォルト値
    return {'r': 0, 'g': 0, 'b': 0, 'brightness': 0}

def update_data_json(analysis_data, colab_data):
    """
    data.jsonのai_analysis部分を更新
    """
    try:
        # 既存のdata.jsonを読み込む
        data_json = {}
        if os.path.exists(DATA_JSON_PATH):
            with open(DATA_JSON_PATH, 'r', encoding='utf-8') as f:
                data_json = json.load(f)

        # ai_analysis部分を更新
        data_json['ai_analysis'] = {
            'status': 'processed_by_colab',
            'analysis': {
                'is_sleeping': analysis_data['is_sleeping'],
                'concentration': analysis_data['concentration']
            },
            'debug_info': {},
            'processing_timestamp': colab_data.get('timestamp', datetime.now().timestamp()),
            'input_summary': {
                'name': data_json.get('username', 'Gayagaya'),
                'concentration_avg': analysis_data['conc_avg'],
                'concentration_max': analysis_data['conc_max'],
                'concentration_min': analysis_data['conc_min'],
                'num_predictions': colab_data.get('num_predictions', 0)
            },
            'summary': colab_data.get('summary', {}),
            'avg_concentration': colab_data.get('avg_concentration', 0)
        }

        # ファイルに書き込む
        with open(DATA_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(data_json, f, ensure_ascii=False, indent=2)

        print(f"   data.json更新完了")

    except Exception as e:
        print(f" data.json更新エラー: {e}")

def write_to_log(data, session_id, result_id, light_values, conc_stats):
    """
    受け取ったデータをログファイルに書き出す
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = get_username_from_data_json()

        # ログエントリのヘッダー
        log_entry = f"""
{'='*80}
受信時刻: {timestamp}
セッションID: {session_id} | 結果ID: {result_id}
ユーザー: {username}

【ライト設定】
  RGB: ({light_values['r']}, {light_values['g']}, {light_values['b']})
  輝度: {light_values['brightness']}%

【受信データ全体】
"""

        # 受け取ったデータ全体をJSON形式で整形して追加
        log_entry += json.dumps(data, ensure_ascii=False, indent=2)
        log_entry += f"\n{'='*80}\n"

        # ログファイルに追記
        with open(LOG_FILE_PATH, 'a', encoding='utf-8') as f:
            f.write(log_entry)

        print(f"   ログファイル書き込み完了: {LOG_FILE_PATH}")

    except Exception as e:
        print(f" ログファイル書き込みエラー: {e}")

def save_ai_result_to_db(data):
    """
    Colabから受け取った推論結果をDBに保存
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # data.jsonからユーザー名を取得
    username = get_username_from_data_json()

    # moveMotors.jsonからライト情報を取得
    light_values = get_current_light_values()

    summary = data.get('summary', {})
    avg_conc = data.get('avg_concentration', 0)

    # time_series_dataから集中度の統計と睡眠状態を計算
    time_series = data.get('time_series_data', [])
    if time_series:
        # drowsy_scoreは眠気スコアなので、集中度は (1 - drowsy_score) * 100
        concentration_scores = [(1 - item.get('drowsy_score', 0)) * 100 for item in time_series]
        conc_max = max(concentration_scores) if concentration_scores else 0
        conc_min = min(concentration_scores) if concentration_scores else 0
        conc_avg = sum(concentration_scores) / len(concentration_scores) if concentration_scores else 0

        # 全データポイントのdrowsy_statusを集計
        status_count = {'AWAKE': 0, 'DROWSY': 0, 'SLEEPING': 0}
        for item in time_series:
            status = item.get('drowsy_status', 'AWAKE')
            if status in status_count:
                status_count[status] += 1

        # 最も多い状態を判定
        total_count = len(time_series)
        awake_ratio = status_count['AWAKE'] / total_count if total_count > 0 else 0
        drowsy_ratio = status_count['DROWSY'] / total_count if total_count > 0 else 0
        sleeping_ratio = status_count['SLEEPING'] / total_count if total_count > 0 else 0

        # ratioを計算（全データポイントから）
        ratio_high = awake_ratio  # 覚醒 = 集中
        ratio_medium = drowsy_ratio  # 眠気
        ratio_low = sleeping_ratio * 0.5  # 寝落ちの半分
        ratio_zero = sleeping_ratio * 0.5  # 寝落ちの半分

        # 寝落ちの割合が30%以上なら睡眠中、眠気が50%以上なら眠気状態
        if sleeping_ratio >= 0.3:
            is_sleeping = 1
        elif drowsy_ratio >= 0.5:
            is_sleeping = 0  # 眠気状態だが寝ていない
        else:
            is_sleeping = 0  # 覚醒状態

    else:
        # time_series_dataがない場合はavg_concentrationとsummaryを使用
        conc_max = avg_conc * 100
        conc_min = avg_conc * 100
        conc_avg = avg_conc * 100

        # summaryからratioを計算
        ratio_high = summary.get('集中', 0) / 100
        ratio_medium = summary.get('眠気', 0) / 100
        ratio_low = summary.get('寝落ち', 0) / 100 * 0.5
        ratio_zero = summary.get('寝落ち', 0) / 100 * 0.5

        # summaryから睡眠状態を判定
        sleep_states = {
            '集中': summary.get('集中', 0),
            '眠気': summary.get('眠気', 0),
            '寝落ち': summary.get('寝落ち', 0)
        }
        dominant_state = max(sleep_states, key=sleep_states.get)
        is_sleeping = 1 if dominant_state == '寝落ち' else 0

    # 集中度カテゴリ（計算した平均値を使用）
    conc_avg_normalized = conc_avg / 100  # 0-100を0-1に正規化
    if conc_avg_normalized >= 0.7:
        concentration_category = f"High ({conc_avg:.0f}%)"
    elif conc_avg_normalized >= 0.4:
        concentration_category = f"Medium ({conc_avg:.0f}%)"
    elif conc_avg_normalized >= 0.1:
        concentration_category = f"Low ({conc_avg:.0f}%)"
    else:
        concentration_category = f"Zero ({conc_avg:.0f}%)"

    # study_logsに保存
    study_sql = '''
        INSERT INTO study_logs (
            username,
            study_duration_minutes,
            concentration_avg,
            concentration_max,
            concentration_min,
            ratio_high,
            ratio_medium,
            ratio_low,
            ratio_zero,
            light_r,
            light_g,
            light_b,
            light_brightness,
            timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    study_values = (
        username,
        0,
        conc_avg,
        int(conc_max),
        int(conc_min),
        ratio_high,
        ratio_medium,
        ratio_low,
        ratio_zero,
        light_values['r'],
        light_values['g'],
        light_values['b'],
        light_values['brightness'],
        now
    )

    cursor.execute(study_sql, study_values)
    session_id = cursor.lastrowid

    # data.jsonを更新
    analysis_data = {
        'is_sleeping': is_sleeping,
        'concentration': concentration_category,
        'conc_avg': conc_avg,
        'conc_max': int(conc_max),
        'conc_min': int(conc_min)
    }
    update_data_json(analysis_data, data)

    # ai_analysis_resultsに詳細を保存
    ai_sql = '''
        INSERT INTO ai_analysis_results (
            session_id,
            status,
            is_sleeping,
            concentration,
            raw_response,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
    '''

    ai_values = (
        session_id,
        'processed_by_colab',
        is_sleeping,
        concentration_category,
        json.dumps(data, ensure_ascii=False, indent=2),
        now
    )

    cursor.execute(ai_sql, ai_values)
    result_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return session_id, result_id


@app.route('/webhook', methods=['POST'])
def receive_result():
    data = request.json

    print(f"\n{'='*40}")
    print(f" 受信: {datetime.now()}")
    print(f"動画: {data.get('video_path')}")
    print(f"予測数: {data.get('num_predictions')}")
    
    print(f"   Timestamp: {data.get('timestamp')}")

    if 'summary' in data:
        print(f"   集中: {data['summary']['集中']:.1f}%")
        print(f"   眠気: {data['summary']['眠気']:.1f}%")
        print(f"   寝落ち: {data['summary']['寝落ち']:.1f}%")
        print(f"   平均集中度: {data['avg_concentration']:.3f}")

    try:
        session_id, result_id = save_ai_result_to_db(data)

        # 保存されたライト情報とユーザー名を取得
        light_values = get_current_light_values()
        username = get_username_from_data_json()

        # 集中度統計を計算（表示用）
        time_series = data.get('time_series_data', [])
        if time_series:
            concentration_scores = [(1 - item.get('drowsy_score', 0)) * 100 for item in time_series]
            conc_max = max(concentration_scores) if concentration_scores else 0
            conc_min = min(concentration_scores) if concentration_scores else 0
            conc_avg = sum(concentration_scores) / len(concentration_scores) if concentration_scores else 0
        else:
            avg_conc = data.get('avg_concentration', 0)
            conc_max = avg_conc * 100
            conc_min = avg_conc * 100
            conc_avg = avg_conc * 100

        # ログファイルに書き出し
        conc_stats = {
            'avg': conc_avg,
            'max': conc_max,
            'min': conc_min
        }
        write_to_log(data, session_id, result_id, light_values, conc_stats)

        print(f"\n DB保存完了:")
        print(f"   セッションID: {session_id}")
        print(f"   結果ID: {result_id}")
        print(f"   ユーザー: {username}")
        print(f"   集中度: 平均={conc_avg:.1f}% 最大={conc_max:.1f}% 最小={conc_min:.1f}%")
        print(f"   ライト: RGB({light_values['r']}, {light_values['g']}, {light_values['b']}) 輝度: {light_values['brightness']}%")

        return jsonify({
            'status': 'received',
            'session_id': session_id,
            'result_id': result_id
        })
    
    except Exception as e:
        print(f" DB保存エラー: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == '__main__':
    # 0.0.0.0で外部からアクセス可能に
    app.run(host='0.0.0.0', port=8080)
