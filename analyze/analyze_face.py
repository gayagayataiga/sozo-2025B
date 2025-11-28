# import cv2
# import dlib
# import numpy as np
# import os
# from imutils import face_utils


# class FaceAnalyzer:
#     """
#     dlibのランドマークモデルを使用し、顔の分析（EAR、頭部傾き）を行うクラス。
#     """

#     def __init__(self, model_path="./dlib/shape_predictor_68_face_landmarks.dat"):
#         # --- 68点ランドマーク検出器の準備 ---
#         if not os.path.exists(model_path):
#             print(f"エラー: ランドマークモデル '{model_path}' が見つかりません。")
#             print("dlibからダウンロードして配置してください。")
#             raise FileNotFoundError(model_path)

#         self.predictor = dlib.shape_predictor(model_path)

#         # 目のランドマークのインデックスを取得
#         (self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
#         (self.rStart,
#          self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

#         print("dlibランドマークモデルを正常に読み込みました。")

#     def calculate_ear(self, eye_points):
#         """目の開き具合 (Eye Aspect Ratio) を計算する"""
#         v1 = np.linalg.norm(eye_points[1] - eye_points[5])
#         v2 = np.linalg.norm(eye_points[2] - eye_points[4])
#         h = np.linalg.norm(eye_points[0] - eye_points[3])
#         if h == 0:
#             return 0.0
#         ear = (v1 + v2) / (2.0 * h)
#         return ear

#     def calculate_head_tilt(self, shape_2d, image_shape):
#         """頭の傾き (Yaw) を計算する (solvePnPを使用)"""
#         image_points = np.array([
#             shape_2d[30],     # 鼻先
#             shape_2d[8],      # 顎
#             shape_2d[36],     # 左目尻
#             shape_2d[45],     # 右目尻
#             shape_2d[48],     # 左口角
#             shape_2d[54]      # 右口角
#         ], dtype="double")

#         model_points = np.array([
#             (0.0, 0.0, 0.0),             # 鼻先
#             (0.0, -330.0, -65.0),        # 顎
#             (-225.0, 170.0, -135.0),     # 左目尻
#             (225.0, 170.0, -135.0),      # 右目尻
#             (-150.0, -150.0, -125.0),    # 左口角
#             (150.0, -150.0, -125.0)     # 右口角
#         ])

#         focal_length = image_shape[1]
#         center = (image_shape[1]/2, image_shape[0]/2)
#         camera_matrix = np.array([
#             [focal_length, 0, center[0]],
#             [0, focal_length, center[1]],
#             [0, 0, 1]
#         ], dtype="double")

#         dist_coeffs = np.zeros((4, 1))

#         try:
#             (success, rotation_vector, translation_vector) = cv2.solvePnP(
#                 model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)
#         except cv2.error:
#             return 0.0

#         (rotation_matrix, _) = cv2.Rodrigues(rotation_vector)
#         sy = np.sqrt(rotation_matrix[0, 0] * rotation_matrix[0, 0] +
#                      rotation_matrix[1, 0] * rotation_matrix[1, 0])

#         if sy < 1e-6:
#             y = np.arctan2(-rotation_matrix[2, 0], sy)
#         else:
#             y = np.arctan2(-rotation_matrix[2, 0], sy)

#         yaw = np.degrees(y)
#         return yaw

#     def analyze(self, gray, face, frame_shape):
#         """
#         1つの顔 (face) を分析し、EARと頭部傾きを計算する。

#         :param gray: グレースケール画像
#         :param face: dlib.rectangle オブジェクト (検出された顔)
#         :param frame_shape: 元のカラーフレームの shape
#         :return: (avg_ear, head_tilt_deg) 分析結果のタプル
#         """
#         # --- ランドマーク検出 ---
#         shape = self.predictor(gray, face)
#         shape_np = face_utils.shape_to_np(shape)

