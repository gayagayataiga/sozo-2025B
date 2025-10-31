# main.py & Servers - Architecture Overview

This document provides a focused overview of the `main.py` central controller and the server-related components within the project.

## 概要 (Overall Architecture)

このシステムのアーキテクチャは、中央制御を担う `main.py` と、データを受け取るための複数のサーバーコンポーネントによって構成されています。

1.  **データ入力**: `main.py` は `serverFolder/MakeCameraAsRas.py` 等から配信されるビデオストリームを直接処理します。並行して、`GetPhoto_SendFeatures.py` や `serverFolder/GetPhotoServer.py` といったFlaskサーバーが、Raspberry Piなどの外部デバイスから静止画像を受け取ります。
2.  **中央処理**: `main.py` は受け取ったストリームをリアルタイムで解析します。状態（探索→識別→分析）に応じて `detect` モジュールを呼び出し、顔の特徴量を抽出します。
3.  **AI連携**: `main.py` は、分析した特徴量の時系列データを `ai.py` に渡します。`ai.py` はそのデータを外部のAI分析サーバー（Colab）に送信し、高度な分析（集中度や眠気の推定など）を依頼します。

---

## 主要コンポーネント (Core Components)

### `main.py` (中心的な制御スクリプト)

アプリケーションの「頭脳」として機能するメインループです。

-   **役割**: リアルタイムのビデオストリームを取得し、人物の検出から顔の分析までの一連の処理を状態機械（ステートマシン）として管理します。
-   **状態遷移**: `STATE_SEARCHING_BODY` (人物探索) → `STATE_SEARCHING_FACE` (顔識別) → `STATE_ANALYZING_FACE` (顔分析) の順に状態が遷移します。
-   **連携モジュール**:
    -   `detect/detect_upperbody.py`: 人物の上半身を検出するために使用。
    -   `detect/detect_person.py`: 検出した顔が誰であるかを識別・追跡するために使用。
-   **非同期AI連携**:
    -   分析データが溜まると、`ai_input.json` ファイルに時系列データを書き出します。
    -   `subprocess.Popen` を使って `ai.py` を非同期で起動し、処理を依頼します。
    -   `ai.py` が出力を終えた `ai_result.json` を監視し、結果を読み取って `data.json` を更新します。

### `ai.py` (リモートAI分析ブリッジ)

`main.py` と外部のAIモデルを繋ぐ仲介役です。

-   **役割**: `main.py` によって起動され、`ai_input.json` から入力データを読み込みます。読み込んだデータを、ngrok経由で公開されているGoogle Colab上の分析サーバーにPOSTリクエストで送信します。
-   **出力**: Colabサーバーから受け取った分析結果（JSON）を、`main.py` が読み取れるように `ai_result.json` ファイルに書き出してから終了します。

### サーバーコンポーネント (Servers)

#### `GetPhoto_SendFeatures.py` (高機能ハブサーバー)

-   **役割**: 画像の受信から特徴量抽出、Colabへのデータ送信までを一台で担うFlaskサーバーです。
-   **エンドポイント**: `/process_pi_image`
-   **処理フロー**: Raspberry Pi等から画像を受信 → `im2csv.py` を使ってローカルで顔特徴量を抽出しCSV化 → 生成されたCSVファイルをColabサーバーの `/upload_csv` エンドポイントに直接送信します。

#### `serverFolder/GetPhotoServer.py` (シンプル画像受信サーバー)

-   **役割**: 画像を外部から受け取り、指定されたディレクトリに保存することに特化した軽量なFlaskサーバーです。
-   **エンドポイント**: `/upload_image`
-   **処理フロー**: 受信した画像ファイルにタイムスタンプを付けて `received_images/` ディレクトリに保存します。

#### `serverFolder/MakeCameraAsRas.py`

-   **役割**: (ファイル内容からの推測) Raspberry Piに接続されたカメラの映像を、MJPEG形式のビデオストリームとしてネットワークに配信するサーバーと思われます。`main.py` は、ここで配信されるストリームURL (`http://<IP_ADDRESS>:5000/video_feed`) に接続して映像を取得します。

---

## 関連ディレクトリ (Related Directories)

-   `detect/`: `main.py` が使用する、人物の検出・識別・追跡といった中核的なロジックを格納します。
-   `serverFolder/`: 上記で説明した、各種サーバー機能を持つスクリプトが格納されています。
-   `received_images/`: サーバーが外部デバイスから受信した画像や、その処理結果が保存される場所です。
