# import cv2
# import dlib
# import numpy as np
# import time
# import os
# import glob
# from imutils import face_utils

# # --- 分析モジュールをインポート ---
# try:
#     from analyze.analyze_face import FaceAnalyzer
# except ImportError:
#     print("エラー: 'analyze/analyze_face.py' が見つかりません。")
#     print("同じ階層に 'analyze' フォルダを作成し、その中に 'analyze_face.py' を配置してください。")
#     exit()
# # ------------------------------------

# # --- グローバル定数 (デフォルト値) ---
# # これらの値は、クラス初期化時に外部から上書き可能
# DEFAULT_KNOWN_FACES_DIR = "./known_faces"
# DEFAULT_LANDMARK_MODEL = "./dlib/shape_predictor_68_face_landmarks.dat"
# DEFAULT_REC_MODEL = "./dlib/dlib_face_recognition_resnet_model_v1.dat"
# DEFAULT_THRESHOLD = 0.6  # ★ 1.0 から 0.6 に修正
# DEFAULT_COOLDOWN = 5.0


# class PersonIdentifier:
#     """
#     顔の検出、分析、識別、および「Unknown」の登録を行うクラス。
#     """

#     def __init__(self,
#                  landmark_model_path=DEFAULT_LANDMARK_MODEL,
#                  recognition_model_path=DEFAULT_REC_MODEL,
#                  known_faces_dir=DEFAULT_KNOWN_FACES_DIR,
#                  threshold=DEFAULT_THRESHOLD,
#                  cooldown=DEFAULT_COOLDOWN):
#         """
#         クラスの初期化時に、モデルの読み込みと登録済み顔のスキャンを行う。
#         """

#         # 定数の設定
#         self.KNOWN_FACES_DIR = known_faces_dir
#         self.RECOGNITION_THRESHOLD = threshold
#         self.UNKNOWN_SAVE_COOLDOWN = cooldown

#         # dlib モデルの準備
#         self.detector = dlib.get_frontal_face_detector()
#         try:
#             self.analyzer = FaceAnalyzer(
#                 landmark_model_path=landmark_model_path,
#                 recognition_model_path=recognition_model_path
#             )
#         except FileNotFoundError as e:
#             print(f"分析モデルの読み込みに失敗: {e}")
#             raise  # 初期化失敗時はエラーを上位に投げる
#         print("dlib 顔検出器と分析モデルを正常に読み込みました。")

#         # 登録済み顔データのロード
#         self.known_encodings, self.known_names = self._register_known_faces()
#         if len(self.known_encodings) == 0:
#             print("[WARN] 登録済みの顔がありません。全ての顔は 'Unknown' と表示されます。")

#         # Unknown保存用の設定
#         self.last_save_time = 0
#         self.unknown_counter = self._get_unknown_counter()
#         print(
#             f"[INFO] 現在のUnknown最大番号: {self.unknown_counter} (次に保存する際は {self.unknown_counter + 1} を使用します)")

#     def _register_known_faces(self):
#         """
#         (内部メソッド) KNOWN_FACES_DIR から顔写真を読み込む。
#         (前回修正した、1フォルダ1枚のロジックを含む)
#         """
#         known_encodings = []
#         known_names = []
#         print(f"[INFO] '{self.KNOWN_FACES_DIR}' から登録済みの顔をスキャン中...")

#         if not os.path.exists(self.KNOWN_FACES_DIR):
#             print(f"[WARN] 登録用フォルダ '{self.KNOWN_FACES_DIR}' が見つかりません。")
#             return known_encodings, known_names

#         for person_name in os.listdir(self.KNOWN_FACES_DIR):
#             person_dir = os.path.join(self.KNOWN_FACES_DIR, person_name)
#             if not os.path.isdir(person_dir):
#                 continue

#             image_files = []
#             extensions = ["*.jpg", "*.png", "*.jpeg"]
#             for ext in extensions:
#                 image_files.extend(glob.glob(os.path.join(person_dir, ext)))

#             if not image_files:
#                 continue

