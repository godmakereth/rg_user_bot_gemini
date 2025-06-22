# 檔案：handlers/states.py
# 職責：定義所有使用者狀態 (Enum)，讓程式碼更易讀。

from enum import Enum, auto

class UserState(Enum):
    """定義使用者的多步驟操作狀態"""
    IDLE = auto()                           # 閒置，無任何待處理操作

    # --- 推播流程 ---
    AWAITING_BROADCAST_MESSAGE = auto()     # 等待使用者發送或回覆要推播的訊息

    # --- 推播組合管理流程 ---
    AWAITING_SET_NAME = auto()              # 等待使用者輸入組合名稱
    SELECTING_GROUPS_FOR_SET = auto()       # 使用者正在編輯器中選擇群組
