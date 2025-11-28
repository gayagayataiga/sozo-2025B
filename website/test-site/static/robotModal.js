// /**
//  * robotModal.js
//  * * ロボット操作モーダルのすべてのUI操作を担当するファイル。
//  * * state.js から現在の角度や電源状態を、
//  * * api.js から sendCommand 関数をインポートして使用します。
//  */

// // ------------------------------------------------------------------
// // 1. 必要なモジュールをインポート
// // ------------------------------------------------------------------

// // state.js から状態と定数、セッター関数をインポート
// import {
// 	isPowerOn,
// 	currentArmAngle,
// 	currentWristAngle,
// 	setArmAngle,
// 	setWristAngle,
// 	ANGLE_HOME,
// 	ANGLE_STEP,
// 	ANGLE_MIN,
// 	ANGLE_MAX,
// 	WRIST_ANGLE_HOME,
// 	WRIST_ANGLE_STEP,
// 	WRIST_ANGLE_MIN,
// 	WRIST_ANGLE_MAX
// } from './state.js';

// // api.js からサーバー通信関数をインポート
// import { sendCommand } from './api.js';

// // ------------------------------------------------------------------
// // 2. このファイル固有の定数とDOM取得
// // ------------------------------------------------------------------

// // (注意) lightingModal.js でも settingModal をインポートする必要があります
// const settingModal = document.getElementById('setting-modal');

// // --- HTML要素の取得 ---
// const openRobotMoveButton = document.getElementById('open-robot-move-button');
// const robotMoveModal = document.getElementById('robot-move-modal');

// // モーダル内のロボット操作ボタン
// const armMoveHomeButton = document.getElementById('arm-move-home');
// const armMoveUpButton = document.getElementById('arm-move-up');
// const armMoveDownButton = document.getElementById('arm-move-down');

// const wristmotorUpButton = document.getElementById('wrist-motor-up');
// const wristmotorHomeButton = document.getElementById('wrist-motor-home');
// const wristmotorDownButton = document.getElementById('wrist-motor-down');

// // 画像
// const robotStatusImage = document.getElementById('robot-status-image');

// // --- 画像の対応表 ---
// // (※このファイルが管理する肘の角度と画像のマップ)
// const ARM_IMAGE_MAP = {
// 	0: '../static/photo/arm.jpg',
// 	30: '../static/photo/arm - コピー.jpg',
// 	60: '../static/photo/arm - コピー (2).jpg',
// 	90: '../static/photo/arm - コピー (3).jpg',
// };

// // ------------------------------------------------------------------
// // 3. モーダルの「開閉」イベント
// // ------------------------------------------------------------------

// // 「ロボット動作を開く」ボタンが押されたらモーダルを表示
// if (openRobotMoveButton) {
// 	openRobotMoveButton.addEventListener('click', () => {
// 		robotMoveModal.classList.remove('hidden');
// 		if (settingModal) {
// 			settingModal.classList.add('hidden'); // ※ 照明モーダルを閉じる
// 		}
// 	});
// }

// // ロボットモーダルの外側（半透明部分）がクリックされたら非表示
// if (robotMoveModal) {
// 	robotMoveModal.addEventListener('click', (e) => {
// 		// クリックされたのがモーダル自身（.modal-contentではない）であることを確認
// 		if (e.target === robotMoveModal) {
// 			robotMoveModal.classList.add('hidden');
// 		}
// 	});
// }

// // ------------------------------------------------------------------
// // 4. モーダル内のボタン操作
// // ------------------------------------------------------------------

// /**
//  * 肘（アーム）の操作
//  * @param {string} action 'home', 'up', 'down'
//  */
// function handleArmMove(action) {
// 	// state.js から isPowerOn を参照
// 	if (!isPowerOn) {
// 		alert('電源がオフです。電源をオンにしてください。');
// 		return;
// 	}

// 	// state.js から currentArmAngle を参照
// 	let newAngle = currentArmAngle;

