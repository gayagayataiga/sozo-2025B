from collections import deque
import numpy as np

class DrowsinessDetector:
    """複数の指標を統合して居眠りを検知するクラス"""
    
    def __init__(self):
        # 各指標の重み（合計1.0にする必要はない）
        self.weights = {
            'eye': 0.4,      # 目の状態が最も重要
            'posture': 0.35, # 姿勢も重要
            'mouth': 0.25    # 口は補助的
        }
        
        # 閾値
        self.ear_threshold = 0.21      # これ以下で「目が閉じている」
        self.mar_threshold = 0.5       # これ以上で「口が開いている」（あくび）
        self.posture_z_threshold = 2.0 # Z-scoreがこれ以上で「姿勢崩れ」
        
        # 時間的な平滑化用（瞬きと居眠りを区別）
        self.eye_closed_frames = 0
        self.eye_closed_threshold_frames = 15  # 約0.5秒（30fps想定）
        
        # 総合スコアの閾値
        self.drowsiness_threshold = 0.6  # これ以上で「居眠り」と判定
        
        # 状態の履歴（急な変化を防ぐ）
        self.score_history = deque(maxlen=10)
    
    def calculate_eye_score(self, ear: float) -> float:
        """目の状態スコア（0=開いている, 1=閉じている）"""
        if ear < self.ear_threshold:
            self.eye_closed_frames += 1
        else:
            self.eye_closed_frames = max(0, self.eye_closed_frames - 2)
        
        # 一定フレーム以上閉じていたら居眠りの可能性
        if self.eye_closed_frames > self.eye_closed_threshold_frames:
            return 1.0
        elif self.eye_closed_frames > 0:
            return self.eye_closed_frames / self.eye_closed_threshold_frames
        return 0.0
    
    def calculate_posture_score(self, z_score: float) -> float:
        """姿勢スコア（0=正常, 1=崩れている）"""
        if z_score <= 0:
            return 0.0
        # Z-scoreを0-1にマッピング
        return min(1.0, z_score / (self.posture_z_threshold * 1.5))
    
    def calculate_mouth_score(self, mar: float) -> float:
        """口の状態スコア（あくび検出）"""
        if mar > self.mar_threshold:
            # あくびの可能性
            return min(1.0, (mar - self.mar_threshold) / 0.3)
        return 0.0
    
    def update(self, ear: float, mar: float, posture_z: float) -> tuple:
        """
        総合的な居眠りスコアを計算
        
        Returns:
            (status: str, score: float, details: dict)
        """
        # 各スコアを計算
        eye_score = self.calculate_eye_score(ear)
        posture_score = self.calculate_posture_score(posture_z)
        mouth_score = self.calculate_mouth_score(mar)
        
        # 重み付け合計
        weighted_score = (
            eye_score * self.weights['eye'] +
            posture_score * self.weights['posture'] +
            mouth_score * self.weights['mouth']
        )
        
        # 正規化（0-1の範囲に）
        max_possible = sum(self.weights.values())
        normalized_score = weighted_score / max_possible
        
        # 履歴に追加して平滑化
        self.score_history.append(normalized_score)
        smoothed_score = np.mean(self.score_history)
        
        # 状態判定
        if smoothed_score >= self.drowsiness_threshold:
            status = "SLEEPING"
        elif smoothed_score >= self.drowsiness_threshold * 0.6:
            status = "DROWSY"  # 眠気あり（警告段階）
        else:
            status = "AWAKE"
        
        details = {
            'eye_score': eye_score,
            'posture_score': posture_score,
            'mouth_score': mouth_score,
            'raw_score': normalized_score,
            'smoothed_score': smoothed_score
        }
        
        return status, smoothed_score, details