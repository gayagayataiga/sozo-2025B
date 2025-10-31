import cv2
import time
# detect.person_identifier ではなく detect.detect_person からインポート
try:
    from detect.detect_person import PersonIdentifier
except ImportError as e:
    print(f"エラー: PersonIdentifier のインポートに失敗しました。{e}")
    print("detect_person.py が同じ階層の detect フォルダ内にあるか確認してください。")
    exit()

# 処理したいストリームのURLを指定
STREAM_URL = 'http://192.168.11.10:5000/video_feed'

print("顔識別器を初期化します...")
try:
    # 初期化 (モデルの読み込みは一度だけ)
    identifier = PersonIdentifier(
        landmark_model_path="./dlib/shape_predictor_68_face_landmarks.dat",
        recognition_model_path="./dlib/dlib_face_recognition_resnet_model_v1.dat",
        known_faces_dir="./known_faces",
        threshold=0.6  # 閾値を0.6に設定
    )
except Exception as e:
    print(f"初期化中にエラーが発生しました: {e}")
    exit()

print("初期化完了。")

# ストリームに接続
print(f"ストリーム ({STREAM_URL}) に接続中...")
cap = cv2.VideoCapture(STREAM_URL)

# カメラが初期化されるのを少し待つ
time.sleep(1.0)

if not cap.isOpened():
    print(f"エラー: ストリーム ({STREAM_URL}) を開けませんでした。")
    print("IPカメラが起動しているか、URLが正しいか確認してください。")
    exit()

print("ストリームに接続しました。1フレーム取得します...")
ret, frame = cap.read()
cap.release()  # 1枚取得したらすぐに解放
print("ストリームを解放しました。")

if ret:
    print("フレームを取得。顔分析を実行します...")
    # ★ processed_image はもう使わないので、変数名を _ (アンダーバー) にしてもOK
    processed_image, names = identifier.process_frame(frame)

    if names:
        print(f"検出結果: {names}")

        # --- ★★★ ここから変更 ★★★ ---

        recognized_count = 0
        # 検出された名前のリストをループ
        for name in names:
            # "Unknown" で始まらない名前 (＝登録済みの名前) の場合
            if not name.startswith("Unknown"):
                print(f"\n👋 Hello {name} ! 👋")
                recognized_count += 1

        if recognized_count == 0 and len(names) > 0:
            print("（認識済みの顔は見つかりませんでした）")

        # --- ★★★ ここまで変更 ★★★ ---

    else:
        print("顔は検出されませんでした。")

else:
    print("エラー: ストリームからフレームを取得できませんでした。")
