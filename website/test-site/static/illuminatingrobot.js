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
		// アームを定位置にリセット
		currentArmAngle = ANGLE_HOME;

		// 手首を定位置にリセット
		currentWristAngle = WRIST_ANGLE_HOME;
		//初期画像に更新
		updateArmImage(currentArmAngle);


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
			// 全ボタンから 'active' クラスを削除
			document.querySelectorAll('.color-btn').forEach(btn => {
				btn.classList.remove('active');
			});
			// クリックされたボタンに 'active' クラスを追加
			event.target.classList.add('active');

			// サーバーへ信号送信 (REST APIを使用)
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
let picker = null;

if (pickerContainer) {
	// 2. カラーピッカーを初期化
	picker = new Picker({
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


const resetColorButton = document.getElementById('reset-color-button');
if (resetColorButton) {
	resetColorButton.addEventListener('click', () => {
		if (isPowerOn) {
			const resetColor = 'rgb(255, 255, 255)'; // リセットする色（白）

			// 1. サーバーにリセット色（白）を送信
			sendCommand('set_color_wheel', resetColor);
			console.log('色をリセットしました:', resetColor);

			// 2. カラーピッカーの表示も更新 (pickerインスタンスが存在する場合)
			if (picker) {
				// 第2引数を指定しないかfalseにすると、onChangeイベントを発火させずにUIのみ更新します
				picker.setColor(resetColor);
			}

		} else {
			alert('電源がオフです。色設定はできません。');
		}
	});
}

// ロボットの操作を行うための関数群やイベントリスナーの定義はここ以降
// --- HTML要素の取得 に追記 ---
const openRobotMoveButton = document.getElementById('open-robot-move-button');
const robotMoveModal = document.getElementById('robot-move-modal');

// モーダル内のロボット操作ボタン
const armMoveHomeButton = document.getElementById('arm-move-home');
const armMoveUpButton = document.getElementById('arm-move-up');
const armMoveDownButton = document.getElementById('arm-move-down');

const wristmotorUpButton = document.getElementById('wrist-motor-up');
const wristmotorHomeButton = document.getElementById('wrist-motor-home');
const wristmotorDownButton = document.getElementById('wrist-motor-down');

// 画像を変えるコード
const robotStatusImage = document.getElementById('robot-status-image');

// 肘の角度のステップと範囲を定義 (例: 10度ずつ、70度～110度)
const ANGLE_HOME = 90;  // 「定位置」の角度
const ANGLE_STEP = 10;  // 1回に動く角度
const ANGLE_MIN = 70;   // 「下へ」の可動域 (最小)
const ANGLE_MAX = 100;  // 「上へ」の可動域 (最大)

// 手首の角度のステップと範囲を定義
const WRIST_ANGLE_HOME = 45;  // 手首の「定位置」
const WRIST_ANGLE_STEP = 5;  // 手首の1回の動作角度
const WRIST_ANGLE_MIN = 30;   // 手首の最小角度
const WRIST_ANGLE_MAX = 60;  // 手首の最大角度

// 肘の現在角度を持っておく変数
let currentArmAngle = ANGLE_HOME;
// 手首の現在角度を持っておく変数
let currentWristAngle = WRIST_ANGLE_HOME;

// 画像を保持しておく
const ARM_IMAGE_MAP = {
	70: '../static/photo/arm.jpg',  // 下限
	80: '../static/photo/arm - コピー.jpg',
	90: '../static/photo/arm - コピー (2).jpg',
	100: '../static/photo/arm - コピー (3).jpg',
};


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
		switch (action) {
			case 'home':
				currentArmAngle = ANGLE_HOME;
				break;
			case 'up': // 「アームを上へ」
				if (currentArmAngle + ANGLE_STEP > ANGLE_MAX) {
					alert('これ以上アームを上げることはできません。');
				}
				// 最大角度(ANGLE_MAX)を超えないようにする
				currentArmAngle = Math.min(currentArmAngle + ANGLE_STEP, ANGLE_MAX);
				break;
			case 'down': // 「アームを下へ」
				if (currentArmAngle - ANGLE_STEP < ANGLE_MIN) {
					alert('これ以上アームを下げることはできません。');
				}
				// 最小角度(ANGLE_MIN)より下がらないようにする
				currentArmAngle = Math.max(currentArmAngle - ANGLE_STEP, ANGLE_MIN);
				break;
		}
		// 現在の肘の角度をサーバーに送信
		sendCommand('set_angle_elbow', currentArmAngle);

		// 3. 新しい角度に基づいて画像を一括更新
		updateArmImage(currentArmAngle);
	} else {
		alert('電源がオフです。電源をオンにしてください。');
	}
}

function handleWristMotor(action) {
	if (isPowerOn) {

		// 1. action に応じて「手首の角度」の変数を更新
		switch (action) {
			case 'home':
				currentWristAngle = WRIST_ANGLE_HOME;
				break;
			case 'up': // 「上へ」
				if (currentWristAngle + WRIST_ANGLE_STEP > WRIST_ANGLE_MAX) {
					alert('これ以上手首を上げることはできません。');
				}
				// 最大角度(WRIST_ANGLE_MAX)を超えないようにする
				currentWristAngle = Math.min(currentWristAngle + WRIST_ANGLE_STEP, WRIST_ANGLE_MAX);
				break;
			case 'down': // 「下へ」
				if (currentWristAngle - WRIST_ANGLE_STEP < WRIST_ANGLE_MIN) {
					alert('これ以上手首を下げることはできません。');
				}
				// 最小角度(WRIST_ANGLE_MIN)より下がらないようにする
				currentWristAngle = Math.max(currentWristAngle - WRIST_ANGLE_STEP, WRIST_ANGLE_MIN);
				break;
		}

		// 2. 現在の手首の角度をサーバーに送信
		console.log(`手首の角度: ${currentWristAngle}度`);
		sendCommand('set_angle_wrist', currentWristAngle);

	} else {
		alert('電源がオフです。電源をオンにしてください。');
	}
}
// 各ボタンにイベントを割り当て
if (armMoveHomeButton) {
	armMoveHomeButton.addEventListener('click', () => handleArmMove('home'));
}
if (armMoveUpButton) {
	armMoveUpButton.addEventListener('click', () => handleArmMove('up'));
}
if (armMoveDownButton) {
	armMoveDownButton.addEventListener('click', () => handleArmMove('down'));
}
if (wristmotorUpButton) {
	wristmotorUpButton.addEventListener('click', () => handleWristMotor('up'));
}
if (wristmotorHomeButton) {
	wristmotorHomeButton.addEventListener('click', () => handleWristMotor('home'));
}
if (wristmotorDownButton) {
	wristmotorDownButton.addEventListener('click', () => handleWristMotor('down'));
}





/**
 * 現在の角度に基づいて、ロボットの画像を指定の角度のものに更新する
 * @param {number} angle - 表示したい角度
 */
function updateArmImage(angle) {
	console.log(`現在の角度: ${angle}度`);

	if (robotStatusImage && ARM_IMAGE_MAP[angle]) {
		// 対応表 (ARM_IMAGE_MAP) から正しい画像パスを取得して設定
		robotStatusImage.src = ARM_IMAGE_MAP[angle];
	} else {
		// もし 75度 など、対応表にない角度が指定された場合
		console.warn(`角度 ${angle} に対応する画像が ARM_IMAGE_MAP にありません。`);
		// (オプション: 一番近い角度の画像を探すロジックも組めます)
	}
}