#             # 各フォルダの最初の1枚の画像のみを登録対象とする
#             for image_name in image_files:
#                 print(f"  > 登録処理中: {image_name} (名前: {person_name})")
#                 image = cv2.imread(image_name)
#                 if image is None:
#                     print(f"    [WARN] 画像 {image_name} を読み込めません。スキップします。")
#                     continue

#                 gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
#                 faces = self.detector(gray, 1)

#                 if len(faces) != 1:
#                     print(f"    [WARN] {image_name} 内の顔が1人ではありません。")
#                     continue

#                 face = faces[0]

#                 try:
#                     (ear, tilt, face_encoding) = self.analyzer.analyze(
#                         gray, face, image.shape, image)

#                     known_encodings.append(face_encoding)
#                     known_names.append(person_name)

#                     print(f"    [OK] {person_name} を登録しました。")
#                     break  # ★ 1人につき1つの顔を登録したら、次の人物フォルダへ
#                 except Exception as e:
#                     print(f"    [ERROR] {image_name} の分析中にエラーが発生しました: {e}")

#         print(f"[INFO] 登録完了。 {len(known_names)} 件の顔データをロードしました。")
#         return known_encodings, known_names

#     def _get_unknown_counter(self):
#         """ (内部メソッド) 既存の Unknown フォルダの最大番号を取得 """
#         unknown_counter = 0
#         if os.path.exists(self.KNOWN_FACES_DIR):
#             for dir_name in os.listdir(self.KNOWN_FACES_DIR):
#                 if dir_name.startswith("Unknown_") and os.path.isdir(os.path.join(self.KNOWN_FACES_DIR, dir_name)):
#                     try:
#                         num = int(dir_name.split('_')[1])
#                         if num > unknown_counter:
#                             unknown_counter = num
#                     except (IndexError, ValueError):
#                         continue
#         return unknown_counter

#     def process_frame(self, frame):
#         """
#         【★ 外部から呼び出すメイン関数 ★】
#         1フレームを処理し、検出結果を描画したフレームと、検出した名前のリストを返す。

#         :param frame: BGR画像 (numpy array)
#         :return: (processed_frame, detected_names)
#                  processed_frame: 名前のバウンディングボックスが描画されたフレーム
#                  detected_names: 検出された名前（"Unknown_1" や "Tanaka" など）のリスト
#         """

#         processed_frame = frame.copy()  # 元のフレームを変更しないようにコピー
#         analysis_results = []

#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         faces = self.detector(gray, 0)  # 高速化のためアップサンプリングなし

#         for face in faces:
#             (x, y, w, h) = face_utils.rect_to_bb(face)

#             try:
#                 # 顔分析 (EAR, Tilt, Encoding)
#                 (avg_ear, head_tilt, new_encoding) = self.analyzer.analyze(
#                     gray, face, frame.shape, frame)
#             except Exception as e:
#                 # ランドマーク検出失敗など
#                 print(f"[WARN] 顔分析中にエラー: {e}。この顔をスキップします。")
#                 continue

#             name = "Unknown"

#             # --- 登録済みデータと比較 ---
#             if len(self.known_encodings) > 0:
#                 distances = np.linalg.norm(
#                     self.known_encodings - new_encoding, axis=1)
#                 min_distance = np.min(distances)
#                 best_match_index = np.argmin(distances)

#                 if min_distance < self.RECOGNITION_THRESHOLD:
#                     name = self.known_names[best_match_index]

#             # --- Unknown の顔を保存 ---
#             if name == "Unknown":
#                 current_time = time.time()
#                 # クールダウンチェック
#                 if (current_time - self.last_save_time) > self.UNKNOWN_SAVE_COOLDOWN:

#                     self.unknown_counter += 1
#                     new_person_name = f"Unknown_{self.unknown_counter}"
#                     save_dir = os.path.join(
#                         self.KNOWN_FACES_DIR, new_person_name)
#                     os.makedirs(save_dir, exist_ok=True)

#                     timestamp = time.strftime("%Y%m%d_%H%M%S")
#                     filename = os.path.join(save_dir, f"{timestamp}.jpg")

