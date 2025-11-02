/**
 * robotModal.js
 * * ロボット操作モーダルのすべてのUI操作を担当するファイル。
 * * state.js から現在の角度や電源状態を、
 * * api.js から sendCommand 関数をインポートして使用します。
 */

// ------------------------------------------------------------------
// 1. 必要なモジュールをインポート
// ------------------------------------------------------------------

// state.js から状態と定数、セッター関数をインポート
import {
	isPowerOn,
	currentArmAngle,
	currentWristAngle,
	setArmAngle,
	setWristAngle,
	ANGLE_HOME,
	ANGLE_STEP,
	ANGLE_MIN,
	ANGLE_MAX,
	WRIST_ANGLE_HOME,
	WRIST_ANGLE_STEP,
	WRIST_ANGLE_MIN,
	WRIST_ANGLE_MAX
} from './state.js';

// api.js からサーバー通信関数をインポート
import { sendCommand } from './api.js';

// ------------------------------------------------------------------
// 2. このファイル固有の定数とDOM取得
// ------------------------------------------------------------------

// (注意) lightingModal.js でも settingModal をインポートする必要があります
const settingModal = document.getElementById('setting-modal');

// --- HTML要素の取得 ---
const openRobotMoveButton = document.getElementById('open-robot-move-button');
const robotMoveModal = document.getElementById('robot-move-modal');

// モーダル内のロボット操作ボタン
const armMoveHomeButton = document.getElementById('arm-move-home');
const armMoveUpButton = document.getElementById('arm-move-up');
const armMoveDownButton = document.getElementById('arm-move-down');

const wristmotorUpButton = document.getElementById('wrist-motor-up');
const wristmotorHomeButton = document.getElementById('wrist-motor-home');
const wristmotorDownButton = document.getElementById('wrist-motor-down');

// 画像
const robotStatusImage = document.getElementById('robot-status-image');

// --- 画像の対応表 ---
// (※このファイルが管理する肘の角度と画像のマップ)
const ARM_IMAGE_MAP = {
	70: '../static/photo/arm.jpg',
	80: '../static/photo/arm - コピー.jpg',
	90: '../static/photo/arm - コピー (2).jpg',
	100: '../static/photo/arm - コピー (3).jpg',
};

// ------------------------------------------------------------------
// 3. モーダルの「開閉」イベント
// ------------------------------------------------------------------

// 「ロボット動作を開く」ボタンが押されたらモーダルを表示
if (openRobotMoveButton) {
	openRobotMoveButton.addEventListener('click', () => {
		robotMoveModal.classList.remove('hidden');
		if (settingModal) {
			settingModal.classList.add('hidden'); // ※ 照明モーダルを閉じる
		}
	});
}

// ロボットモーダルの外側（半透明部分）がクリックされたら非表示
if (robotMoveModal) {
	robotMoveModal.addEventListener('click', (e) => {
		// クリックされたのがモーダル自身（.modal-contentではない）であることを確認
		if (e.target === robotMoveModal) {
			robotMoveModal.classList.add('hidden');
		}
	});
}

// ------------------------------------------------------------------
// 4. モーダル内のボタン操作
// ------------------------------------------------------------------

/**
 * 肘（アーム）の操作
 * @param {string} action 'home', 'up', 'down'
 */
function handleArmMove(action) {
	// state.js から isPowerOn を参照
	if (!isPowerOn) {
		alert('電源がオフです。電源をオンにしてください。');
		return;
	}

	// state.js から currentArmAngle を参照
	let newAngle = currentArmAngle;

	switch (action) {
		case 'home':
			newAngle = ANGLE_HOME;
			break;
		case 'up': // 「アームを上へ」
			if (currentArmAngle + ANGLE_STEP > ANGLE_MAX) {
				alert('これ以上アームを上げることはできません。');
			}
			newAngle = Math.min(currentArmAngle + ANGLE_STEP, ANGLE_MAX);
			break;
		case 'down': // 「アームを下へ」
			if (currentArmAngle - ANGLE_STEP < ANGLE_MIN) {
				alert('これ以上アームを下げることはできません。');
			}
			newAngle = Math.max(currentArmAngle - ANGLE_STEP, ANGLE_MIN);
			break;
	}

	// 1. state.js の状態を更新
	setArmAngle(newAngle);

	// 2. api.js の関数を使い、サーバーに送信
	sendCommand('set_angle_elbow', newAngle);

	// 3. UI（画像）を更新
	updateArmImage(newAngle);
}

/**
 * 手首（リスト）の操作
 * @param {string} action 'home', 'up', 'down'
 */
function handleWristMotor(action) {
	if (!isPowerOn) {
		alert('電源がオフです。電源をオンにしてください。');
		return;
	}

	let newAngle = currentWristAngle;

	switch (action) {
		case 'home':
			newAngle = WRIST_ANGLE_HOME;
			break;
		case 'up': // 「上へ」
			if (currentWristAngle + WRIST_ANGLE_STEP > WRIST_ANGLE_MAX) {
				alert('これ以上手首を上げることはできません。');
			}
			newAngle = Math.min(currentWristAngle + WRIST_ANGLE_STEP, WRIST_ANGLE_MAX);
			break;
		case 'down': // 「下へ」
			if (currentWristAngle - WRIST_ANGLE_STEP < WRIST_ANGLE_MIN) {
				alert('これ以上手首を下げることはできません。');
			}
			newAngle = Math.max(currentWristAngle - WRIST_ANGLE_STEP, WRIST_ANGLE_MIN);
			break;
	}

	// 1. state.js の状態を更新
	setWristAngle(newAngle);

	// 2. api.js の関数を使い、サーバーに送信
	console.log(`手首の角度: ${newAngle}度`);
	sendCommand('set_angle_wrist', newAngle);
}

/**
 * 肘の角度に基づいて画像を更新する
 * @param {number} angle - 表示したい角度
 */
function updateArmImage(angle) {
	console.log(`現在の肘の角度: ${angle}度`);

	if (robotStatusImage && ARM_IMAGE_MAP[angle]) {
		robotStatusImage.src = ARM_IMAGE_MAP[angle];
	} else {
		console.warn(`角度 ${angle} に対応する画像が ARM_IMAGE_MAP にありません。`);
	}
}

// ------------------------------------------------------------------
// 5. イベントリスナーの割り当て
// ------------------------------------------------------------------

// 肘（アーム）
if (armMoveHomeButton) {
	armMoveHomeButton.addEventListener('click', () => handleArmMove('home'));
}
if (armMoveUpButton) {
	armMoveUpButton.addEventListener('click', () => handleArmMove('up'));
}
if (armMoveDownButton) {
	armMoveDownButton.addEventListener('click', () => handleArmMove('down'));
}

// 手首（リスト）
if (wristmotorUpButton) {
	wristmotorUpButton.addEventListener('click', () => handleWristMotor('up'));
}
if (wristmotorHomeButton) {
	wristmotorHomeButton.addEventListener('click', () => handleWristMotor('home'));
}
if (wristmotorDownButton) {
	wristmotorDownButton.addEventListener('click', () => handleWristMotor('down'));
}

// ------------------------------------------------------------------
// 6. 他のファイルから `import` される関数 (あれば)
// ------------------------------------------------------------------

// (例: 電源ON時に main.js から updateArmImage(ANGLE_HOME) を呼ぶ場合)
// export { updateArmImage };
// (今回は main.js 側で直接 state をリセットし、
//  robotModal.js 側で updateArmImage を呼ぶように変更しました)

// (※) `updateArmImage` は `main.js` の電源ON処理からも
// 呼び出す必要があるため、`export` します。
export { updateArmImage };