// 	switch (action) {
// 		case 'home':
// 			newAngle = ANGLE_HOME;
// 			break;
// 		case 'up': // 「アームを上へ」
// 			if (currentArmAngle + ANGLE_STEP > ANGLE_MAX) {
// 				alert('これ以上アームを上げることはできません。');
// 			}
// 			newAngle = Math.min(currentArmAngle + ANGLE_STEP, ANGLE_MAX);
// 			break;
// 		case 'down': // 「アームを下へ」
// 			if (currentArmAngle - ANGLE_STEP < ANGLE_MIN) {
// 				alert('これ以上アームを下げることはできません。');
// 			}
// 			newAngle = Math.max(currentArmAngle - ANGLE_STEP, ANGLE_MIN);
// 			break;
// 	}

// 	// 1. state.js の状態を更新
// 	setArmAngle(newAngle);

// 	// 2. api.js の関数を使い、サーバーに送信
// 	sendCommand('set_angle_elbow', newAngle);

// 	// 3. UI（画像）を更新
// 	updateArmImage(newAngle);
// }

// /**
//  * 手首（リスト）の操作
//  * @param {string} action 'home', 'up', 'down'
//  */
// function handleWristMotor(action) {
// 	if (!isPowerOn) {
// 		alert('電源がオフです。電源をオンにしてください。');
// 		return;
// 	}

// 	let newAngle = currentWristAngle;

// 	switch (action) {
// 		case 'home':
// 			newAngle = WRIST_ANGLE_HOME;
// 			break;
// 		case 'up': // 「上へ」
// 			if (currentWristAngle + WRIST_ANGLE_STEP > WRIST_ANGLE_MAX) {
// 				alert('これ以上手首を上げることはできません。');
// 			}
// 			newAngle = Math.min(currentWristAngle + WRIST_ANGLE_STEP, WRIST_ANGLE_MAX);
// 			break;
// 		case 'down': // 「下へ」
// 			if (currentWristAngle - WRIST_ANGLE_STEP < WRIST_ANGLE_MIN) {
// 				alert('これ以上手首を下げることはできません。');
// 			}
// 			newAngle = Math.max(currentWristAngle - WRIST_ANGLE_STEP, WRIST_ANGLE_MIN);
// 			break;
// 	}

// 	// 1. state.js の状態を更新
// 	setWristAngle(newAngle);

// 	// 2. api.js の関数を使い、サーバーに送信
// 	console.log(`手首の角度: ${newAngle}度`);
// 	sendCommand('set_angle_wrist', newAngle);
// }

// /**
//  * 肘の角度に基づいて画像を更新する
//  * @param {number} angle - 表示したい角度
//  */
// function updateArmImage(angle) {
// 	console.log(`現在の肘の角度: ${angle}度`);

// 	if (robotStatusImage && ARM_IMAGE_MAP[angle]) {
// 		robotStatusImage.src = ARM_IMAGE_MAP[angle];
// 	} else {
// 		console.warn(`角度 ${angle} に対応する画像が ARM_IMAGE_MAP にありません。`);
// 	}
// }

// // ------------------------------------------------------------------
// // 5. イベントリスナーの割り当て
// // ------------------------------------------------------------------

// // 肘（アーム）
// if (armMoveHomeButton) {
// 	armMoveHomeButton.addEventListener('click', () => handleArmMove('home'));
// }
// if (armMoveUpButton) {
// 	armMoveUpButton.addEventListener('click', () => handleArmMove('up'));
// }
// if (armMoveDownButton) {
// 	armMoveDownButton.addEventListener('click', () => handleArmMove('down'));
// }

// // 手首（リスト）
// if (wristmotorUpButton) {
// 	wristmotorUpButton.addEventListener('click', () => handleWristMotor('up'));
// }
// if (wristmotorHomeButton) {
// 	wristmotorHomeButton.addEventListener('click', () => handleWristMotor('home'));
// }
// if (wristmotorDownButton) {
// 	wristmotorDownButton.addEventListener('click', () => handleWristMotor('down'));
// }

// // ------------------------------------------------------------------
// // 6. 他のファイルから `import` される関数 (あれば)
// // ------------------------------------------------------------------

// // (例: 電源ON時に main.js から updateArmImage(ANGLE_HOME) を呼ぶ場合)
// // export { updateArmImage };
// // (今回は main.js 側で直接 state をリセットし、
// //  robotModal.js 側で updateArmImage を呼ぶように変更しました)

