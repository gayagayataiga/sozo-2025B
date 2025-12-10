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
const controlURL = `http://${LOCAL_PC_IP}:5003/api/control`;

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
export const socket = io(`http://${LOCAL_PC_IP}:5003`);

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
	console.log('📨 WebSocketで受信したデータ (api.js):', data);

	const concentrationDisplay = document.getElementById('concentration');
	if (concentrationDisplay) {
		const level = data.concentration_level || 'Unknown';
		concentrationDisplay.textContent = level;

		// 集中度に応じて画像グループを変更
		// High, Medium, Low, Unknown の4段階に対応
		if (typeof setImageGroupByConcentration === 'function') {
			console.log('🎯 集中度レベル (level変数):', level);

			// level変数から集中度カテゴリを抽出
			// "High (85%)" → "High"
			// "Medium" → "Medium"
			// "Low" → "Low"
			// "Unknown" または "N/A" → "Unknown"
			let levelCategory = 'Unknown'; // デフォルト値

			if (typeof level === 'string') {
				// 文字列から High, Medium, Low を検索（大文字小文字区別なし）
				if (level.match(/High/i)) {
					levelCategory = 'High';
				} else if (level.match(/Medium/i)) {
					levelCategory = 'Medium';
				} else if (level.match(/Low/i)) {
					levelCategory = 'Low';
				}
				// それ以外（"Unknown", "N/A"など）はデフォルトの "Unknown" のまま
			}

			// concentration_level を画像グループに変換
			// High → グループ4 (集中度 高: 76-100%)
			// Medium → グループ2 (集中度 中低: 26-50%)
			// Low → グループ1 (集中度 低: 0-25%)
			// Unknown → グループ1 (集中度 低: 0-25%)
			const groupMapping = {
				'High': 4,
				'Medium': 2,
				'Low': 1,
				'Unknown': 1
			};

			const groupNumber = groupMapping[levelCategory];

			// グループ番号に対応する集中度パーセンテージを計算
			// グループ1: 12% (Low/Unknown)
			// グループ2: 38% (Medium)
			// グループ3: 63% (使用しない)
			// グループ4: 88% (High)
			const concentrationPercent = groupNumber === 4 ? 88 :
				groupNumber === 3 ? 63 :
					groupNumber === 2 ? 38 : 12;

			console.log(`🔄 画像グループ変更: level="${level}" → カテゴリ="${levelCategory}" → グループ${groupNumber} (${concentrationPercent}%)`);
			setImageGroupByConcentration(concentrationPercent);
		} else {
			console.warn('⚠️ setImageGroupByConcentration関数が見つかりません');
		}
	}

	const nameElement = document.getElementById('username-display');
	if (nameElement) {
		// データに username が入っていれば表示、なければ 'ゲスト'
		nameElement.textContent = data.username || 'ゲスト';
	}
});

/**
 * 勉強時間をサーバーに保存する (POST /api/log)
 * (main.js から呼ばれることを想定)
 * @param {string} duration - "HH:MM:SS" 形式の経過時間
 */
export async function saveStudyLog(duration) {
	try {
		const response = await fetch(`${API_BASE_URL}/api/log`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify({ duration: duration }),
		});
		if (!response.ok) {
			throw new Error(`ログの保存に失敗しました: ${response.status}`);
		}
		console.log(`✅ 勉強記録の保存成功: ${duration}`);
		return await response.json();
	} catch (error) {
		console.error('❌ saveStudyLog エラー:', error);
		return null;
	}
}

/**
 * 勉強記録の履歴をサーバーから取得する (GET /api/logs)
 * (studyLogModal.js から呼ばれることを想定)
 * @returns {Promise<Array|null>} 記録の配列、またはエラー時 null
 */
export async function fetchStudyLogs() {
	try {
		const response = await fetch(`${API_BASE_URL}/api/logs`);
		if (!response.ok) {
			throw new Error(`ログの取得に失敗しました: ${response.status}`);
		}
		const logs = await response.json();
		console.log(`✅ 勉強記録の取得成功 (${logs.length}件)`);
		return logs;
	} catch (error) {
		console.error('❌ fetchStudyLogs エラー:', error);
		return null;
	}
}