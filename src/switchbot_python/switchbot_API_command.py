"""
SwitchBot照明制御コマンドモジュール
各状態（起きているとき、接続時、寝ているとき）の照明設定を定義するモジュール

このモジュールは設定値のみを定義し、実際の通信処理は呼び出し元で行う
"""

# ========================================================================
# 照明設定の定義（明るさ、RGB値）
# ========================================================================

# 覚醒時（起きているとき）の設定
AWAKE_SETTINGS = {
    "brightness": 30,
    "r": 255,
    "g": 255,
    "b": 255,
    "description": "覚醒モード（通常点灯）"
}

# 接続時（勉強用）の設定
CONNECT_SETTINGS = {
    "brightness": 50,
    "r": 255,
    "g": 255,
    "b": 200,
    "description": "接続モード（勉強用）"
}

# 睡眠検知時（起床促進）の設定
SLEEPING_SETTINGS = {
    "brightness": 80,
    "r": 255,
    "g": 0,
    "b": 0,
    "description": "睡眠検知モード（起床促進）"
}


# ========================================================================
# 呼び出し用関数（設定値を返すだけ）
# ========================================================================

def get_awake_settings():
    """
    覚醒時の照明設定を返す

    Returns:
        dict: {"brightness": int, "r": int, "g": int, "b": int, "description": str}
    """
    return AWAKE_SETTINGS.copy()


def get_connect_settings():
    """
    接続時（勉強用）の照明設定を返す

    Returns:
        dict: {"brightness": int, "r": int, "g": int, "b": int, "description": str}
    """
    return CONNECT_SETTINGS.copy()


def get_sleeping_settings():
    """
    睡眠検知時（起床促進）の照明設定を返す

    Returns:
        dict: {"brightness": int, "r": int, "g": int, "b": int, "description": str}
    """
    return SLEEPING_SETTINGS.copy()


# ========================================================================
# 全設定を取得する関数
# ========================================================================

def get_all_settings():
    """
    全ての照明設定を辞書で返す

    Returns:
        dict: {"awake": dict, "connect": dict, "sleeping": dict}
    """
    return {
        "awake": AWAKE_SETTINGS.copy(),
        "connect": CONNECT_SETTINGS.copy(),
        "sleeping": SLEEPING_SETTINGS.copy()
    }


# ========================================================================
# テスト用（このファイルを直接実行した場合）
# ========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SwitchBot照明設定モジュール")
    print("=" * 60)
    print("\n定義されている照明設定:")

    all_settings = get_all_settings()

    for mode_name, settings in all_settings.items():
        print(f"\n【{mode_name.upper()}】")
        print(f"  説明: {settings['description']}")
        print(f"  明るさ: {settings['brightness']}%")
        print(f"  RGB: ({settings['r']}, {settings['g']}, {settings['b']})")

    print("\n" + "=" * 60)
    print("使用例:")
    print("  from switchbot_API_command import get_connect_settings")
    print("  settings = get_connect_settings()")
    print("  # settingsを使って照明を制御")
    print("=" * 60)
