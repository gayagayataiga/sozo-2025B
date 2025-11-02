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

// 肘 (Arm)
export const ANGLE_HOME = 90;
export const ANGLE_STEP = 10;
export const ANGLE_MIN = 70;
export const ANGLE_MAX = 100;

// 手首 (Wrist)
export const WRIST_ANGLE_HOME = 45;
export const WRIST_ANGLE_STEP = 5;
export const WRIST_ANGLE_MIN = 30;
export const WRIST_ANGLE_MAX = 60;


// --- アプリケーションの現在の状態 (State) ---

// 電源状態
export let isPowerOn = false;

// タイマー状態
export let startTime = 0;
export let timerInterval = null;

// モーターの現在角度
export let currentArmAngle = ANGLE_HOME;
export let currentWristAngle = WRIST_ANGLE_HOME;


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