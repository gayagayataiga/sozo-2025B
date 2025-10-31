# Project Souzou - Architecture Overview

This document provides an overview of the project structure and the purpose of each component.

## 概要 (Overall Architecture)

This project is a real-time face analysis and recognition system. It appears to be designed in a modular way:

1.  **Data Acquisition**: A video stream is captured (`main.py`) or images are received from an external source like a Raspberry Pi (`GetPhoto_SendFeatures.py`, `serverFolder/GetPhotoServer.py`).
2.  **Detection & Recognition**: The system first detects upper bodies, then faces. It identifies known individuals and tracks them (`detect/detect_person.py`).
3.  **Feature Extraction**: For detected faces, it extracts a rich set of features like eye-opening (EAR), mouth-opening (MAR), and head pose (`analyze/analyze_face.py`, `face_analyzer.py`).
4.  **AI Analysis**: Time-series data of these features is sent to a remote server (Google Colab) for higher-level analysis (e.g., drowsiness or concentration prediction) (`ai.py`).
5.  **State Management**: The main application (`main.py`) operates as a state machine, transitioning between searching for people, identifying them, and analyzing them.

---

## ディレクトリ構成 (Directory Structure)

### ルートディレクトリ (`/`)

-   `main.py`: **[中心的な制御スクリプト]** アプリケーションのメインループ。ビデオストリームを取得し、状態（人物探索→顔識別→顔分析）を管理する。`detect`と`analyze`モジュールを呼び出し、非同期で`ai.py`をトリガーする。
-   `ai.py`: **[リモートAI分析スクリプト]** `main.py`から起動される。顔特徴量の時系列データを`ai_input.json`から読み込み、Google Colab上の分析サーバーに送信し、結果を`ai_result.json`に書き込む。
-   `face_analyzer.py`: **[顔特徴量計算ライブラリ]** 画像からEAR（目の開き）、MAR（口の開き）、頭の傾きなどの詳細な顔特徴量を計算する関数群。
-   `file_utils.py`: **[ファイル保存ユーティリティ]** 抽出した特徴量をCSVファイルに保存したり、解析結果（バウンディングボックスなど）を描画した画像を保存するヘルパー関数。
-   `GetPhoto_SendFeatures.py`: **[Flaskサーバー]** Raspberry Pi等から画像を受信し、特徴量抽出(`im2csv`)からColabへのCSV送信までの一連のパイプラインを実行する中央ハブサーバー。
-   `im2csv.py`: **[画像→CSV変換スクリプト]** 単一の画像を受け取り、顔分析を行い、結果をCSVと注釈付き画像として保存する処理をまとめたもの。
-   `data.json`: `main.py`と`ai.py`が情報を共有するために使用されるJSONファイル。AIの分析結果などが書き込まれる。
-   `ai_input.json` / `ai_log.txt`: `main.py`が`ai.py`を呼び出す際に、入力データとログを渡すための一時ファイル。
-   `*.pdf`: プロジェクトに関連するドキュメント。
-   (その他のスクリプト): `make-dot.py`, `makecsv.py`, `resize.py`, `seeMovie_fromras.py`, `useim2csv.py` は、データ作成やテスト、補助的な処理に使われるスクリプトの可能性が高い。

### `analyze/`

-   `analyze_face.py`: **[顔分析クラス]** `face_analyzer.py`のクラスベース版。dlibモデルをロードし、EAR、MAR、頭部姿勢、さらには顔認証用のベクトル（embedding）まで計算する、より構造化された分析モジュール。

### `detect/`

-   `detect_person.py`: **[人物識別・追跡クラス]** `PersonIdentifier`クラスを定義。顔検出、`known_faces`内の人物との照合による身元識別、未知の人物の自動登録、`dlib.correlation_tracker`を使った高速な顔追跡など、このプロジェクトの核となる機能を持つ。
-   `detect_face.py`, `detect_upperbody.py`: 顔や上半身を検出するための個別のスクリプト。`main.py`や`detect_person.py`から利用される。

### `dlib/`

-   `*.dat`: dlibライブラリが使用する学習済みモデルファイル。顔のランドマーク検出（68点）や顔認証に使われる。

### `known_faces/`

-   人物名のサブディレクトリ（例: `Gayagaya/`, `ussi/`）を格納する。各ディレクトリには、その人物の顔画像を入れ、`detect_person.py`が起動時に読み込んで顔認証の辞書を作成する。`Unknown_*`ディレクトリは、未知の人物が検出された際に自動で作成される。

### `received_images/`

-   `GetPhotoServer.py`などのサーバーが、外部（Raspberry Piなど）から受信した画像や、それらを処理した中間生成物（CSV、加工後画像）を保存するディレクトリ。

### `output/`

-   `im2csv.py`などの処理結果（CSVや画像）が保存されるデフォルトの出力ディレクトリ。

### `serverFolder/`

-   `GetPhotoServer.py`: **[Flaskサーバー]** 外部から画像を受信し、`received_images`にタイムスタンプ付きで保存するだけのシンプルなサーバー。
-   `MakeCameraAsRas.py`: Raspberry PiをWebカメラ化してストリーミング配信するためのサーバーコードの可能性が高い。

### `sozo/`

-   Pythonの仮想環境（Virtual Environment）ディレクトリ。プロジェクトの依存ライブラリがここにインストールされる。

### その他

-   `__pycache__/`: Pythonが生成するコンパイル済みバイトコードのキャッシュ。
-   `images/`, `FindFace/`, `HabCode/`, `website/`: それぞれ、テスト用画像、過去の実験コード、通信関連コード、Webインターフェース用のディレクトリと思われる。