// // (※) `updateArmImage` は `main.js` の電源ON処理からも
// // 呼び出す必要があるため、`export` します。
// export { updateArmImage };

/**
 * robotModal.js
 * * ロボット操作モーダルのUI操作（スライダー版）
 */

// ------------------------------------------------------------------
// 1. 必要なモジュールをインポート
// ------------------------------------------------------------------
import {
	isPowerOn,
	currentArmAngle,
	currentWristAngle,
	currentShoulderAngle,
	setArmAngle,
	setWristAngle,
	setShoulderAngle,
	ANGLE_HOME,
	WRIST_ANGLE_HOME,
	SHOULDER_ANGLE_HOME,
} from './state.js';

import { sendCommand } from './api.js';

// ------------------------------------------------------------------
// 2. DOM要素の取得
// ------------------------------------------------------------------

// モーダル制御用
const settingModal = document.getElementById('setting-modal');
const openRobotMoveButton = document.getElementById('open-robot-move-button');
const robotMoveModal = document.getElementById('robot-move-modal');

// --- 肘（アーム）コントロール要素 ---
const armSlider = document.getElementById('arm-slider');          // スライダー
const armDisplay = document.getElementById('arm-value-display');  // 数値表示
const armHomeButton = document.getElementById('arm-home');        // Homeボタン

// --- 手首（リスト）コントロール要素 ---
const wristSlider = document.getElementById('wrist-slider');
const wristDisplay = document.getElementById('wrist-value-display');
const wristHomeButton = document.getElementById('wrist-home');

// --- 肩コントロール要素 ---
const shoulderSlider = document.getElementById('shoulder-slider');
const shoulderDisplay = document.getElementById('shoulder-value-display');
const shoulderHomeButton = document.getElementById('shoulder-home');

// 画像要素
const robotStatusImage = document.getElementById('robot-status-image');

// --- 画像の対応表 ---
// キーを数値にしておくと計算しやすい
const ARM_IMAGE_MAP = {
	0: '../static/photo/arm.jpg',
	30: '../static/photo/arm - コピー.jpg',
	60: '../static/photo/arm - コピー (2).jpg',
	90: '../static/photo/arm - コピー (3).jpg',
};

// ------------------------------------------------------------------
// 3. モーダルの開閉イベント
// ------------------------------------------------------------------

if (openRobotMoveButton) {
	openRobotMoveButton.addEventListener('click', () => {
		robotMoveModal.classList.remove('hidden');
		if (settingModal) settingModal.classList.add('hidden');

		// モーダルを開いた瞬間に、現在の値をスライダーに反映させる
		syncSlidersToState();
	});
}

if (robotMoveModal) {
	robotMoveModal.addEventListener('click', (e) => {
		if (e.target === robotMoveModal) {
			robotMoveModal.classList.add('hidden');
		}
	});
}

/**
 * 現在の内部状態(state.js)の値を、スライダーと数値表示に反映する関数
 */
function syncSlidersToState() {
	if (armSlider && armDisplay) {
		armSlider.value = currentArmAngle;
		armDisplay.textContent = currentArmAngle;
		updateArmImage(currentArmAngle); // 画像も更新
	}
	if (wristSlider && wristDisplay) {
		wristSlider.value = currentWristAngle;
		wristDisplay.textContent = currentWristAngle;
	}
	if (shoulderSlider && shoulderDisplay) {
		shoulderSlider.value = currentShoulderAngle;
		shoulderDisplay.textContent = currentShoulderAngle;
	}
}


/**
 * 肘スライダーのセットアップ
 */
if (armSlider) {
	// 1. ドラッグ中：数値表示だけ更新（ロボットには送らない）
	armSlider.addEventListener('input', (e) => {
		armDisplay.textContent = e.target.value;
	});

	// 2. ドラッグ終了時：ロボットに命令送信
	armSlider.addEventListener('change', (e) => {
		const newAngle = parseInt(e.target.value, 10);
		handleArmChange(newAngle);
	});
}

/**
 * 手首スライダーのセットアップ
 */
