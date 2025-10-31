// サーバー接続設定 ------------------------------------------------------------------
// const LOCAL_PC_IP = '192.168.11.10';
const controlURL = `http://${LOCAL_PC_IP}:5001/api/control`;

// ------------------------------------------------------------------
// サーバーへのコマンド送信 (REST API) 関数を定義
// ------------------------------------------------------------------
function sendCommand(action, value) {
	const data = { action: action, value: value };

	fetch(controlURL, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data)
	})
		.then(response => {
			// サーバー側でレスポンスを返す必要があります
			if (!response.ok) throw new Error(`送信失敗: ${response.status}`);
			console.log(`✅ コマンド送信成功: ${action}, ${value}`);
			return response.json();
		})
		.catch(error => console.error('❌ 通信エラー発生:', error));
}
// ------------------------------------------------------------------


// HTML要素の取得
const powerToggle = document.getElementById('power-toggle');
const statusText = document.getElementById('status-text');
const visualArea = document.getElementById('active-visual');
const timerDisplay = document.getElementById('timer-display');
const concentrationDisplay = document.getElementById('concentration'); // 集中度表示要素を追加

// 2. WebSocketによるデータ受信の初期化 -----------------------------------------------
const socket = io(`http://${LOCAL_PC_IP}:5001`);

socket.on('connect', () => {
	statusText.textContent = 'ロボットの状態：接続済み (PCサーバー)';
});

socket.on('disconnect', () => {
	statusText.textContent = 'ロボットの状態：切断中';
});

// 'status_update'イベントでデータを受信 (集中度、AI推奨色など)
socket.on('status_update', (data) => {
	console.log('受信データ:', data);

	const level = data.concentration_level || 'N/A';
	concentrationDisplay.textContent = level;

	// (集中度に応じた映像切り替えロジックなどをここに追加)
	// animation.jsにそのコードを書いた
});
// ------------------------------------------------------------------


// タイマー関連の変数と関数 (変更なし) -----------------------------------------------
let isPowerOn = false;
let startTime = 0;
let timerInterval = null;

function formatTime(seconds) {
	const h = String(Math.floor(seconds / 3600)).padStart(2, '0');
	const m = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
	const s = String(seconds % 60).padStart(2, '0');
	return `${h}:${m}:${s}`;
}

function updateTimer() {
	if (!isPowerOn) return;
	const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
	timerDisplay.textContent = `経過時間: ${formatTime(elapsedSeconds)}`;
}

function startTimer() {
	startTime = Date.now();
	updateTimer();
	timerInterval = setInterval(updateTimer, 1000);
}

function stopTimer() {
	clearInterval(timerInterval);
	timerInterval = null;
	timerDisplay.textContent = '経過時間: 00:00:00';
}
// ------------------------------------------------------------------




// 3. UI操作イベントの割り当て ------------------------------------------------------
// 電源トグルボタンのクリックイベント
powerToggle.addEventListener('click', () => {
	const currentStatus = powerToggle.getAttribute('data-status');
	const isOff = (currentStatus === 'off');

	if (isOff) {
		// 電源をオンにする
		powerToggle.setAttribute('data-status', 'on');
		powerToggle.textContent = '電源をオフにする';
		statusText.textContent = 'ロボットの状態：オンライン (稼働中)';
		visualArea.classList.remove('light-off');
		visualArea.classList.add('light-on');

		// サーバーへON信号送信 (REST APIを使用)
		sendCommand('power_toggle', 'on');

		// タイマー開始
		isPowerOn = true;
		startTimer();
		startAnimation();

	} else {
		// 電源をオフにする
		powerToggle.setAttribute('data-status', 'off');
		powerToggle.textContent = '電源をオンにする';
		statusText.textContent = 'ロボットの状態：オフライン';
		visualArea.classList.remove('light-on');
		visualArea.classList.add('light-off');

		// サーバーへOFF信号送信 (REST APIを使用)
		sendCommand('power_toggle', 'off');

		// タイマー停止
		isPowerOn = false;
		stopTimer();
		stopAnimation();
	}
});

// アーム動作ボタン
document.getElementById('arm-move').addEventListener('click', () => {
	if (isPowerOn) {
		// サーバーへ信号送信 (REST APIを使用)
		sendCommand('move_arm', 'home');
	} else {
		alert('電源がオフです。電源をオンにしてください。');
	}
});

// 強弱（明るさ）スライダー
const brightnessSlider = document.getElementById('brightness-slider');
const brightnessValue = document.getElementById('brightness-value');

const modalBrightnessSlider = document.getElementById('brightness-slider-modal');
const modalBrightnessValue = document.getElementById('brightness-value-modal');
const modalColorControls = document.getElementById('color-controls-modal'); // 色コントロールの親要素


