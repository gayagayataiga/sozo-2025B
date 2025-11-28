/**
 * lightingModal.js
 * * 照明設定モーダルのすべてのUI操作を担当するファイル。
 * * api.js から sendCommand を、
 * * state.js から isPowerOn をインポートして使用します。
 */

// ------------------------------------------------------------------
// 1. 必要なモジュールをインポート
// ------------------------------------------------------------------

// state.js から電源状態をインポート
import { isPowerOn } from './state.js';

// api.js からサーバー通信関数をインポート
import { sendCommand } from './api.js';

// ------------------------------------------------------------------
// 2. このファイル固有のDOM取得
// ------------------------------------------------------------------

// (注意) robotModal.js でも robotMoveModal をインポートする必要があります
const robotMoveModal = document.getElementById('robot-move-modal');

// --- HTML要素の取得 ---
const settingModal = document.getElementById('setting-modal');
const openSettingsButton = document.getElementById('open-settings-button');
const closeButton = document.querySelector('.close-button'); // (※HTMLに .close-button がある場合)

// 明るさ
const modalBrightnessSlider = document.getElementById('brightness-slider-modal');
const modalBrightnessValue = document.getElementById('brightness-value-modal');
// (※もしメイン画面にも明るさ表示があれば、それも取得します)
// const brightnessValue = document.getElementById('brightness-value');

// 色
const pickerContainer = document.getElementById('picker-container');
const resetColorButton = document.getElementById('reset-color-button');
let picker = null; // カラーピッカーのインスタンスを保持

// ------------------------------------------------------------------
// 3. モーダルの「開閉」イベント
// ------------------------------------------------------------------

// 「照明設定を開く」ボタンが押されたらモーダルを表示
if (openSettingsButton) {
	openSettingsButton.addEventListener('click', () => {
		settingModal.classList.remove('hidden');
		if (robotMoveModal) {
			robotMoveModal.classList.add('hidden'); // ※ ロボットモーダルを閉じる
		}
	});
}

// 閉じるボタン（×ボタン）が押されたらモーダルを非表示
if (closeButton) {
	closeButton.addEventListener('click', () => {
		settingModal.classList.add('hidden');
	});
}

// モーダルの外側（半透明部分）がクリックされたら非表示
if (settingModal) {
	settingModal.addEventListener('click', (e) => {
		// クリックされたのがモーダル自身（.modal-contentではない）であることを確認
		if (e.target === settingModal) {
			settingModal.classList.add('hidden');
		}
	});
}

// ------------------------------------------------------------------
// 4. モーダル内のボタン操作
// ------------------------------------------------------------------

// --- 明るさスライダー ---
if (modalBrightnessSlider) {
	modalBrightnessSlider.addEventListener('input', (event) => {
		const value = parseInt(event.target.value);

		// モーダル内の値を更新
		if (modalBrightnessValue) modalBrightnessValue.textContent = value;
		// (メイン画面の値も更新する場合)
		// if (brightnessValue) brightnessValue.textContent = value;

		// サーバーに送信 (state.js の isPowerOn を参照)
		if (isPowerOn) {
			sendCommand('set_brightness', value);
		}
	});
}

// --- 色相環 (vanilla-picker) ---
if (pickerContainer) {
	picker = new Picker({
		parent: pickerContainer,
		popup: false,
		color: 'rgb(255, 0, 0)', // 初期色 (リセットボタンと合わせるなら 'rgb(255, 255, 255)')
		layout: 'hsv',
		editor: false,
		alpha: false,
		doneButton: false,

		onChange: color => {
			const rgbString = color.rgbString;
			console.log("選択された色:", rgbString);

			if (isPowerOn) {
				sendCommand('set_color_wheel', rgbString);
			}
		}
	});
}

// --- 色リセットボタン ---
if (resetColorButton) {
	resetColorButton.addEventListener('click', () => {
		if (isPowerOn) {
			const resetColor = 'rgb(255, 255, 255)'; // 白

			// 1. サーバーに送信
			sendCommand('set_color_wheel', resetColor);
			console.log('色をリセットしました:', resetColor);

			// 2. ピッカーのUIも更新
			if (picker) {
				picker.setColor(resetColor);
			}

		} else {
			alert('電源がオフです。色設定はできません。');
		}
	});
}

// --- (古い .color-btn の処理はここに含めない) ---