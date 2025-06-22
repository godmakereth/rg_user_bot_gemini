# 檔案：main.py
# 職責：專案主入口，組裝所有模組並啟動。

import asyncio
import logging
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import PeerIdInvalid

import config
from data.data_manager import DataManager
from handlers.message_handler import MessageHandler
from handlers.callback_handler import CallbackHandler
import services.info_service as info_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
user_states = {} 

async def main():
    log.info("初始化 Pyrogram 客戶端...")
    async with Client(
        "user_session",
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        phone_number=config.PHONE_NUMBER,
        password=config.PASSWORD
    ) as client:
        log.info("初始化資料管理器...")
        data_manager = DataManager()
        log.info("註冊事件處理器...")
        MessageHandler(client, user_states, data_manager)
        CallbackHandler(client, user_states, data_manager)

        try:
            me = await client.get_me()
            log.info(f"成功登入帳戶: {me.first_name} (ID: {me.id})")
            log.info("啟動時掃描群組...")
            dialogs = await info_service.scan_all_dialogs(client)
            
            log_message = f"啟動時掃描完成，找到 {len(dialogs)} 個群組/頻道。"
            # [修正] 使用新的日誌格式
            data_manager.add_log(action='startup_scan', status='INFO', message=log_message, user="System")
            
            scan_results_text = "📡 **啟動時群組偵測報告**\n\n"
            if dialogs:
                report_lines = [f"• **{d['title']}**\n  `{d['id']}` ({d['type']})" for d in dialogs]
                scan_results_text += "\n".join(report_lines)
            else:
                scan_results_text += "未在您的帳號中發現任何超級群組或頻道。"

            if len(scan_results_text) > 4096:
                scan_results_text = scan_results_text[:4090] + "\n...報告過長，已被截斷"

            try:
                await client.send_message(
                    config.CONTROL_GROUP,
                    f"✅ **RG 自動推播 Userbot 已成功啟動！**\n請發送 `{config.COMMAND_PREFIX}start` 來顯示主選單。",
                    parse_mode=ParseMode.MARKDOWN
                )
                await client.send_message(
                    config.CONTROL_GROUP,
                    scan_results_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            except PeerIdInvalid:
                log.error("="*60)
                log.error("！！！啟動警告：指定的 CONTROL_GROUP ID 不正確或無法訪問！")
                log.error(f"目前設定的錯誤 ID: {config.CONTROL_GROUP}")
                log.error("★ 好消息：已將您所有的群組列表發送到您的「已存訊息 (Saved Messages)」中。")
                log.error("\n請依照以下步驟修正：")
                log.error("1. 打開您的 Telegram，找到「已存訊息 (Saved Messages)」。")
                log.error("2. 從該列表中找到您想設為「控制群組」的群組，並複製其 -100 開頭的 ID。")
                log.error("3. 將此 ID 更新到您的 .env 檔案的 CONTROL_GROUP 欄位中。")
                log.error("4. 重啟程式。")
                log.error("="*60)
                try:
                    await client.send_message("me", scan_results_text, parse_mode=ParseMode.MARKDOWN)
                    log.info("已成功將群組列表發送到您的「已存訊息」。")
                except Exception as send_to_me_error:
                    log.error(f"發送群組列表到「已存訊息」時失敗: {send_to_me_error}")
            
            log.info("Userbot 已啟動並待命中... (按 Ctrl+C 停止)")
            await asyncio.Future()
        except Exception as e:
            log.error(f"運行過程中發生嚴重錯誤: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("程式被手動中斷。")
