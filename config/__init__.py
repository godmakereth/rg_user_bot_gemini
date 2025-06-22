# 檔案：config/__init__.py
# 職責：讀取 .env 並提供全域設定，增加更精確的錯誤檢查。

import os
from dotenv import load_dotenv

# 讀取位於專案根目錄的 .env 檔案
load_dotenv()

# --- Helper function for robust checking ---
def get_env_var(var_name, is_int=False, is_list=False, is_int_list=False):
    """
    一個更健壯的函式，用來獲取、轉換和檢查環境變數。
    """
    value = os.environ.get(var_name)
    if not value:
        # 如果變數不存在或為空，直接拋出錯誤
        raise ValueError(f"缺少必要的環境變數：請在 .env 檔案中設定 '{var_name}'。")
    
    try:
        if is_int:
            return int(value)
        if is_list:
            return [item.strip() for item in value.split(',') if item.strip()]
        if is_int_list:
            return [int(item.strip()) for item in value.split(',') if item.strip()]
        return value
    except (ValueError, TypeError) as e:
        raise ValueError(f"環境變數 '{var_name}' 的格式不正確。請檢查 .env 檔案。") from e

# --- 讀取所有設定 ---
try:
    # --- Telegram API & User Account ---
    API_ID = get_env_var("API_ID", is_int=True)
    API_HASH = get_env_var("API_HASH")

    # --- User Session ---
    PHONE_NUMBER = os.environ.get("PHONE_NUMBER") # 這個可以為空
    PASSWORD = os.environ.get("PASSWORD")         # 這個也可以為空

    # --- App Configuration ---
    CONTROL_GROUP = get_env_var("CONTROL_GROUP", is_int=True)
    ADMIN_USERS = get_env_var("ADMIN_USERS", is_int_list=True)
    TARGET_CHANNELS_STR = get_env_var("TARGET_CHANNELS", is_list=True)

except ValueError as e:
    # 重新拋出我們自訂的、更清晰的錯誤訊息
    raise e

# --- 再次確認列表不為空 ---
if not ADMIN_USERS:
    raise ValueError("環境變數 'ADMIN_USERS' 不能为空，請至少設定一個 User ID。")
if not TARGET_CHANNELS_STR:
    raise ValueError("環境變數 'TARGET_CHANNELS' 不能为空，請至少設定一個目標群組。")

# --- 全域指令設定 ---
COMMAND_PREFIX = "."