#         # --- EAR (目の開き具合) の計算 ---
#         leftEAR = self.calculate_ear(shape_np[self.lStart:self.lEnd])
#         rightEAR = self.calculate_ear(shape_np[self.rStart:self.rEnd])
#         avg_ear = (leftEAR + rightEAR) / 2.0

#         # --- 頭の傾き (Yaw) の計算 ---
#         head_tilt_deg = self.calculate_head_tilt(shape_np, frame_shape)

#         return (avg_ear, head_tilt_deg)

# analyze/analyze_face.py (修正版)

import cv2
import dlib
import numpy as np
import os
from imutils import face_utils


class FaceAnalyzer:
    """
    dlibのモデルを使用し、顔の分析（EAR、頭部傾き、顔認証ベクトル）を行うクラス。
    """

    # --- 1. __init__ を修正 ---
    # detect_person.py が渡す引数名と一致させる
    def __init__(self, landmark_model_path, recognition_model_path):

        # --- ランドマーク検出器 (EAR, Tilt用) ---
        if not os.path.exists(landmark_model_path):
            print(f"エラー: ランドマークモデル '{landmark_model_path}' が見つかりません。")
            raise FileNotFoundError(landmark_model_path)

        self.predictor = dlib.shape_predictor(landmark_model_path)
        print("dlibランドマークモデルを正常に読み込みました。")

        # --- 顔認証モデル (Encoding用) を追加 ---
        if not os.path.exists(recognition_model_path):
            print(f"エラー: 認証モデル '{recognition_model_path}' が見つかりません。")
            raise FileNotFoundError(recognition_model_path)

        # dlibの顔認証モデルv1をロード
        self.facerec = dlib.face_recognition_model_v1(recognition_model_path)
        print("dlib顔認証モデルを正常に読み込みました。")

        # 目のランドマークのインデックスを取得
        (self.lStart, self.lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
        (self.rStart,
         self.rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
        (self.mStart, self.mEnd) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]

    def calculate_ear(self, eye_points):
        """目の開き具合 (Eye Aspect Ratio) を計算する"""
        # (この関数は変更なし)
        v1 = np.linalg.norm(eye_points[1] - eye_points[5])
        v2 = np.linalg.norm(eye_points[2] - eye_points[4])
        h = np.linalg.norm(eye_points[0] - eye_points[3])
        if h == 0:
            return 0.0
        ear = (v1 + v2) / (2.0 * h)
        return ear

    def calculate_mar(self, mouth_points):
        """  口の開き具合 (Mouth Aspect Ratio) を計算する (追加) """
        # 口の内側のインデックス (60-67)
        inner_mouth = mouth_points[12:20]  # 60番から67番

        # 垂直距離
        v1 = np.linalg.norm(inner_mouth[1] - inner_mouth[7])  # 61-67
        v2 = np.linalg.norm(inner_mouth[2] - inner_mouth[6])  # 62-66
        v3 = np.linalg.norm(inner_mouth[3] - inner_mouth[5])  # 63-65
        # 水平距離
        h = np.linalg.norm(inner_mouth[0] - inner_mouth[4])  # 60-64

        if h == 0:
            return 0.0
        mar = (v1 + v2 + v3) / (3.0 * h)
        return mar

    def get_full_head_pose(self, shape_2d, image_shape):
        """  頭の傾き (Pitch, Yaw, Roll) を計算する (Yaw以外も返すよう修正) """

        image_points = np.array([
            shape_2d[30],    # 鼻先
            shape_2d[8],     # 顎
            shape_2d[36],    # 左目尻
            shape_2d[45],    # 右目尻
            shape_2d[48],    # 左口角
            shape_2d[54]     # 右口角
        ], dtype="double")

        model_points = np.array([
            (0.0, 0.0, 0.0),             # 鼻先
            (0.0, -330.0, -65.0),        # 顎
            (-225.0, 170.0, -135.0),     # 左目尻
            (225.0, 170.0, -135.0),      # 右目尻
            (-150.0, -150.0, -125.0),    # 左口角
            (150.0, -150.0, -125.0)      # 右口角
        ])

        focal_length = image_shape[1]
        center = (image_shape[1]/2, image_shape[0]/2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype="double")

        dist_coeffs = np.zeros((4, 1))  # 歪み係数なし

        try:
            (success, rotation_vector, translation_vector) = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)
        except cv2.error:
            return (0.0, 0.0, 0.0)  # Pitch, Yaw, Roll

        (rotation_matrix, _) = cv2.Rodrigues(rotation_vector)
        sy = np.sqrt(rotation_matrix[0, 0] * rotation_matrix[0, 0] +
                     rotation_matrix[1, 0] * rotation_matrix[1, 0])

        singular = sy < 1e-6

        if not singular:
            x = np.arctan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
            y = np.arctan2(-rotation_matrix[2, 0], sy)
            z = np.arctan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
        else:
            x = np.arctan2(-rotation_matrix[1, 2], rotation_matrix[1, 1])
            y = np.arctan2(-rotation_matrix[2, 0], sy)
            z = 0

        # ラジアンから度に変換
        pitch = np.degrees(x)
        yaw = np.degrees(y)
        roll = np.degrees(z)

        return (pitch, yaw, roll)

    def analyze_landmarks_only(self, gray, face, frame_shape):
        """
         軽量版: (Yaw以外の計算を get_full_head_pose に移したため修正)
        """
        shape = self.predictor(gray, face)
        shape_np = face_utils.shape_to_np(shape)

        leftEAR = self.calculate_ear(shape_np[self.lStart:self.lEnd])
        rightEAR = self.calculate_ear(shape_np[self.rStart:self.rEnd])
        avg_ear = (leftEAR + rightEAR) / 2.0

        (_, yaw, _) = self.get_full_head_pose(shape_np, frame_shape)  # Yawのみ取得

        return (avg_ear, yaw)

    def analyze_medium(self, gray, face, frame_shape):
        """
         中量版: ランドマーク + 詳細な特徴量 (EAR, MAR, Pose, 68点座標) (新設)
        """
        # --- ランドマーク検出 ---
        shape = self.predictor(gray, face)
        shape_np = face_utils.shape_to_np(shape)

        # --- EAR (目の開き具合) ---
        avg_ear = (self.calculate_ear(shape_np[self.lStart:self.lEnd]) +
                   self.calculate_ear(shape_np[self.rStart:self.rEnd])) / 2.0

        # --- MAR (口の開き具合) ---
        mar = self.calculate_mar(shape_np[self.mStart:self.mEnd])

        # --- 頭部姿勢 (Pitch, Yaw, Roll) ---
        (pitch, yaw, roll) = self.get_full_head_pose(shape_np, frame_shape)

        # 68点すべての座標も返す
        landmarks_68 = shape_np

        return (avg_ear, mar, pitch, yaw, roll, landmarks_68)

    def analyze_full(self, gray, face, frame_shape, frame_bgr):
        """
         重量版: 中量版の特徴量 + 顔認証ベクトル (Encoding) (修正)
        """
        # (中量版と同じ処理を呼び出す)
        (avg_ear, mar, pitch, yaw, roll, landmarks_68) = self.analyze_medium(
            gray, face, frame_shape)

        # --- (重量処理) ---
        # ランドマーク検出は analyze_medium 内で行われるため、
        # ここでは shape を再度計算する必要がある (最適化の余地ありだが、簡潔さのため)
        shape = self.predictor(gray, face)
        face_encoding = self.facerec.compute_face_descriptor(frame_bgr, shape)
        face_encoding_np = np.array(face_encoding)

        # 中量版の返り値 + encoding を返す
        return (avg_ear, mar, pitch, yaw, roll, landmarks_68, face_encoding_np)