#                     # 顔部分を切り出し
#                     padding = 20
#                     (h_frame, w_frame, _) = frame.shape
#                     x1 = max(0, x - padding)
#                     y1 = max(0, y - padding)
#                     x2 = min(w_frame, x + w + padding)
#                     y2 = min(h_frame, y + h + padding)
#                     face_image = frame[y1:y2, x1:x2]

#                     if face_image.size > 0:
#                         cv2.imwrite(filename, face_image)
#                         print(f"[INFO] 新しい顔を保存しました: {filename}")

#                         # ★ 動的に「既知」リストに追加
#                         self.known_encodings.append(new_encoding)
#                         self.known_names.append(new_person_name)
#                         print(f"[INFO] {new_person_name} をセッション中の記憶に追加しました。")

#                         self.last_save_time = current_time
#                         name = new_person_name  # ★ 描画する名前を更新
#                     else:
#                         print(f"[WARN] 顔画像の切り出しに失敗しました (サイズ0)。")
#                         self.unknown_counter -= 1  # カウンタを戻す

#             # 検出したすべての情報を辞書としてリストに追加
#             result_data = {
#                 "name": name,
#                 "ear": avg_ear,
#                 "tilt": head_tilt,
#                 "bbox": (x, y, w, h)
#                 # "encoding": new_encoding # 必要ならこれも追加
#             }
#             analysis_results.append(result_data)

#             # --- 結果を描画 ---
#             cv2.rectangle(processed_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
#             cv2.putText(processed_frame, name, (x, y - 10),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

#         # 処理済みフレームと名前リストを返す
#         return (processed_frame, analysis_results)


# # --- 従来のメイン処理 (このファイルが直接実行された場合) ---
# def main_stream():
#     STREAM_URL = 'http://192.168.11.10:5000/video_feed'

#     # クラスを初期化 (デフォルト値を使用)
#     try:
#         identifier = PersonIdentifier(
#             landmark_model_path=DEFAULT_LANDMARK_MODEL,
#             recognition_model_path=DEFAULT_REC_MODEL,
#             known_faces_dir=DEFAULT_KNOWN_FACES_DIR,
#             threshold=DEFAULT_THRESHOLD
#         )
#     except Exception as e:
#         print(f"初期化に失敗しました: {e}")
#         exit()

#     # ストリーム接続
#     cap = cv2.VideoCapture(STREAM_URL)
#     if not cap.isOpened():
#         print(f"エラー: ストリーム '{STREAM_URL}' を開けませんでした。")
#         exit()
#     print("ストリームに接続しました。'q'キーで終了します。")

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             print("ストリームが切れました。5秒後に再接続を試みます...")
#             cap.release()
#             time.sleep(5)
#             cap = cv2.VideoCapture(STREAM_URL)
#             if not cap.isOpened():
#                 print("再接続に失敗しました。終了します。")
#                 break
#             continue

#         # ★ クラスのメソッドを呼び出す ★
#         processed_frame, detected_names = identifier.process_frame(frame)

#         if detected_names:
#             # ターミナルにも検出結果を表示 (オプション)
#             print(f"検出: {detected_names}")

#         # 読み込んだフレームを表示
#         cv2.imshow('Raspberry Pi Stream (Person Identification)',
#                    processed_frame)

#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     # 後片付け
#     cap.release()
#     cv2.destroyAllWindows()


# if __name__ == "__main__":
#     # python -m detect.detect_person で実行された場合
#     main_stream()

import cv2
import dlib
import numpy as np
import time
import os
import glob
from imutils import face_utils

# --- 分析モジュールをインポート ---
try:
    from analyze.analyze_face import FaceAnalyzer
except ImportError:
    print("エラー: 'analyze/analyze_face.py' が見つかりません。")
    exit()
# ------------------------------------

# (デフォルト値の定数定義は省略)
DEFAULT_KNOWN_FACES_DIR = "./known_faces"
DEFAULT_LANDMARK_MODEL = "./dlib/shape_predictor_68_face_landmarks.dat"
DEFAULT_REC_MODEL = "./dlib/dlib_face_recognition_resnet_model_v1.dat"
DEFAULT_THRESHOLD = 0.4
DEFAULT_COOLDOWN = 5.0