if (modalBrightnessSlider) {
	modalBrightnessSlider.addEventListener('input', (event) => {
		const value = parseInt(event.target.value);
		// メイン画面の値も更新し、モーダル内の値も更新する
		if (brightnessValue) brightnessValue.textContent = value;
		if (modalBrightnessValue) modalBrightnessValue.textContent = value;

		// サーバーに送信するロジック
		if (isPowerOn) {
			sendCommand('set_brightness', value);
		}
	});
}


// 色変更ボタン
document.querySelectorAll('.color-btn').forEach(button => {
	button.addEventListener('click', (event) => {
		const color = event.target.getAttribute('data-color');

		if (isPowerOn) {
			// ★★★ ハイライト処理の追加 ★★★
			// 1. 全ボタンから 'active' クラスを削除
			document.querySelectorAll('.color-btn').forEach(btn => {
				btn.classList.remove('active');
			});
			// 2. クリックされたボタンに 'active' クラスを追加
			event.target.classList.add('active');

			// ★ サーバーへ信号送信 (REST APIを使用)
			sendCommand('set_color', color);
		} else {
			alert('電源がオフです。色設定はできません。');
		}
	});
});
// ------------------------------------------------------------------


// --- HTML要素の取得 に追記 ---
const settingModal = document.getElementById('setting-modal');
const closeButton = document.querySelector('.close-button');
const openSettingsButton = document.getElementById('open-settings-button');

// --- イベントリスナーの追加 ---

// 1. 「照明設定を開く」ボタンが押されたらモーダルを表示
if (openSettingsButton) {
	openSettingsButton.addEventListener('click', () => {
		settingModal.classList.remove('hidden');
		robotMoveModal.classList.add('hidden');
	});
}

// 2. 閉じるボタン（×ボタン）が押されたらモーダルを非表示
if (closeButton) {
	closeButton.addEventListener('click', () => {
		settingModal.classList.add('hidden');
	});
}

// 3. モーダルの外側（半透明部分）がクリックされたら非表示
if (settingModal) {
	settingModal.addEventListener('click', (e) => {
		// クリックされたのがモーダル自身（.modal-contentではない）であることを確認
		if (e.target === settingModal) {
			settingModal.classList.add('hidden');
		}
	});
}

// 1. HTML要素を取得 (モーダル内にあることを確認)
const pickerContainer = document.getElementById('picker-container');

if (pickerContainer) {
	// 2. カラーピッカーを初期化
	const picker = new Picker({
		parent: pickerContainer,     // どのHTML要素内にピッカーを配置するか
		popup: false,                // ポップアップではなく、常時表示（インライン）
		color: 'rgb(255, 0, 0)',     // 初期色
		layout: 'hsv',               // 色相(H)と彩度(S)のみ表示
		editor: false,               // RGB入力欄を表示
		alpha: false,                // 透明度スライダーを表示
		doneButton: false,			// 「完了」ボタンを非表示

		// 3. 色の変更が完了したときにサーバーへ送信 (onDoneは onchangeと別に残す)
		onChange: color => {
			const rgbString = color.rgbString;
			console.log("選択された色:", rgbString);

			if (isPowerOn) {
				sendCommand('set_color_wheel', rgbString);
			}
		}
	});
}

// ロボットの操作を行うための関数群やイベントリスナーの定義はここ以降
// --- HTML要素の取得 に追記 ---
const openRobotMoveButton = document.getElementById('open-robot-move-button');
const robotMoveModal = document.getElementById('robot-move-modal');

// モーダル内のロボット操作ボタン
const armMoveHomeButton = document.getElementById('arm-move-home');
const armMoveLeftButton = document.getElementById('arm-move-left');
const armMoveRightButton = document.getElementById('arm-move-right');

// 1. 「ロボット動作を開く」ボタンが押されたらモーダルを表示
if (openRobotMoveButton) {
	openRobotMoveButton.addEventListener('click', () => {
		robotMoveModal.classList.remove('hidden');
		settingModal.classList.add('hidden'); // ※ 既存の照明モーダルを閉じる
	});
}

// 2. ロボットモーダルの外側（半透明部分）がクリックされたら非表示
if (robotMoveModal) {
	robotMoveModal.addEventListener('click', (e) => {
		// クリックされたのがモーダル自身（.modal-contentではない）であることを確認
		if (e.target === robotMoveModal) {
			robotMoveModal.classList.add('hidden');
		}
	});
}

// 3. モーダル内のロボット操作ボタンのイベント
// 共通の処理を関数化
function handleArmMove(action) {
	if (isPowerOn) {
		// サーバーへ信号送信 (REST APIを使用)
		sendCommand('move_arm', action);
	} else {
		alert('電源がオフです。電源をオンにしてください。');
	}
}

// 各ボタンにイベントを割り当て
if (armMoveHomeButton) {
	armMoveHomeButton.addEventListener('click', () => handleArmMove('home'));
}
if (armMoveLeftButton) {
	armMoveLeftButton.addEventListener('click', () => handleArmMove('left'));
}
if (armMoveRightButton) {
	armMoveRightButton.addEventListener('click', () => handleArmMove('right'));
}