# 檔案：services/info_service.py
# 職責：業務邏輯，獲取統計數據、群組資訊、掃描群組等。

import logging
from datetime import datetime, timedelta
from pyrogram import Client
from pyrogram.enums import ChatType
from data.data_manager import DataManager
import config

async def get_system_stats(data_manager: DataManager) -> dict:
    """獲取用於主面板顯示的系統統計數據。"""
    sets = data_manager.get_broadcast_sets()
    now = datetime.now()
    time_24_hours_ago = now - timedelta(hours=24)
    
    logs_24h = [
        log for log in data_manager.get_logs() 
        if datetime.fromisoformat(log['time']) > time_24_hours_ago
    ]
    
    return {
        "set_count": len(sets),
        "total_target_count": len(config.TARGET_CHANNELS_STR),
        "today_broadcasts": len(logs_24h)
    }

async def get_all_channel_details(client: Client, channel_ids: list) -> list:
    """獲取所有目標頻道的詳細資訊 (ID, 名稱, 人數)。"""
    details = []
    for channel_id_str in channel_ids:
        try:
            chat_id = int(channel_id_str) if channel_id_str.startswith('-') else channel_id_str
            chat = await client.get_chat(chat_id)
            details.append({
                "id": chat.id,
                "title": chat.title or "無標題",
                "members_count": getattr(chat, 'members_count', 'N/A')
            })
        except Exception as e:
            logging.error(f"無法獲取頻道 {channel_id_str} 的資訊: {e}")
            details.append({
                "id": channel_id_str,
                "title": f"錯誤 ({channel_id_str})",
                "members_count": "無法訪問"
            })
    return details

# --- 【新功能】---
async def scan_all_dialogs(client: Client) -> list:
    """
    掃描您帳號中所有的對話，並篩選出群組和頻道。
    返回一個包含詳細資訊的列表。
    """
    scanned_groups = []
    async for dialog in client.get_dialogs():
        # 我們只關心超級群組和頻道
        if dialog.chat.type in [ChatType.SUPERGROUP, ChatType.CHANNEL]:
            scanned_groups.append({
                "id": dialog.chat.id,
                "title": dialog.chat.title or "無標題",
                "type": "超級群組" if dialog.chat.type == ChatType.SUPERGROUP else "頻道"
            })
    logging.info(f"掃描完成，共找到 {len(scanned_groups)} 個群組/頻道。")
    return scanned_groups
