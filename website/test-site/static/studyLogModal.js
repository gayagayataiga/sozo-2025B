// モーダルを開くボタン
const openLogButton = document.getElementById('show-study-log-button');
// モーダル本体
const logModal = document.getElementById('study-log-modal');
// モーダルを閉じるボタン
const closeLogButton = document.getElementById('close-log-modal-button');

// 勉強記録を取得して表示する関数
async function loadStudyLogs() {
	const loadingIndicator = document.getElementById('loading-indicator');
	const studyLogsList = document.getElementById('study-logs-list');

	try {
		// ローディング表示
		loadingIndicator.style.display = 'block';
		studyLogsList.innerHTML = '';

		// 現在のユーザー名を取得
		const usernameElement = document.getElementById('username-display');
		const currentUsername = usernameElement ? usernameElement.textContent : null;

		// ゲストの場合はユーザー名を指定しない（全ユーザーの記録を表示）
		const username = (currentUsername && currentUsername !== 'ゲスト') ? currentUsername : null;

		// サーバーから勉強記録を取得（ユーザー名でフィルタ）
		let url = `http://${LOCAL_PC_IP}:5001/api/study-logs?limit=10`;
		if (username) {
			url += `&username=${encodeURIComponent(username)}`;
		}
		const response = await fetch(url);
		const result = await response.json();

		// ローディングを非表示
		loadingIndicator.style.display = 'none';

		if (result.status === 'success' && result.data.length > 0) {
			// 勉強記録を表示
			result.data.forEach(session => {
				const logItem = createStudyLogItem(session);
				studyLogsList.appendChild(logItem);
			});
		} else {
			studyLogsList.innerHTML = '<p style="text-align: center; color: #bb99ff;">勉強記録がありません</p>';
		}
	} catch (error) {
		console.error('勉強記録の取得に失敗:', error);
		loadingIndicator.style.display = 'none';
		studyLogsList.innerHTML = '<p style="text-align: center; color: #dc3545;">データの取得に失敗しました</p>';
	}
}

// 勉強記録の要素を作成する関数
function createStudyLogItem(session) {
	const item = document.createElement('div');
	item.className = 'study-log-item';

	// 日付のフォーマット
	const date = new Date(session.timestamp);
	const formattedDate = `${date.getFullYear()}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;

	// ライトの色を表示
	const lightColor = session.light_color;
	const lightColorStyle = `background-color: rgb(${lightColor.r}, ${lightColor.g}, ${lightColor.b});`;

	item.innerHTML = `
		<h4>📖 ${session.username} さんの記録</h4>
		<p>📅 日時: ${formattedDate}</p>
		<p>⏱️ 勉強時間: ${session.study_duration_minutes} 分</p>
		<p>💡 使用した照明色: <span class="light-color-display" style="${lightColorStyle}"></span></p>
		<div class="study-log-stats">
			<div class="stat-item">
				<span class="stat-label">平均集中度</span>
				<span class="stat-value">${session.concentration_avg ? session.concentration_avg.toFixed(1) : 'N/A'}</span>
			</div>
			<div class="stat-item">
				<span class="stat-label">最大集中度</span>
				<span class="stat-value">${session.concentration_max || 'N/A'}</span>
			</div>
			<div class="stat-item">
				<span class="stat-label">最小集中度</span>
				<span class="stat-value">${session.concentration_min || 'N/A'}</span>
			</div>
			<div class="stat-item">
				<span class="stat-label">照明明るさ</span>
				<span class="stat-value">${lightColor.brightness}%</span>
			</div>
		</div>
		${session.ratio_high !== undefined ? `
		<p style="margin-top: 10px; font-size: 0.9em;">
			🔥 高集中: ${(session.ratio_high * 100).toFixed(1)}% |
			🌟 中集中: ${(session.ratio_medium * 100).toFixed(1)}% |
			😴 低集中: ${(session.ratio_low * 100).toFixed(1)}%
		</p>
		` : ''}
	`;

	return item;
}

// 開くボタンが押された時の処理
if (openLogButton) {
	openLogButton.addEventListener('click', () => {
		logModal.classList.remove('hidden'); // hiddenクラスを削除して表示
		loadStudyLogs(); // 勉強記録を取得して表示
	});
}

// 閉じるボタンが押された時の処理
if (closeLogButton) {
	closeLogButton.addEventListener('click', () => {
		logModal.classList.add('hidden'); // hiddenクラスを追加して非表示
	});
}