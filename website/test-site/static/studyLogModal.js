// モーダルを開くボタン
const openLogButton = document.getElementById('show-study-log-button');
// モーダル本体
const logModal = document.getElementById('study-log-modal');
// モーダルを閉じるボタン
const closeLogButton = document.getElementById('close-log-modal-button');

// 開くボタンが押された時の処理
if (openLogButton) {
	openLogButton.addEventListener('click', () => {
		logModal.classList.remove('hidden'); // hiddenクラスを削除して表示
		// TODO: ここで勉強記録をサーバーから取得する処理を呼ぶ
	});
}

// 閉じるボタンが押された時の処理
if (closeLogButton) {
	closeLogButton.addEventListener('click', () => {
		logModal.classList.add('hidden'); // hiddenクラスを追加して非表示
	});
}