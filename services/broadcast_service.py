# 檔案：services/broadcast_service.py
# 職責：業務邏輯，執行推播、轉發的核心功能。

import asyncio
import logging
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserIsBlocked, PeerIdInvalid

async def broadcast_to_targets(
    client: Client, 
    target_channels: list, 
    message_to_broadcast: Message
) -> tuple[int, int]:
    """
    將一則訊息推播到指定的目標頻道列表。
    使用 message.copy() 能夠處理絕大多數訊息類型。
    返回 (成功數量, 失敗數量)。
    """
    success_count, failed_count = 0, 0
    
    for channel_id in target_channels:
        try:
            # Pyrogram 內部會處理 @username 和 int ID
            chat_id = int(channel_id) if str(channel_id).startswith('-') else channel_id
            
            await message_to_broadcast.copy(chat_id)

            success_count += 1
            logging.info(f"成功推播到 {chat_id}")
            
        except FloodWait as e:
            logging.warning(f"推播到 {channel_id} 時遭遇洪水限制，將等待 {e.value} 秒。")
            await asyncio.sleep(e.value)
            # 重試一次
            try:
                await message_to_broadcast.copy(chat_id)
                success_count += 1
            except Exception as retry_e:
                failed_count += 1
                logging.error(f"重試推播到 {channel_id} 仍然失敗: {retry_e}")
        
        except (UserIsBlocked, PeerIdInvalid) as e:
            failed_count += 1
            logging.error(f"推播到 {channel_id} 失敗，可能是被封鎖或ID無效: {e}")

        except Exception as e:
            failed_count += 1
            logging.error(f"推播到 {channel_id} 時發生未知錯誤: {e}")
            
        finally:
            # 在每次發送後都短暫延遲，以避免因發送過快而被 Telegram 限制
            await asyncio.sleep(1.5)
            
    return success_count, failed_count
