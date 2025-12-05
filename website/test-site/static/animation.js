/* --- 設定 --- */

// 集中度に応じた4つの画像グループ
const imageGroups = {
	// グループ1: 集中度 低 (0-25%)
	group1: [
		'../static/photo/updown/group1/updownup.png',
		'../static/photo/updown/group1/updowndown.png'
	],
	// グループ2: 集中度 中低 (26-50%)
	group2: [
		'../static/photo/updown/group2/updownup.png',
		'../static/photo/updown/group2/updowndown.png'
	],
	// グループ3: 集中度 中高 (51-75%)
	group3: [
		'../static/photo/updown/group3/updownup.png',
		'../static/photo/updown/group3/updowndown.png'
	],
	// グループ4: 集中度 高 (76-100%)
	group4: [
		'../static/photo/updown/group4/updownup.png',
		'../static/photo/updown/group4/updowndown.png'
	]
};

// 現在使用中の画像フレーム配列
let imageFrames = imageGroups.group1; // 初期値はグループ1

const intervalTime = 1000; // 1秒ごとに画像を切り替え

// --- HTML要素の取得 ---
const stopMotionImage = document.getElementById('stop-motion-image');

// --- アニメーション用変数 ---
let currentFrameIndex = 0;
let animationInterval = null; // setIntervalのIDを保存する変数
// --- アニメーションを開始する関数 ---
function startAnimation() {
	if (animationInterval) return;

	animationInterval = setInterval(() => {
		currentFrameIndex = (currentFrameIndex + 1) % imageFrames.length;
		if (stopMotionImage) {
			stopMotionImage.src = imageFrames[currentFrameIndex];
		}
	}, intervalTime);
}

// --- アニメーションを停止する関数 ---
function stopAnimation() {
	clearInterval(animationInterval);
	animationInterval = null;
	currentFrameIndex = 0;
	if (stopMotionImage) {
		stopMotionImage.src = imageFrames[0];
	}
}

// --- 集中度に応じて画像グループを変更する関数 ---
function setImageGroupByConcentration(concentrationLevel) {
	console.log('受信した集中度データ:', concentrationLevel);

	// 集中度の文字列を数値に変換
	let concentration = 0;

	if (typeof concentrationLevel === 'string') {
		// "High (85%)" や "75%" のような文字列から数値を抽出
		const match = concentrationLevel.match(/(\d+)/);
		if (match) {
			concentration = parseInt(match[1]);
		} else {
			// "Unknown" や "N/A" の場合はデフォルト値
			console.log('集中度が不明なため、デフォルト値(0)を使用します');
			concentration = 0;
		}
	} else if (typeof concentrationLevel === 'number') {
		concentration = concentrationLevel;
	}

	console.log('パースした集中度値:', concentration);

	// 集中度に応じてグループを選択
	let newGroup;
	let groupNumber;

	if (concentration <= 25) {
		newGroup = imageGroups.group1;
		groupNumber = 1;
	} else if (concentration <= 50) {
		newGroup = imageGroups.group2;
		groupNumber = 2;
	} else if (concentration <= 75) {
		newGroup = imageGroups.group3;
		groupNumber = 3;
	} else {
		newGroup = imageGroups.group4;
		groupNumber = 4;
	}

	// 画像グループが変更された場合のみ更新
	if (imageFrames !== newGroup) {
		imageFrames = newGroup;
		currentFrameIndex = 0;

		// アニメーションが実行中の場合は、即座に新しいグループの最初の画像を表示
		if (stopMotionImage) {
			stopMotionImage.src = imageFrames[0];
		}

		console.log(`✅ 画像グループを変更: 集中度 ${concentration}% -> グループ${groupNumber}`);
	} else {
		console.log(`画像グループは変更なし: グループ${groupNumber}`);
	}
}