if (wristSlider) {
	wristSlider.addEventListener('input', (e) => {
		wristDisplay.textContent = e.target.value;
	});

	wristSlider.addEventListener('change', (e) => {
		const newAngle = parseInt(e.target.value, 10);
		handleWristChange(newAngle);
	});
}

// 肩スライダーのセットアップ（必要に応じて追加）
if (shoulderSlider) {
	shoulderSlider.addEventListener('input', (e) => {
		shoulderDisplay.textContent = e.target.value;
	});

	shoulderSlider.addEventListener('change', (e) => {
		const newAngle = parseInt(e.target.value, 10);
		handleShoulderChange(newAngle);
	});
}

/**
 * 肘の値を変更して送信する処理
 */
function handleArmChange(angle) {
	// 電源チェック
	if (!isPowerOn) {
		alert('電源がオフです。電源をオンにしてください。');
		// 電源オフならスライダーを元の位置に戻す
		armSlider.value = currentArmAngle;
		armDisplay.textContent = currentArmAngle;
		return;
	}

	// 1. state更新
	setArmAngle(angle);

	// 2. API送信
	sendCommand('set_angle_elbow', angle);

	// 3. 画像更新
	updateArmImage(angle);
}

/**
 * 手首の値を変更して送信する処理
 */
function handleWristChange(angle) {
	if (!isPowerOn) {
		alert('電源がオフです。電源をオンにしてください。');
		wristSlider.value = currentWristAngle;
		wristDisplay.textContent = currentWristAngle;
		return;
	}

	setWristAngle(angle);
	sendCommand('set_angle_wrist', angle);
}

// 肩の値を変更して送信する処理（必要に応じて追加）
function handleShoulderChange(angle) {
	if (!isPowerOn) {
		alert('電源がオフです。電源をオンにしてください。');
		shoulderSlider.value = currentShoulderAngle;
		shoulderDisplay.textContent = currentShoulderAngle;
		return;
	}

	setShoulderAngle(angle);
	sendCommand('set_angle_shoulder', angle);
}

// ------------------------------------------------------------------
// 5. Homeボタンのロジック
// ------------------------------------------------------------------

if (armHomeButton) {
	armHomeButton.addEventListener('click', () => {
		if (!isPowerOn) {
			alert('電源がオフです。');
			return;
		}
		// UIをホーム位置に動かす
		armSlider.value = ANGLE_HOME;
		armDisplay.textContent = ANGLE_HOME;

		// 変更処理を実行
		handleArmChange(ANGLE_HOME);
	});
}

if (wristHomeButton) {
	wristHomeButton.addEventListener('click', () => {
		if (!isPowerOn) {
			alert('電源がオフです。');
			return;
		}
		wristSlider.value = WRIST_ANGLE_HOME;
		wristDisplay.textContent = WRIST_ANGLE_HOME;

		handleWristChange(WRIST_ANGLE_HOME);
	});
}

if (shoulderHomeButton) {
	shoulderHomeButton.addEventListener('click', () => {
		if (!isPowerOn) {
			alert('電源がオフです。');
			return;
		}
		shoulderSlider.value = SHOULDER_ANGLE_HOME;
		shoulderDisplay.textContent = SHOULDER_ANGLE_HOME;

		handleShoulderChange(SHOULDER_ANGLE_HOME);
	});
}


/**
 * 肘の角度に基づいて画像を更新する
 * マップにない角度(例: 45度)の場合、一番近い画像の角度を探して表示する
 * @param {number} angle 
 */
function updateArmImage(angle) {
	if (!robotStatusImage) return;

	// 定義されている角度キーを取得 [0, 30, 60, 90]
	const mapKeys = Object.keys(ARM_IMAGE_MAP).map(Number);

	// 一番近い角度を探す
	const closestAngle = mapKeys.reduce((prev, curr) => {
		return (Math.abs(curr - angle) < Math.abs(prev - angle) ? curr : prev);
	});

	console.log(`現在の角度: ${angle} -> 表示画像: ${closestAngle}度用`);

	const imagePath = ARM_IMAGE_MAP[closestAngle];
	if (imagePath) {
		robotStatusImage.src = imagePath;
	}
}

// ------------------------------------------------------------------
// 7. エクスポート
// ------------------------------------------------------------------
export { updateArmImage };