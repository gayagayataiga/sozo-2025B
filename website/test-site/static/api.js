/**
 * api.js
 * * サーバーとの通信（REST APIとWebSocket）を
 * 専門に担当するファイル。
 * * `sendCommand` と `socket` を export し、
 * 他のファイル (main.js, lightingModal.jsなど) が
 * サーバー通信を意識せず使えるようにします。
 */

// ------------------------------------------------------------------
// 1. サーバーへのコマンド送信 (REST API)
// ------------------------------------------------------------------

// (注意) LOCAL_PC_IP は HTML の <script> タグで定義されている
// グローバル変数 'LOCAL_PC_IP' を参照します。
const controlURL = `http://${LOCAL_PC_IP}:5001/api/control`;

/**
 * サーバーの /api/control エンドポイントにコマンドを送信する
 * @param {string} action - 'set_angle_elbow', 'set_color_wheel' など
 * @param {*} value - 'on', 90, 'rgb(255, 0, 0)' など
 */
export function sendCommand(action, value) {
	const data = { action: action, value: value };

	fetch(controlURL, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(data)
	})
		.then(response => {
			if (!response.ok) throw new Error(`送信失敗: ${response.status}`);
			console.log(`✅ コマンド送信成功: ${action}, ${value}`);
			return response.json();
		})
		.catch(error => console.error('❌ 通信エラー発生:', error));
}

// ------------------------------------------------------------------
// 2. サーバーからのデータ受信 (WebSocket)
// ------------------------------------------------------------------

// WebSocket 接続を初期化
// (こちらもグローバルな 'LOCAL_PC_IP' を参照)
export const socket = io(`http://${LOCAL_PC_IP}:5001`);

// 接続イベント (main.js や status.js に移動しても良い)
socket.on('connect', () => {
	// (※) DOM操作は api.js の責務ではないため、
	// 本来は main.js が socket.on('connect') をリッスンすべき。
	// 今回は元のロジックをそのまま移植します。
	const statusText = document.getElementById('status-text');
	if (statusText) {
		statusText.textContent = 'ロボットの状態：接続済み (PCサーバー)';
	}
	console.log("✅ WebSocket 接続成功");
});

socket.on('disconnect', () => {
	const statusText = document.getElementById('status-text');
	if (statusText) {
		statusText.textContent = 'ロボットの状態：切断中';
	}
	console.log("❌ WebSocket 切断");
});

// 'status_update' イベント
// (※) これも main.js や concentration.js など、
// 集中度を表示する責務を持つファイルに移動する方が
// 本来は望ましいです。
socket.on('status_update', (data) => {
	console.log('受信データ:', data);

	const concentrationDisplay = document.getElementById('concentration');
	if (concentrationDisplay) {
		const level = data.concentration_level || 'N/A';
		concentrationDisplay.textContent = level;
	}

	// (animation.js に関連するロジックはここには含めない)
});