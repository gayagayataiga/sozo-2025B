import cv2
import time
import subprocess  # 非同期で別プロセスを起動するため
import json       # データの受け渡し（書き込み）のため
import os         # ファイルの存在確認・削除のため
import numpy as np  # 顔ランドマーク(Numpy配列)をJSONに変換するため
import sys
from collections import deque
# キューを使って、最大の長さが30のデータを確実に送る
# AIの推論がどれだけ遅くなるかわからないし、早いかもしれないので、固定長のキューを使う
historical_data = deque(maxlen=30)

# 使うpythonの実行ファイルパスを取得
# ai.pyをサブプロセスで起動する際に同じPython環境を使うため
# これがないとただのpythonになり、仮想環境に入っているライブラリを使えない
python_executable = sys.executable
print(f"使用するPythonインタプリタ: {python_executable}")

# --- 各モジュールから「クラス」をインポート ---
try:
    # pythonファイルのパスを通す
    # もしかしたらimportできないかもしれないので、try-exceptで囲む
    from detect.detect_upperbody import UpperBodyDetector
    from detect.detect_person import PersonIdentifier
    from switchbot_python.switchbot_API_test import TOKEN, SECRET, TARGET_DEVICE_ID, generate_auth_headers, send_command
    from serverFolder.sendrasev3command import EV3Commander
except ImportError as e:
    print(f"エラー: モジュールのインポートに失敗しました。{e}")
    exit()

# ラズベリーパイからくる映像ストリームのURL
# 家、TeaLab,TeaClassで全然違うので注意
# ラズパイのIPアドレス
RASPBERRY_PI_IP = "10.27.75.121"
STREAM_URL = f'http://{RASPBERRY_PI_IP}:5001/video_feed'

# ev3との通信を定義
print(f"EV3通信機を IP: {RASPBERRY_PI_IP} で初期化します...")
ev3_communicator = EV3Commander(RASPBERRY_PI_IP)

# --- 状態定義 ---
# 上から順に上半身を探す -> 顔を探す -> 顔を分析・追跡
# これを行うことで、無駄な処理を減らす
STATE_SEARCHING_BODY = 1
STATE_SEARCHING_FACE = 2
STATE_ANALYZING_FACE = 3

# --- AIモデルの初期化 ---
# ここでAIモデルを初期化しておくことで、毎フレームの処理が速くなる
# 毎回の初期化をなくす→ 処理が速くなる
print("AIモデルを初期化しています...")
try:
    detector_body = UpperBodyDetector()
    identifier_person = PersonIdentifier()
except Exception as e:
    print(f"モデルの初期化中にエラーが発生しました: {e}")
    exit()
print("--- モデル初期化完了 ---")

# --- ビデオストリームの初期化 ---
# ラズベリーパイからの映像を取得（パソコンのカメラの時もあった）
cap = cv2.VideoCapture(STREAM_URL)
if not cap.isOpened():
    print(f"エラー: ストリーム '{STREAM_URL}' を開けませんでした。")
    exit()
# 少し待つことで、ストリームが安定する
# 真っ暗な画面とかなりにくそうだよね
time.sleep(1.0)
print("ストリームに接続しました。'q'で終了します。")

# --- メインループ ---
# 最初は上半身を探す状態から開始
current_state = STATE_SEARCHING_BODY
# AIのプロセスを速くしすぎないように調整する
ai_process = None  # AIプロセスの状態を管理
last_ai_trigger_time = 0  # AIを最後に実行した時刻
AI_COOLDOWN_SECONDS = 5  # AIの実行クールダウン（5秒）


# --- Numpy配列をJSONに変換するためのヘルパー関数 ---
# 顔の68個の点をAIに渡すときに使うかもだけど、今は使ってない
# それを使えるモデルが見つからない→作らないといけない
class NumpyEncoder(json.JSONEncoder):
    """ Numpy配列をJSONシリアライズ可能にするためのクラス """

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()  # Numpy配列をPythonのリストに変換
        return json.JSONEncoder.default(self, obj)


