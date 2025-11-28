import cv2
import numpy as np
import mediapipe as mp  # MediaPipeをインポート


class UpperBodyDetector:
    """
    MediaPipe Pose を使用して、上半身（人間）を検出するクラス。
    (Haar Cascadeより格段に高速・高精度)
    """

    def __init__(self, cascade_path=None):
        """
        MediaPipe Pose 検出器を初期化する。
        """
        # MediaPipe Pose のソリューションを準備
        self.mp_pose = mp.solutions.pose

        # Pose検出器のインスタンスを作成
        # min_detection_confidence:
        #   0.5 = 50%以上の信頼度で人間として検出
        self.pose = self.mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0  # 0が最速の "Lite" モデル
        )

        # (オプション) 検出結果を描画するためのユーティリティ
        self.mp_drawing = mp.solutions.drawing_utils

        print("MediaPipe Pose (Liteモデル) を正常に読み込みました。")

    def process_frame(self, frame):
        """
        【 外部から呼び出すメイン関数 】
        1フレームを処理し、人間を検出する。

        :param frame: BGR画像 (numpy array)
        :return: (processed_frame, detected_items)
        """

        processed_frame = frame.copy()
        detected_items = []

        # --- MediaPipeでの検出 ---
        # 1. BGR -> RGB に変換 (MediaPipeはRGBを入力として要求する)
        image_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)

        # 2. 検出を実行
        results = self.pose.process(image_rgb)

        # 3. 検出結果 (results.pose_landmarks) が存在するかチェック
        if results.pose_landmarks:
            #  ランドマークが見つかった = 人間（上半身）が見つかった
            detected_items.append("UpperBody")  # main.py が期待する名前を返す

            # (オプション) 検出した骨格を描画する
            # これを有効にすると、main.pyのS1の画面に骨格が表示される
            # self.mp_drawing.draw_landmarks(
            #     processed_frame,
            #     results.pose_landmarks,
            #     self.mp_pose.POSE_CONNECTIONS
            # )
            pass  # 描画しない場合は pass

        return (processed_frame, detected_items)


# --- このファイルが直接実行された場合のテスト動作 ---
def main_stream():
    stream_url = 'http://192.168.11.10:5000/video_feed'  # IPアドレス確認

    try:
        detector = UpperBodyDetector()
    except Exception as e:
        print(f"初期化に失敗しました: {e}")
        exit()

    cap = cv2.VideoCapture(stream_url)
    if not cap.isOpened():
        print("エラー: ストリームを開けませんでした。")
        exit()

    print("ストリームに接続しました。'q'キーで終了します。")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("ストリームが切れました。")
            break

        #  クラスのメソッドを呼び出す
        processed_frame, detections = detector.process_frame(frame)

        if detections:
            print(f"検出: {len(detections)} 件の人間を検出")
            # 検出結果（骨格）を描画したい場合は、
            # 上記 process_frame 内の self.mp_drawing.draw_landmarks の
            # コメントアウトを解除してください。

        cv2.imshow('MediaPipe Pose Test (S1 Detector)', processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # `python -m detect.detect_upperbody` で実行された場合
    main_stream()
