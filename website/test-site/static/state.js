// code for states
// アプリケーション全体の「現在の状態」を保存
/**
 * state.js
 * * アプリケーション全体の「状態」と、
 * それを定義する「定数」を管理するファイル。
 * * 他のファイル (main.js, robotModal.jsなど) は、
 * ここから定数や状態を import して使用します。
 */

// --- ロボットの動作を定義する定数 ---
// ※ server.pyとconfig.pyの初期角度と一致させること

// 肘 (Arm) - 初期位置90度
export const ANGLE_HOME = 90;
export const ANGLE_STEP = 1;
export const ANGLE_MIN = 50;
export const ANGLE_MAX = 130;

// 手首 (Wrist) - 初期位置45度
export const WRIST_ANGLE_HOME = 45;
export const WRIST_ANGLE_STEP = 5;
export const WRIST_ANGLE_MIN = 15;
export const WRIST_ANGLE_MAX = 75;

// 肩 (Shoulder) - 初期位置90度
export const SHOULDER_ANGLE_HOME = 90;
export const SHOULDER_ANGLE_STEP = 5;
export const SHOULDER_ANGLE_MIN = 70;
export const SHOULDER_ANGLE_MAX = 110;


// --- アプリケーションの現在の状態 (State) ---

// 電源状態
export let isPowerOn = false;

// タイマー状態
export let startTime = 0;
export let timerInterval = null;

// モーターの現在角度
export let currentArmAngle = ANGLE_HOME;
export let currentWristAngle = WRIST_ANGLE_HOME;
export let currentShoulderAngle = SHOULDER_ANGLE_HOME;

// --- 状態を変更するための関数 (Setter) ---
// 他のファイルは、状態を直接変更する代わりに
// これらの関数を呼び出すことを推奨します。

export function setPowerOn(value) {
	isPowerOn = value;
}

export function setStartTime(time) {
	startTime = time;
}

export function setTimerInterval(interval) {
	timerInterval = interval;
}

export function setArmAngle(angle) {
	currentArmAngle = angle;
}

export function setWristAngle(angle) {
	currentWristAngle = angle;
}

export function setShoulderAngle(angle) {
	currentShoulderAngle = angle;
}