predictor = dlib.shape_predictor("dlib/shape_predictor_68_face_landmarks.dat")
detector = dlib.get_frontal_face_detector()


class PersonIdentifier:
    """
    顔の検出、分析、識別、追跡を行うクラス。
    """

    def __init__(self,
                 landmark_model_path=DEFAULT_LANDMARK_MODEL,
                 recognition_model_path=DEFAULT_REC_MODEL,
                 known_faces_dir=DEFAULT_KNOWN_FACES_DIR,
                 threshold=DEFAULT_THRESHOLD,
                 cooldown=DEFAULT_COOLDOWN):

        # (元の __init__ と同じ)
        self.KNOWN_FACES_DIR = known_faces_dir
        self.RECOGNITION_THRESHOLD = threshold
        self.UNKNOWN_SAVE_COOLDOWN = cooldown

        self.detector = dlib.get_frontal_face_detector()
        try:
            self.analyzer = FaceAnalyzer(
                landmark_model_path=landmark_model_path,
                recognition_model_path=recognition_model_path
            )
        except FileNotFoundError as e:
            print(f"分析モデルの読み込みに失敗: {e}")
            raise
        print("dlib 顔検出器と分析モデルを正常に読み込みました。")

        self.known_encodings, self.known_names = self._register_known_faces()
        if len(self.known_encodings) == 0:
            print("[WARN] 登録済みの顔がありません。")

        self.last_save_time = 0
        self.unknown_counter = self._get_unknown_counter()
        print(f"[INFO] 現在のUnknown最大番号: {self.unknown_counter}")

        # --- ★ トラッカー用の状態を追加 ---
        self.active_trackers = []  # dlib.correlation_tracker のリスト
        self.tracked_names = {}   # tracker_hash -> "Gayagaya" などの名前

    # --- ( _register_known_faces と _get_unknown_counter は変更なし) ---
    # def _register_known_faces(self):
    #     known_encodings = []
    #     known_names = []
    #     print(f"[INFO] '{self.KNOWN_FACES_DIR}' から登録済みの顔をスキャン中...")
    #     if not os.path.exists(self.KNOWN_FACES_DIR):
    #         print(f"[WARN] 登録用フォルダ '{self.KNOWN_FACES_DIR}' が見つかりません。")
    #         return known_encodings, known_names
    #     for person_name in os.listdir(self.KNOWN_FACES_DIR):
    #         person_dir = os.path.join(self.KNOWN_FACES_DIR, person_name)
    #         if not os.path.isdir(person_dir):
    #             continue
    #         image_files = []
    #         extensions = ["*.jpg", "*.png", "*.jpeg"]
    #         for ext in extensions:
    #             image_files.extend(glob.glob(os.path.join(person_dir, ext)))
    #         if not image_files:
    #             continue
    #         for image_name in image_files:
    #             print(f"  > 登録処理中: {image_name} (名前: {person_name})")
    #             image = cv2.imread(image_name)
    #             if image is None:
    #                 continue
    #             image = normalize_lighting(image)
    #             image = align_face(image)
    #             image = resize_face(image)
    #             gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    #             # faces = self.detector(gray, 1)
    #             # if len(faces) != 1:
    #             #     continue
    #             # face = faces[0]
    #             face_rect = dlib.rectangle(
    #                 # (0, 0, 150, 150) と同義
    #                 0, 0, image.shape[1], image.shape[0])
    #             try:
    #                 #  戻り値が7つになった
    #                 (ear, mar, pitch, yaw, roll, landmarks, face_encoding) = self.analyzer.analyze_full(
    #                     gray, face_rect, image.shape, image)

    #                 known_names.append(person_name)
    #                 known_encodings.append(face_encoding)
    #                 print(f"    [OK] {person_name} を登録しました。")
    #                 break  # 1フォルダ1枚
    #             except Exception as e:
    #                 print(f"    [ERROR] {image_name} の分析中にエラーが発生しました: {e}")
    #     print(f"[INFO] 登録完了。 {len(known_names)} 件の顔データをロードしました。")
    #     return known_encodings, known_names

    def _register_known_faces(self):
        known_encodings = []
        known_names = []
        print(f"[INFO] '{self.KNOWN_FACES_DIR}' から登録済みの顔をスキャン中...")
        if not os.path.exists(self.KNOWN_FACES_DIR):
            print(f"[WARN] 登録用フォルダ '{self.KNOWN_FACES_DIR}' が見つかりません。")
            return known_encodings, known_names

        # ( person_name : 'Gayagaya' や 'Unknown_1' など)
        for person_name in os.listdir(self.KNOWN_FACES_DIR):
            person_dir = os.path.join(self.KNOWN_FACES_DIR, person_name)
            if not os.path.isdir(person_dir):
                continue

            # --- ★ 変更点 1: この人専用のエンコーディングリストを作成 ---
            person_encodings = []

            image_files = []
            extensions = ["*.jpg", "*.png", "*.jpeg"]
            for ext in extensions:
                image_files.extend(glob.glob(os.path.join(person_dir, ext)))

            if not image_files:
                print(f"  [INFO] {person_name} フォルダに画像がありません。")
                continue

            print(f"  > {person_name} の処理を開始 (画像 {len(image_files)} 枚)...")

            for image_name in image_files:
                # print(f"  > 登録処理中: {image_name}") # ログが多すぎる場合はコメントアウト
                image = cv2.imread(image_name)
                if image is None:
                    print(f"    [WARN] {image_name} が読み込めません。")
                    continue

                # --- 認証時と全く同じ前処理を適用 (前回の修正) ---
                image = normalize_lighting(image)
                image = align_face(image)
                image = resize_face(image)  # 150x150
                # -----------------------------------

                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                # 150x150 の画像全体を顔矩形として扱う (前回の修正)
                face_rect = dlib.rectangle(
                    0, 0, image.shape[1], image.shape[0])

                try:
                    (ear, mar, pitch, yaw, roll, landmarks, face_encoding) = self.analyzer.analyze_full(
                        gray,       # 150x150 gray
                        face_rect,  # 150x150 rect
                        image.shape,  # 150x150 shape
                        image)       # 150x150 BGR

                    # --- ★ 変更点 2: 1枚処理するごとに、一時リストに追加 ---
                    person_encodings.append(face_encoding)

                except Exception as e:
                    print(f"    [ERROR] {image_name} の分析中にエラーが発生しました: {e}")

            # --- ★ 変更点 3: 全ての画像を処理した後、平均を計算して登録 ---
            if not person_encodings:
                # 1枚も有効な画像がなかった場合
                print(f"    [WARN] {person_name} は有効な顔画像を登録できませんでした。")
                continue

            # Numpy配列に変換し、平均を計算 (axis=0 はベクトルごとの平均)
            mean_encoding = np.mean(person_encodings, axis=0)

            # 最終的なリストに「名前」と「平均エンコーディング」を追加
            known_names.append(person_name)
            known_encodings.append(mean_encoding)

            print(
                f"    [OK] {person_name} を {len(person_encodings)} 枚の画像の平均で登録しました。")

            # --- ★ 変更点 4: 1枚で終了していた `break` を削除 ---
            # (旧) break  <- これを削除

        print(f"[INFO] 登録完了。 {len(known_names)} 件の顔データをロードしました。")
        return known_encodings, known_names

    def _get_unknown_counter(self):
        unknown_counter = 0
        if os.path.exists(self.KNOWN_FACES_DIR):
            for dir_name in os.listdir(self.KNOWN_FACES_DIR):
                if dir_name.startswith("Unknown_") and os.path.isdir(os.path.join(self.KNOWN_FACES_DIR, dir_name)):
                    try:
                        num = int(dir_name.split('_')[1])
                        if num > unknown_counter:
                            unknown_counter = num
                    except (IndexError, ValueError):
                        continue
        return unknown_counter
    # --- (ここまで変更なし) ---

    def process_frame(self, frame, mode="identify"):
        """
        メインの処理関数。モードに応じて動作を変える。
        mode="identify": (S2用) 顔検出 + 顔認証 (重い)
        mode="analyze_only": (S3用) 顔追跡 + ランドマーク分析 (軽い)
        """

        processed_frame = frame.copy()
        analysis_results = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 常にグレースケールは用意

        if mode == "identify":
            # --- S2: 識別モード (重い) ---
            # 既存のトラッカーをすべてリセット
            self.active_trackers = []
            self.tracked_names = {}

            faces = self.detector(gray, 0)  # 顔検出 (dlib.rectangle)

            for face in faces:
                (x, y, w, h) = face_utils.rect_to_bb(face)
                face_rect = dlib.rectangle(
                    x, y, x + w, y + h)  # dlib.rectangle形式

                try:
                    # 顔領域を切り出して前処理
                    (x, y, w, h) = face_utils.rect_to_bb(face)
                    face_img = frame[y:y+h, x:x+w]
                    face_img = normalize_lighting(face_img)
                    face_img = align_face(face_img)
                    face_img = resize_face(face_img)

                    # Dlibベース分析（従来通り）
                    (avg_ear, mar, pitch, yaw, roll, landmarks, new_encoding) = self.analyzer.analyze_full(
                        cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY), dlib.rectangle(0, 0, face_img.shape[1], face_img.shape[0]), face_img.shape, face_img)

                except Exception as e:
                    print(f"[WARN] 顔分析(Full)中にエラー: {e}。スキップします。")
                    continue

                # --- 顔認証とUnknown登録 (元のロジックと同じ) ---
                name = "Unknown"
                if len(self.known_encodings) > 0:
                    distances = np.linalg.norm(
                        self.known_encodings - new_encoding, axis=1)
                    min_distance = np.min(distances)
                    best_match_index = np.argmin(distances)

                    if min_distance < self.RECOGNITION_THRESHOLD:
                        name = self.known_names[best_match_index]

                if name == "Unknown":
                    current_time = time.time()
                    if (current_time - self.last_save_time) > self.UNKNOWN_SAVE_COOLDOWN:
                        self.unknown_counter += 1
                        new_person_name = f"Unknown_{self.unknown_counter}"
                        save_dir = os.path.join(
                            self.KNOWN_FACES_DIR, new_person_name)
                        os.makedirs(save_dir, exist_ok=True)
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        filename = os.path.join(save_dir, f"{timestamp}.jpg")

                        padding = 20
                        (h_frame, w_frame, _) = frame.shape
                        x1, y1 = max(0, x - padding), max(0, y - padding)
                        x2, y2 = min(w_frame, x + w +
                                     padding), min(h_frame, y + h + padding)
                        face_image = frame[y1:y2, x1:x2]

                        if face_image.size > 0:
                            cv2.imwrite(filename, face_image)
                            print(f"[INFO] 新しい顔を保存: {filename}")
                            self.known_encodings.append(new_encoding)
                            self.known_names.append(new_person_name)
                            print(
                                f"[INFO] {new_person_name} をセッション中の記憶に追加しました。")
                            self.last_save_time = current_time
                            name = new_person_name  # 名前を更新
                        else:
                            self.unknown_counter -= 1
                # --- (ここまでUnknown登録処理) ---

                # ★ トラッカーを起動
                tracker = dlib.correlation_tracker()
                # (frame_bgr, dlib.rectangle) で追跡開始
                tracker.start_track(frame, face_rect)

                self.active_trackers.append(tracker)
                self.tracked_names[hash(tracker)] = name  # トラッカーと名前を紐付け

                result_data = {
                    "name": name,
                    "ear": avg_ear,
                    "mar": mar,
                    "pitch": pitch,
                    "yaw": yaw,
                    "roll": roll,
                    "landmarks": landmarks,  # 68点座標
                    "bbox": (x, y, w, h)
                }
                analysis_results.append(result_data)

                # 描画
                cv2.rectangle(processed_frame, (x, y),
                              (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(processed_frame, name, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        elif mode == "analyze_only":
            # --- S3: 分析・追跡モード (軽い) ---
            lost_trackers = []
            for tracker in self.active_trackers:
                # トラッカーで顔を追跡 (BGR画像でupdate)
                confidence = tracker.update(frame)

                # 追跡の信頼度が低い (例: 7未満) なら、ロストとみなす
                if confidence < 7.0:
                    lost_trackers.append(tracker)
                    continue

                pos = tracker.get_position()
                face_rect = dlib.rectangle(int(pos.left()), int(
                    pos.top()), int(pos.right()), int(pos.bottom()))
                (x, y, w, h) = (int(pos.left()), int(pos.top()),
                                int(pos.width()), int(pos.height()))

                # 名前は S2 で特定したものを引き継ぐ
                name = self.tracked_names.get(hash(tracker), "Tracking...")

                try:
                    #  中量版の分析を呼び出す (戻り値 6つ)
                    (avg_ear, mar, pitch, yaw, roll, landmarks) = self.analyzer.analyze_medium(
                        gray, face_rect, frame.shape)
                except Exception as e:
                    # 顔が画面外に出たりするとランドマーク検出が失敗する
                    print(f"[WARN] 顔分析(Light)中にエラー: {e}。スキップします。")
                    lost_trackers.append(tracker)  # エラーが出たら追跡失敗とみなす
                    continue

                result_data = {
                    "name": name,
                    "ear": avg_ear,
                    "mar": mar,
                    "pitch": pitch,
                    "yaw": yaw,
                    "roll": roll,
                    "landmarks": landmarks,
                    "bbox": (x, y, w, h)
                }
                analysis_results.append(result_data)

                # 描画 (S3は青い枠にするなど、色を変えても良い)
                cv2.rectangle(processed_frame, (x, y),
                              (x+w, y+h), (255, 0, 0), 2)
                cv2.putText(processed_frame, f"{name} (EAR: {avg_ear:.2f} MAR: {mar:.2f})", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

            # 追跡失敗したトラッカーを削除
            for tracker in lost_trackers:
                if tracker in self.active_trackers:
                    self.active_trackers.remove(tracker)
                    del self.tracked_names[hash(tracker)]

        # 処理済みフレームと結果リストを返す
        return (processed_frame, analysis_results)
# --- 前処理ユーティリティ ---


def enhance_lighting(bgr_img):
    """CLAHEによる明るさ/コントラスト改善。BGR入力、BGR出力。"""
    lab = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    return enhanced


def ensure_min_size(img, min_side=160):
    h, w = img.shape[:2]
    if min(h, w) < min_side:
        scale = min_side / min(h, w)
        img = cv2.resize(img, (int(w*scale), int(h*scale)))
    return img


def align_face(image):
    dets = detector(image, 1)
    if len(dets) == 0:
        return image
    shape = predictor(image, dets[0])
    shape = face_utils.shape_to_np(shape)
    left_eye = np.mean(shape[36:42], axis=0)
    right_eye = np.mean(shape[42:48], axis=0)
    dy, dx = right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]
    angle = np.degrees(np.arctan2(dy, dx))
    eyes_center = ((left_eye[0] + right_eye[0]) / 2,
                   (left_eye[1] + right_eye[1]) / 2)
    M = cv2.getRotationMatrix2D(eyes_center, angle, scale=1.0)
    return cv2.warpAffine(image, M, (image.shape[1], image.shape[0]), flags=cv2.INTER_CUBIC)

# ③ サイズ統一


def resize_face(image, size=(150, 150)):
    return cv2.resize(image, size)


def normalize_lighting(image):
    img_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    img_yuv[:, :, 0] = clahe.apply(img_yuv[:, :, 0])
    return cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)


def main_stream():
    STREAM_URL = 'http://192.168.11.10:5000/video_feed'
    try:
        identifier = PersonIdentifier()
    except Exception as e:
        print(f"初期化に失敗しました: {e}")
        exit()
    cap = cv2.VideoCapture(STREAM_URL)
    if not cap.isOpened():
        print(f"エラー: ストリーム '{STREAM_URL}' を開けませんでした。")
        exit()
    print("ストリームに接続しました。'q'キーで終了します。")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # ★ テスト時は identify モードのみ実行
        processed_frame, detected_names = identifier.process_frame(
            frame, mode="identify")

        if detected_names:
            print(f"検出: {detected_names}")
        cv2.imshow('Test Stream (PersonIdentifier)', processed_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main_stream()
