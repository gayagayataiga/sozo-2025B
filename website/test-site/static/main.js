/**
 * main.js
 * * メインUI（電源、タイマー、ステータス表示）の
 * ロジックを担当するファイル。
 * * 各モジュールを `import` して、
 * 電源ON/OFF時に各状態をリセットする起点となります。
 */

// ------------------------------------------------------------------
// 1. 必要なモジュールをインポート
// ------------------------------------------------------------------

// api.js から サーバー通信 と WebSocket をインポート
import { sendCommand, socket } from './api.js';

// state.js から 全ての状態 と セッター をインポート
import {
	isPowerOn, setPowerOn,
	startTime, setStartTime,
	timerInterval, setTimerInterval,
	setArmAngle, ANGLE_HOME,
	setWristAngle, WRIST_ANGLE_HOME
} from './state.js';

// robotModal.js から 肘の画像更新関数 をインポート
import { updateArmImage } from './robotModal.js';

// animation.js から (グローバルに
// `startAnimation` `stopAnimation` が定義されている想定)
// もし animation.js もモジュールなら
// import { startAnimation, stopAnimation } from './animation.js';

// ------------------------------------------------------------------
// 2. メインUIのDOM要素を取得
// ------------------------------------------------------------------

const powerToggle = document.getElementById('power-toggle');
const statusText = document.getElementById('status-text');
const visualArea = document.getElementById('active-visual');
const timerDisplay = document.getElementById('timer-display');
const concentrationDisplay = document.getElementById('concentration');

// ------------------------------------------------------------------
// 3. WebSocketイベントの処理 (api.js から移動)
// ------------------------------------------------------------------

// (※ api.js は接続を定義するだけ、
//     main.js が「接続後に何をするか」を定義する)
socket.on('connect', () => {
	if (statusText) {
		statusText.textContent = 'ロボットの状態：接続済み (PCサーバー)';
	}
	console.log("✅ WebSocket 接続成功 (main.js)");
});

socket.on('disconnect', () => {
	if (statusText) {
		statusText.textContent = 'ロボットの状態：切断中';
	}
	console.log("❌ WebSocket 切断 (main.js)");
});

// 集中度ステータスの更新
socket.on('status_update', (data) => {
	console.log('受信データ (main.js):', data);

	if (concentrationDisplay) {
		const level = data.concentration_level || 'N/A';
		concentrationDisplay.textContent = level;
	}
});

// ------------------------------------------------------------------
// 4. タイマー関連の関数
// ------------------------------------------------------------------

function formatTime(seconds) {
	const h = String(Math.floor(seconds / 3600)).padStart(2, '0');
	const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
	const s = String(seconds % 60).padStart(2, '0');
	return `${h}:${m}:${s}`;
}

function updateTimer() {
	// state.js から isPowerOn と startTime を参照
	if (!isPowerOn) return;
	const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
	timerDisplay.textContent = `経過時間: ${formatTime(elapsedSeconds)}`;
}

function startTimer() {
	// state.js の startTime と timerInterval を更新
	setStartTime(Date.now());
	updateTimer();
	const interval = setInterval(updateTimer, 1000);
	setTimerInterval(interval);
}

function stopTimer() {
	// state.js の timerInterval を参照・更新
	clearInterval(timerInterval);
	setTimerInterval(null);
	timerDisplay.textContent = '経過時間: 00:00:00';
}

// ------------------------------------------------------------------
// 5. 電源ボタンのイベントリスナー
// ------------------------------------------------------------------

powerToggle.addEventListener('click', () => {
	// state.js の isPowerOn を参照
	const currentStatus = powerToggle.getAttribute('data-status');
	const isOff = (currentStatus === 'off');

	if (isOff) {
		// --- 電源をオンにする ---
		powerToggle.setAttribute('data-status', 'on');
		powerToggle.textContent = '電源をオフにする';
		statusText.textContent = 'ロボットの状態：オンライン (稼働中)';
		visualArea.classList.remove('light-off');
		visualArea.classList.add('light-on');

		// 1. 状態(state.js)をリセット
		setArmAngle(ANGLE_HOME);
		setWristAngle(WRIST_ANGLE_HOME);
		setPowerOn(true);

		// 2. UIをリセット (robotModal.js の関数を呼ぶ)
		updateArmImage(ANGLE_HOME);

		// 3. サーバーに送信 (api.js の関数を呼ぶ)
		sendCommand('power_toggle', 'on');

		// 4. タイマーとアニメーションを開始
		startTimer();
		startAnimation(); // animation.js の関数

	} else {
		// --- 電源をオフにする ---
		powerToggle.setAttribute('data-status', 'off');
		powerToggle.textContent = '電源をオンにする';
		statusText.textContent = 'ロボットの状態：オフライン';
		visualArea.classList.remove('light-on');
		visualArea.classList.add('light-off');

		// 1. 状態(state.js)を更新
		setPowerOn(false);

		// 2. サーバーに送信 (api.js の関数を呼ぶ)
		sendCommand('power_toggle', 'off');

		// 3. タイマーとアニメーションを停止
		stopTimer();
		stopAnimation(); // animation.js の関数
	}
});