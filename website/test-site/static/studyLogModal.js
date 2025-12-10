// モーダルを開くボタン
const openLogButton = document.getElementById('show-study-log-button');
// モーダル本体
const logModal = document.getElementById('study-log-modal');
// モーダルを閉じるボタン
const closeLogButton = document.getElementById('close-log-modal-button');

// グラフインスタンスを保持
let weeklyChart = null;

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
		const currentUsername = usernameElement ? usernameElement.textContent.trim() : null;

		// サーバーから勉強記録を取得（ユーザー名でフィルタ）
		let url = `http://${LOCAL_PC_IP}:5003/api/study-logs?limit=10`;
		if (currentUsername && currentUsername !== 'ゲスト') {
			url += `&username=${encodeURIComponent(currentUsername)}`;
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

// 週間統計を取得して表示する関数
async function loadWeeklyStats() {
	const chartLoading = document.getElementById('chart-loading');
	const chartContainer = document.getElementById('weekly-chart-container');

	try {
		// ローディング表示
		chartLoading.style.display = 'block';
		chartContainer.style.display = 'none';

		// 現在のユーザー名を取得
		const usernameElement = document.getElementById('username-display');
		const currentUsername = usernameElement ? usernameElement.textContent.trim() : null;

		// サーバーから週間統計を取得
		let url = `http://${LOCAL_PC_IP}:5003/api/weekly-stats?days=7`;
		if (currentUsername && currentUsername !== 'ゲスト') {
			url += `&username=${encodeURIComponent(currentUsername)}`;
		}
		const response = await fetch(url);
		const result = await response.json();

		// ローディングを非表示
		chartLoading.style.display = 'none';
		chartContainer.style.display = 'block';

		if (result.status === 'success') {
			renderWeeklyChart(result.data);
		} else {
			console.error('週間統計の取得に失敗:', result.message);
		}
	} catch (error) {
		console.error('週間統計の取得に失敗:', error);
		chartLoading.style.display = 'none';
	}
}

// Chart.jsで週間グラフを描画する関数
function renderWeeklyChart(data) {
	const ctx = document.getElementById('weekly-chart').getContext('2d');

	// 既存のグラフがあれば破棄
	if (weeklyChart) {
		weeklyChart.destroy();
	}

	// データを準備
	const labels = data.map(d => {
		const date = new Date(d.date);
		return `${date.getMonth() + 1}/${date.getDate()}`;
	});
	const studyMinutes = data.map(d => d.total_minutes);

	// 集中度に基づいて色を決定する関数
	function getColorByConcentration(avgConcentration) {
		if (avgConcentration === null || avgConcentration === undefined) {
			// データがない場合はグレー
			return {
				background: 'rgba(128, 128, 128, 0.6)',
				border: 'rgba(128, 128, 128, 1)'
			};
		}

		// 集中度の閾値を設定 (適宜調整してください)
		if (avgConcentration >= 7) {
			// High: 赤
			return {
				background: 'rgba(255, 99, 99, 0.6)',
				border: 'rgba(255, 99, 99, 1)'
			};
		} else if (avgConcentration >= 4) {
			// Medium: 緑
			return {
				background: 'rgba(99, 255, 132, 0.6)',
				border: 'rgba(99, 255, 132, 1)'
			};
		} else {
			// Low: 青
			return {
				background: 'rgba(99, 132, 255, 0.6)',
				border: 'rgba(99, 132, 255, 1)'
			};
		}
	}

	// 各日の集中度に基づいて色を設定
	const backgroundColors = data.map(d => getColorByConcentration(d.avg_concentration).background);
	const borderColors = data.map(d => getColorByConcentration(d.avg_concentration).border);

	// グラフを作成
	weeklyChart = new Chart(ctx, {
		type: 'bar',
		data: {
			labels: labels,
			datasets: [{
				label: '勉強時間（分）',
				data: studyMinutes,
				backgroundColor: backgroundColors,
				borderColor: borderColors,
				borderWidth: 2,
				borderRadius: 8
			}]
		},
		options: {
			responsive: true,
			maintainAspectRatio: false,
			plugins: {
				legend: {
					display: true,
					labels: {
						color: '#f0f0f0',
						font: {
							size: 14
						}
					}
				},
				title: {
					display: true,
					text: '過去7日間の勉強時間',
					color: '#bb99ff',
					font: {
						size: 16,
						weight: 'bold'
					}
				}
			},
			scales: {
				y: {
					beginAtZero: true,
					ticks: {
						color: '#f0f0f0',
						callback: function(value) {
							return value + '分';
						}
					},
					grid: {
						color: 'rgba(255, 255, 255, 0.1)'
					}
				},
				x: {
					ticks: {
						color: '#f0f0f0'
					},
					grid: {
						color: 'rgba(255, 255, 255, 0.1)'
					}
				}
			}
		}
	});
}

// タブ切り替え機能
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

tabButtons.forEach(button => {
	button.addEventListener('click', () => {
		const targetTab = button.getAttribute('data-tab');

		// すべてのタブボタンとコンテンツから active クラスを削除
		tabButtons.forEach(btn => btn.classList.remove('active'));
		tabContents.forEach(content => content.classList.remove('active'));

		// クリックされたタブをアクティブに
		button.classList.add('active');

		// 対応するコンテンツを表示
		if (targetTab === 'list') {
			document.getElementById('log-content-area').classList.add('active');
		} else if (targetTab === 'chart') {
			document.getElementById('chart-content-area').classList.add('active');
			// グラフタブが開かれたら、データを読み込んで描画
			loadWeeklyStats();
		}
	});
});