import cv2
import dlib
import numpy as np
import time

# --- dlib 顔検出器の準備 ---
# dlib に標準搭載されているHOGベースの顔検出器をロード
try:
    detector = dlib.get_frontal_face_detector()
except ImportError:
    print("エラー: 'dlib' ライブラリが見つかりません。")
    print("仮想環境で 'pip install dlib' を実行してください。")
    exit()

print("dlib 顔検出器を正常に読み込みました。")
# ------------------------------------

# ラズパイが配信しているMJPEGストリームのURL
# !!! ここのIPアドレスをあなたのラズパイのIPアドレスに変更してください !!!
stream_url = 'http://192.168.11.10:5000/video_feed'

# URLを開く
cap = cv2.VideoCapture(stream_url)

# 接続確認
if not cap.isOpened():
    print("エラー: ストリームを開けませんでした。")
    print("URLが正しいか、ラズパイ側でサーバーが起動しているか確認してください。")
    exit()

print("ストリームに接続しました。'q'キーで終了します。")

# リアルタイムでフレームを読み込み続ける
while True:
    # 1フレーム読み込む
    ret, frame = cap.read()

    # 読み込みが失敗したら（ストリームが途切れたら）終了
    if not ret:
        print("ストリームが切れました。")
        # 'overread' エラー対策: 接続が切れたら再接続を試みる
        print("5秒後に再接続を試みます...")
        cap.release()
        time.sleep(5)
        cap = cv2.VideoCapture(stream_url)
        if not cap.isOpened():
            print("再接続に失敗しました。終了します。")
            break
        continue

    # --- ここでPC側でのAI処理 (dlib 顔検出) ---

    # 画像をグレースケールに変換 (dlibのHOG検出器はグレースケール画像で動作)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 顔検出を実行 (第2引数の 0 はアップサンプリングしないことを意味し、高速)
    faces = detector(gray, 0)

    # 検出した顔を四角で囲む
    # dlibが返す 'faces' は bounding box のリスト (dlib.rectangles)
    for face in faces:
        x = face.left()
        y = face.top()
        w = face.width()
        h = face.height()
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)  # 青色の四角を描画

    # ------------------------------------

    # 読み込んだフレームを 'Stream' という名前のウィンドウに表示
    cv2.imshow('Raspberry Pi Stream (dlib Face Detection)', frame)  # ウィンドウ名を変更

    # 'q' キーが押されたらループを抜ける
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 後片付け
cap.release()
cv2.destroyAllWindows()
