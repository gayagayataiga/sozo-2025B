# ベースイメージに明示的な Python 3.11.8 を使用
FROM python:3.11.8-slim

ENV DEBIAN_FRONTEND=noninteractive

# 基本ツールをインストール
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       git \
       curl \
    && rm -rf /var/lib/apt/lists/*

# 非 root ユーザー vscode を作成（Codespaces が期待するユーザー）
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME || true \
 && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME || true

WORKDIR /workspace

# ビルド時に requirements.txt があればインストール（存在しなくても失敗しない）
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
 && if [ -f /tmp/requirements.txt ]; then pip install -r /tmp/requirements.txt || true; fi \
 && rm -f /tmp/requirements.txt

ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# コンテナを非rootユーザーで実行
USER $USERNAME

# デフォルトコマンド（Codespaces では上書きされる）
CMD ["sleep", "infinity"]
