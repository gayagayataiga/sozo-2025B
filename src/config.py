# config.py: アプリケーションの設定値

import sys

# --- 実行環境設定 ---
# 使うPythonの実行ファイルパス（ai.pyのサブプロセス起動用）
# 基本的に変更不要
PYTHON_EXECUTABLE = sys.executable

# --- ネットワーク設定 (Raspberry Pi / EV3) ---
# ラズベリーパイのIPアドレス (環境に合わせて変更)
RASPBERRY_PI_IP = "10.27.72.43"

# 映像ストリームのポートとパス
STREAM_PORT = 5001
STREAM_PATH = "/video_feed"
STREAM_URL = f'http://{RASPBERRY_PI_IP}:{STREAM_PORT}{STREAM_PATH}'
# 構築されるURL: f"http://{RASPBERRY_PI_IP}:{STREAM_PORT}{STREAM_PATH}"

# ストリーム接続時の安定待ち時間 (秒)
STREAM_STABILIZATION_WAIT = 1.0

# --- SwitchBot API設定 ---
# (注: 元のコードでは別ファイルからインポートしていましたが、
#  本来config.pyに集約すべき項目です)
SWITCHBOT_TOKEN = "YOUR_SWITCHBOT_TOKEN_HERE"
SWITCHBOT_SECRET = "YOUR_SWITCHBOT_SECRET_HERE"
SWITCHBOT_TARGET_DEVICE_ID = "YOUR_TARGET_DEVICE_ID_HERE"

# --- 状態定義 ---
# (コードの可読性のため、ここに定義)
STATE_SEARCHING_BODY = 1
STATE_SEARCHING_FACE = 2
STATE_ANALYZING_FACE = 3

# --- AI・分析関連の閾値 (チューニング用) ---

# AI分析のクールダウンタイム (秒)
# この秒数ごとに1回、AI分析(ai.py)をトリガーする
AI_COOLDOWN_SECONDS = 5

# AIに渡す時系列データの最大長 (フレーム数)
HISTORICAL_DATA_MAXLEN = 30

# 顔分析の閾値
# EAR (Eye Aspect Ratio): この値未満で「閉じている」と判定
EAR_THRESHOLD = 0.20

# MAR (Mouth Aspect Ratio): この値以上で「開いている」と判定
MAR_THRESHOLD = 0.5

# Yaw (顔の左右の傾き): ±この値を超えると「横向き」と判定
YAW_THRESHOLD = 15.0

# --- ファイル名定義 ---
# メインプロセス -> AIプロセスへ渡すデータファイル
AI_INPUT_FILENAME = 'ai_input.json'

# AIプロセス -> メインプロセスへ返す結果ファイル
AI_RESULT_FILENAME = 'ai_result.json'

# AIプロセスの実行ログファイル
AI_LOG_FILENAME = 'ai_log.txt'

# サーバー(Web UI)と共有するデータファイル
SHARED_DATA_FILENAME = 'data.json'

# AI (サブプロセス) のスクリプト名
AI_SCRIPT_FILENAME = 'ai.py'

# --- その他 ---
# ファイルI/O（入出力）の競合を避けるための小さな遅延 (秒)
FILE_OPERATION_DELAY_SHORT = 0.3
FILE_OPERATION_DELAY_TINY = 0.01


# server.pyで使う変数
# 'index.html'があるtemplatesのパス
INDEX_HTML_PATH = 'website/test-site/templates'
# jsなどのコードがあるstaticのパス
STATIC_FILES_PATH = 'website/test-site/static'


# 集中度レベルの定義
CONCENTRATION_LEVELS = ["低", "中", "高", "ゾーン"]

# main.py が読み取るファイル
# webサイトからの指示でモーターを動かすためのファイル
MOVE_MOTORS_JSON_PATH = "moveMotors.json"

# ブラウザからの「操作」を受け取るURL
BROWSER_CONTROL_URL = "/api/control"

# 電源に関係する命令
POWER_COMMAND = "power_toggle"

# 明るさに関係する命令
BRIGHTNESS_COMMAND = "set_brightness"

# 色相環に関係する命令
COLOR_WHEEL_COMMAND = "set_color_wheel"

# 肘を動かす命令の判別
ELBOW_MOVE_COMMAND = 'set_angle_elbow'

# 手首を動かす命令の判別
WRIST_MOVE_COMMAND = 'set_angle_wrist'

# ブラウザから送られてくるactionのjsonキー
ACTION_KEY = 'action'

# ブラウザから送られてくるvalueのjsonキー
VALUE_KEY = 'value'

# aiの分析結果のjsonキー
AI_RESULT_KEY = 'ai_analysis'

# 分析したjsonの中の分析結果,analysisキー
AI_ANALYSIS_KEY = 'analysis'

# aiの分析結果内の集中度のキー
AI_CONCENTRATION_KEY = 'concentration'

# aiの分析結果で何もできなかった、受け取れなかったときの値
AI_ANALYSIS_ERROR_VALUE = 'Unknown'

# aiの分析結果内の睡眠状態のキー
AI_SLEEPING_KEY = 'is_sleeping'