# 常時回るコード
while True:
    ret, frame = cap.read()
    if not ret:
        print("ストリームが切れました。")
        break

    display_frame = frame.copy()

    # 上半身を検知する段階
    if current_state == STATE_SEARCHING_BODY:
        # 上半身を検知する関数→ 返り値は表示用フレームと検出結果のリスト
        # 見つからなかったら空リストが返ってくる構成
        display_frame, body_list = detector_body.process_frame(frame)

        if len(body_list) > 0:
            # 上半身が見つかった場合、顔認識モードに移行
            print("[S1 -> S2] 上半身を検出。顔認識モードに移行します。")
            current_state = STATE_SEARCHING_FACE
        else:
            # 上半身が見つからなかった場合、探索を継続
            # 画面上にその旨を表示
            cv2.putText(display_frame, "STATE 1: Searching for person...",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # 顔を検知する段階
    elif current_state == STATE_SEARCHING_FACE:
        # 顔を検知する関数→ 返り値は表示用フレームと検出結果のリスト
        display_frame, face_results = identifier_person.process_frame(
            frame, mode="identify")

        if len(face_results) > 0:
            # 顔が見つかった場合、分析・追跡モードに移行
            # 顔を検知するだけでなく、識別も行う
            print("[S2 -> S3] 顔を検出・識別しました。分析・追跡を継続します。")
            current_state = STATE_ANALYZING_FACE

            # --- 一度だけ挨拶 (MARやPoseも表示) ---
            for face in face_results:
                name = face["name"]
                if not name.startswith("Unknown"):
                    print(f" Hello {name}!")
                    # MAR (口) と Pose (P/Y/R) も表示
                    print(
                        f"  (初回 EAR: {face['ear']:.2f}, MAR: {face['mar']:.2f})")
                    print(
                        f"  (初回 Pose: P={face['pitch']:.1f}, Y={face['yaw']:.1f}, R={face['roll']:.1f})")
                else:
                    print(f"  (Unknown の顔 {name} を検出)")

        else:
            _, body_list = detector_body.process_frame(frame)
            if len(body_list) == 0:
                print("[S2 -> S1] 顔も上半身も見失いました。探索を再開します。")
                current_state = STATE_SEARCHING_BODY
            else:
                cv2.putText(display_frame, "STATE 2: Person found. Come closer...",
                            (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

    elif current_state == STATE_ANALYZING_FACE:
        display_frame, face_results = identifier_person.process_frame(
            frame, mode="analyze_only")

        if len(face_results) > 0:
            # --- 追跡継続中 (ログにMARとYawを表示) ---
            for face in face_results:
                name = face['name']
                ear = face['ear']
                mar = face['mar']
                yaw = face['yaw']
                pitch = face['pitch']  # 上下の傾きも利用可能
                roll = face['roll']   # 回転も利用可能

                # 1. 目の状態 (EAR)
                # ※ 閾値 (0.2) は環境や人によって調整が必要です
                eye_status = "開いている"
                if ear < 0.20:
                    eye_status = "閉じている "

                # 2. 口の状態 (MAR)
                # ※ 閾値 (0.5) は調整が必要です
                mouth_status = "閉じている"
                if mar > 0.5:
                    mouth_status = "開いている "

                # 3. 顔の向き (Yaw)
                # ※ 閾値 (15.0) は調整が必要です
                pose_status = "正面"
                if yaw > 15.0:
                    pose_status = "右向き ➡️"
                elif yaw < -15.0:
                    pose_status = "左向き ⬅️"

                # 解釈した結果を出力
                print(
                    f"[S3] {name}: [目: {eye_status}(E:{ear:.2f})] [口: {mouth_status}(M:{mar:.2f})]")
                print(
                    f"     -> [Pose: P={pitch:.1f}, Y={yaw:.1f}, R={roll:.1f}]")

                current_frame_data = {
                    'timestamp': time.time(),  # ★タイムスタンプを必ず入れる
                    'ear': ear,
                    'mar': mar,
                    'pose_P': pitch,
                    'pose_Y': yaw,
                    'pose_R': roll,
                    # 必要であればランドマークも
                    # 'landmarks': face['landmarks']
                }
                historical_data.append(current_frame_data)

                # 1. AIプロセスが現在実行中か？
                ai_is_running = ai_process and ai_process.poll() is None

                # 2. 現在時刻がクールダウンを経過しているか？
                can_trigger_ai = (
                    time.time() - last_ai_trigger_time) > AI_COOLDOWN_SECONDS

                # ... (AIトリガーの判定) ...
                if not ai_is_running and can_trigger_ai:

                    # ★データが十分溜まってからAIを起動する
                    if len(historical_data) < historical_data.maxlen:
                        # まだデータが溜まっていない場合はスキップ
                        print(
                            f"--- AI分析待機中 (データ収集中 {len(historical_data)}/{historical_data.maxlen}個) ---")
                    else:
                        print("---  AI分析を非同期でトリガーします ---")

                        # 3. AIに渡すデータを準備 (キューをリストに変換して渡す)
                        ai_input_data = {
                            'name': name,
                            'time_series_data': list(historical_data)
                        }

                        # 4. データをJSONファイルとして一時保存
                        with open('ai_input.json', 'w') as f:
                            json.dump(ai_input_data, f, cls=NumpyEncoder)

                    # 出力ログファイル名を定義
                    ai_logfile_path = "ai_log.txt"

                    try:
                        # ログファイルを 'w' (上書き) モードで開く
                        with open(ai_logfile_path, 'w', encoding='utf-8') as log_file:
                            # Popenで ai.py を非同期起動
                            # stdout (print) と stderr (エラー) の両方をログファイルに書き込む
                            ai_process = subprocess.Popen(
                                [python_executable, "ai.py"],
                                stdout=log_file,
                                stderr=log_file
                            )

                        last_ai_trigger_time = time.time()  # 実行時刻を更新
                        print(f"--- AI起動成功。ログは {ai_logfile_path} を確認 ---")
                    except Exception as e:
                        print(f"---  AIの起動に失敗しました: {e} ---")

        else:
            #  全員見失ったら S1 に戻る
            print("[S3 -> S1] 顔の追跡をロスト。上半身から探索を再開します。")
            current_state = STATE_SEARCHING_BODY

    time.sleep(0.3)  # ファイル削除の小さな遅延

    result_file = 'ai_result.json'
    if os.path.exists(result_file):
        print("---  AIの結果ファイル (ai_result.json) を検出！ ---")
        try:
            # AIの結果を読み込む
            with open(result_file, 'r') as f:
                ai_data = json.load(f)

            # サーバー用の共有ファイル (data.json) を更新する
            # (ここでは、既存のdata.jsonにAIデータを追記/更新する想定)

            # まず既存のdata.jsonを読み込む (なければ作成)
            shared_data = {}
            if os.path.exists('data.json'):
                with open('data.json', 'r') as f:
                    try:
                        shared_data = json.load(f)
                    except json.JSONDecodeError:
                        pass  # ファイルが空などの場合は無視

            # AIデータを 'ai_analysis' キーとして更新
            shared_data['ai_analysis'] = ai_data

            # data.json に書き戻す
            with open('data.json', 'w') as f:
                json.dump(shared_data, f, indent=4)

            print(f"--- data.json を更新しました: {ai_data} ---")

            # 処理済みの結果ファイルを削除
            os.remove(result_file)
            time.sleep(0.01)  # ファイル削除の小さな遅延

        except Exception as e:
            print(f"AI結果ファイルの処理中にエラー: {e}")
            if os.path.exists(result_file):
                os.remove(result_file)  # エラー時もファイルを削除して無限ループを防ぐ

    cv2.imshow("Main Controller (Brain)", display_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("プログラムを終了しました。")
