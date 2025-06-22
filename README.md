# RG User Bot Gemini

## 專案簡介
本專案是一個基於 Pyrogram 的 Telegram Userbot，支援自動推播、群組/頻道掃描、事件日誌記錄等功能，適合自動化管理 Telegram 帳號。

## 主要功能
- 啟動時自動掃描所有群組與頻道
- 支援自動推播訊息
- 事件日誌記錄
- 控制群組互動

## 安裝與啟動
1. 下載本專案原始碼：
   ```bash
   git clone https://github.com/godmakereth/rg_user_bot_gemini.git
   cd rg_user_bot_gemini
   ```
2. 安裝相依套件：
   ```bash
   pip install -r requirements.txt
   ```
3. 設定 `.env` 檔案，填入你的 Telegram API 資訊與控制群組 ID。
4. 啟動 Userbot：
   ```bash
   python main.py
   ```

## 主要檔案說明
- `main.py`：專案主入口，負責組裝模組與啟動流程
- `config/`：設定相關模組
- `data/`：資料管理
- `handlers/`：訊息與回呼事件處理
- `services/`：推播與資訊服務
- `ui/`：互動面板

## 聯絡方式
如有問題或建議，歡迎透過 [GitHub Issues](https://github.com/godmakereth/rg_user_bot_gemini/issues) 聯絡作者。 