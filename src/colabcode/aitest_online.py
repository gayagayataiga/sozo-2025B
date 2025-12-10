import cv2
import mediapipe as mp
import numpy as np

class PostureLearner:
    def __init__(self, learning_rate=0.01):
        self.mean = 90.0  # 初期平均（直立90度と仮定）
        self.variance = 10.0 # 初期分散
        self.std_dev = np.sqrt(self.variance)
        self.n_samples = 0
        self.calibration_frames = 100 # 最初の何フレームを初期学習に使うか
        self.alpha = learning_rate # 学習率（新しいデータをどれくらい重視するか）
        self.threshold_sigma = 2.5 # 標準偏差の何倍離れたら異常とするか

    def update(self, new_angle):
        self.n_samples += 1

        # --- 1. 初期キャリブレーション期間 ---
        if self.n_samples <= self.calibration_frames:
            # 逐次平均・分散の計算（Welfordのアルゴリズム的な簡易版）
            if self.n_samples == 1:
                self.mean = new_angle
            else:
                old_mean = self.mean
                self.mean = old_mean + (new_angle - old_mean) / self.n_samples
                self.variance = self.variance + ((new_angle - old_mean) * (new_angle - self.mean) - self.variance) / self.n_samples
            
            self.std_dev = np.sqrt(self.variance)
            return "CALIBRATING", 0.0

        # --- 2. 異常検知 & オンライン学習 ---
        
        # 異常度（Zスコア）の計算: 平均からどれだけ離れているか
        # abs(現在の値 - 平均) / 標準偏差
        diff = abs(new_angle - self.mean)
        if self.std_dev == 0: self.std_dev = 0.001 # ゼロ除算防止
        z_score = diff / self.std_dev

        state = "AWAKE"
        
        # 閾値を超えたら「異常（睡眠）」
        if z_score > self.threshold_sigma:
            state = "SLEEPING"
            # 重要: 寝ている時のデータは「正常」として学習させない！
            # ここでは学習更新をスキップします
        else:
            # 起きているなら、少しだけモデルを更新して今の姿勢に馴染ませる
            # 指数移動平均 (Exponential Moving Average) を使用
            self.mean = (1 - self.alpha) * self.mean + self.alpha * new_angle
            
            # 分散の更新
            new_variance = (new_angle - self.mean) ** 2
            self.variance = (1 - self.alpha) * self.variance + self.alpha * new_variance
            self.std_dev = np.sqrt(self.variance)

        return state, z_score

# --- メイン処理 ---

# MediaPipe設定
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# 学習器のインスタンス化
learner = PostureLearner(learning_rate=0.05) 

def calculate_angle(a, b):
    a = np.array(a); b = np.array(b)
    radians = np.arctan2(b[1] - a[1], b[0] - a[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0: angle = 360 - angle
    return angle

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = pose.process(image)
    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    
    current_status = "UNKNOWN"
    current_z = 0.0
    neck_angle = 0

    try:
        landmarks = results.pose_landmarks.landmark
        
        # 座標取得 (11:左肩, 12:右肩, 7:左耳, 8:右耳)
        s_l = [landmarks[11].x, landmarks[11].y]
        s_r = [landmarks[12].x, landmarks[12].y]
        e_l = [landmarks[7].x, landmarks[7].y]
        e_r = [landmarks[8].x, landmarks[8].y]
        
        # 中点
        s_mid = [(s_l[0]+s_r[0])/2, (s_l[1]+s_r[1])/2]
        e_mid = [(e_l[0]+e_r[0])/2, (e_l[1]+e_r[1])/2]
        
        # 角度計算
        neck_angle = calculate_angle(s_mid, e_mid)
        
        # === AI学習・判定 ===
        current_status, current_z = learner.update(neck_angle)
        # ==================

        # 描画用座標
        h, w, _ = image.shape
        p1 = (int(s_mid[0]*w), int(s_mid[1]*h))
        p2 = (int(e_mid[0]*w), int(e_mid[1]*h))
        
        # 色設定
        color = (0, 255, 0)
        if current_status == "CALIBRATING": color = (0, 255, 255) # 黄色
        elif current_status == "SLEEPING": color = (0, 0, 255)   # 赤

        cv2.line(image, p1, p2, color, 4)
        cv2.circle(image, p1, 5, (255,255,255), -1)
        
        # 情報表示
        cv2.putText(image, f'STATUS: {current_status}', (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.putText(image, f'Angle: {int(neck_angle)} deg', (20, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1)
        
        if current_status != "CALIBRATING":
            # 学習した平均と閾値を表示
            mean_str = f"Mean: {learner.mean:.1f}"
            limit_str = f"Limit: +/- {(learner.std_dev * learner.threshold_sigma):.1f}"
            z_str = f"Anomaly(Z): {current_z:.1f}"
            
            cv2.putText(image, mean_str, (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 1)
            cv2.putText(image, limit_str, (20, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 1)
            cv2.putText(image, z_str, (20, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100,255,100), 1)

    except Exception as e:
        pass
    
    cv2.imshow('Online Learning Sleep Detection', image)
    if cv2.waitKey(10) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()