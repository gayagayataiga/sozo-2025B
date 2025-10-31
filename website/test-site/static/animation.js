/* --- 設定 --- */

// 1. 画像ファイルのリスト (photoフォルダにあると仮定)
// ファイル名は順番通りでなくても構いません。
const imageFrames = [
	'../static/photo/9cd1063f119e369bbb20ef6238cac06f.jpeg',
	'../static/photo/77f0f9365a72eb7044602d9221f44ebb.jpeg',
];

const intervalTime = 1000; // 1秒ごとに画像を切り替え

// --- HTML要素の取得 ---
const stopMotionImage = document.getElementById('stop-motion-image');

// --- アニメーション用変数 ---
let currentFrameIndex = 0;
let animationInterval = null; // setIntervalのIDを保存する変数
// --- アニメーションを開始する関数 ---
function startAnimation() {
	if (animationInterval) return;

	animationInterval = setInterval(() => {
		currentFrameIndex = (currentFrameIndex + 1) % imageFrames.length;
		if (stopMotionImage) {
			stopMotionImage.src = imageFrames[currentFrameIndex];
		}
	}, intervalTime);
}

// --- アニメーションを停止する関数 ---
function stopAnimation() {
	clearInterval(animationInterval);
	animationInterval = null;
	currentFrameIndex = 0;
	if (stopMotionImage) {
		stopMotionImage.src = imageFrames[0];
	}
}
