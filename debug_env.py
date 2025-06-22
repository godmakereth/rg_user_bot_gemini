# 檔案：debug_env.py (進階版)
# 職責：使用更可靠的方法來定位並讀取 .env 檔案。

import os
import pathlib

# 嘗試載入 dotenv，如果沒有安裝也沒關係，我們先手動檢查
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("警告：未安裝 python-dotenv 套件。請執行 pip install python-dotenv")

print("--- 進階 .env 檔案偵錯腳本 ---")

# 使用腳本自身位置來構建 .env 的絕對路徑 (這是最可靠的方法)
print("\n[偵錯步驟：嘗試手動定位 .env 檔案]")
try:
    # __file__ 是目前腳本 (debug_env.py) 的完整路徑
    # pathlib.Path(__file__) 將其轉換為路徑物件
    # .parent 獲取包含此腳本的資料夾路徑 (即 D:\rg_user_bot\)
    # / ".env" 將 ".env" 檔案名附加到資料夾路徑後
    script_dir = pathlib.Path(__file__).parent
    manual_env_path = script_dir / ".env"

    print(f"根據腳本位置，預期的 .env 檔案絕對路徑是: {manual_env_path}")

    # 檢查這個我們手動算出來的路徑，檔案是否存在
    if manual_env_path.exists() and manual_env_path.is_file():
        print(f"✅ 成功！檔案系統確認 '{manual_env_path}' 存在。")
        
        if DOTENV_AVAILABLE:
            # 直接載入這個找到的檔案路徑
            load_dotenv(dotenv_path=manual_env_path)
            
            # 再次檢查變數是否已讀入
            api_id = os.environ.get("API_ID")
            api_hash = os.environ.get("API_HASH")

            print("\n讀取到的環境變數：")
            print(f"API_ID: {api_id} (類型: {type(api_id)})")
            print(f"API_HASH: {api_hash} (類型: {type(api_hash)})")

            if api_id and api_hash:
                print("\n✅✅✅ 最終成功！環境變數已從手動定位的路徑成功讀取。")
                print("這表示您的主程式 (main.py) 可能需要用類似的方式來更明確地載入 .env 檔案。")
            else:
                print("\n❌ 錯誤：檔案存在，但讀取變數失敗。")
                print("請檢查 .env 檔案內容，確保格式為 KEY=VALUE，且沒有包含非預期的特殊字元。")
    else:
        print(f"❌ 嚴重錯誤：檔案系統回報 '{manual_env_path}' 不存在或不是一個檔案。")
        print("這是一個非常奇怪的情況，請確認檔案沒有被設為隱藏或有特殊的權限問題。")

except Exception as e:
    print(f"在手動定位過程中發生錯誤: {e}")


print("\n--- 偵錯結束 ---")
