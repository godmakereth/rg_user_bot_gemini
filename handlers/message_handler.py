# 檔案：handlers/message_handler.py
# 職責：控制器(Controller)，處理所有文字訊息和指令，增加詳細日誌並修正按鍵顯示問題。

import logging
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler as PyrogramMessageHandler
from pyrogram.enums import ParseMode
from pyrogram.types import Message
import config
from .states import UserState
from data.data_manager import DataManager
import services.info_service as info_service
import services.broadcast_service as broadcast_service
import ui.panels as panels

class MessageHandler:
    def __init__(self, client: Client, user_states: dict, data_manager: DataManager):
        self.client = client
        self.user_states = user_states
        self.data_manager = data_manager
        
        # 正式、安全的過濾器，只監聽來自控制群組和管理員的訊息
        client.add_handler(
            PyrogramMessageHandler(
                self.handle_message,
                filters=filters.text & filters.chat(config.CONTROL_GROUP) & filters.user(config.ADMIN_USERS)
            )
        )
        logging.info("MessageHandler 已啟動，正在指定的控制群組中監聽管理員指令。")

    async def handle_message(self, client: Client, message: Message):
        """主訊息處理邏輯中心"""
        user_id = message.from_user.id
        state_data = self.user_states.get(user_id, {'state': UserState.IDLE})
        current_state = state_data.get('state')

        if message.text.startswith(config.COMMAND_PREFIX):
            command = message.text.split(' ')[0].lower().removeprefix(config.COMMAND_PREFIX)
            if await self.handle_command(command, message):
                return

        if current_state != UserState.IDLE:
            if current_state == UserState.AWAITING_BROADCAST_MESSAGE:
                await self.process_broadcast_message(user_id, message)
            elif current_state == UserState.AWAITING_SET_NAME:
                await self.process_set_name(user_id, message)
        
    async def handle_command(self, command: str, message: Message) -> bool:
        """處理文字指令，如果成功處理則返回 True"""
        user_id = message.from_user.id
        user_name = message.from_user.first_name
        
        if command == "start":
            self.user_states[user_id] = {'state': UserState.IDLE}
            
            logging.info("偵錯：正在為 .start 指令生成主面板...")
            stats = await info_service.get_system_stats(self.data_manager)
            panel_data = panels.create_main_panel(stats)
            
            try:
                # --- 【最終修正】移除 reply_to_message_id，改為直接發送新訊息 ---
                await self.client.send_message(
                    chat_id=message.chat.id,
                    text=panel_data['text'],
                    reply_markup=panel_data['reply_markup'],
                    parse_mode=panel_data.get('parse_mode')
                )
                logging.info("偵錯：已使用 client.send_message (非回覆模式) 成功發送主面板。")
                self.data_manager.add_log('command', 'SUCCESS', f"執行指令: .{command}", user_name)
            except Exception as e:
                logging.error(f"偵錯：在發送主面板時發生錯誤: {e}", exc_info=True)
                self.data_manager.add_log('command_start', 'FAILURE', f"顯示主面板時發生錯誤: {e}", user_name)

            return True

        elif command == "cancel":
            if self.user_states.get(user_id, {}).get('state') != UserState.IDLE:
                self.user_states[user_id] = {'state': UserState.IDLE}
                await message.reply_text("✅ 操作已取消。")
                self.data_manager.add_log('command', 'SUCCESS', f"執行指令: .{command}", user_name)
            return True
        elif command == "id":
            text = f"👤 **您的 User ID:** `{user_id}`\n💬 **此群組 Chat ID:** `{message.chat.id}`"
            if message.reply_to_message:
                replied_user = message.reply_to_message.from_user
                text += f"\n\n👤 **被回覆者 User ID:** `{replied_user.id}`"
            await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            self.data_manager.add_log('command', 'SUCCESS', f"執行指令: .{command}", user_name)
            return True
            
        self.data_manager.add_log('command', 'FAILURE', f"未知指令: .{command}", user_name)
        return False

    async def process_broadcast_message(self, user_id: int, message: Message):
        state_data = self.user_states.get(user_id, {})
        user_name = message.from_user.first_name
        target_type = state_data.get('target_type')
        target_channels, target_name = [], ""

        if target_type == 'all':
            target_channels, target_name = config.TARGET_CHANNELS_STR, "所有群組"
        elif target_type == 'set':
            set_id = state_data.get('target_id')
            b_set = self.data_manager.get_broadcast_set_by_id(set_id)
            if b_set:
                target_channels, target_name = b_set['channels'], f"組合「{b_set['name']}」"

        if not target_channels:
            err_msg = "錯誤：找不到推播目標。"
            await message.reply_text(f"❌ {err_msg}")
            self.data_manager.add_log('broadcast', 'FAILURE', err_msg, user_name)
        else:
            status_msg = await message.reply_text(f"🚀 **開始推播...**\n目標: {target_name} ({len(target_channels)}個)")
            msg_to_bcast = message.reply_to_message or message
            success, failed = await broadcast_service.broadcast_to_targets(self.client, target_channels, msg_to_bcast)
            result_text = f"✅ **推播完成！**\n\n- **目標**: {target_name}\n- **成功**: {success} 個\n- **失敗**: {failed} 個"
            await status_msg.edit_text(result_text)
            
            log_msg_content = msg_to_bcast.text[:50] + '...' if msg_to_bcast.text and len(msg_to_bcast.text) > 50 else msg_to_bcast.text or f"媒體訊息 ({msg_to_bcast.media})"
            log_status = 'SUCCESS' if failed == 0 else 'PARTIAL_SUCCESS' if success > 0 else 'FAILURE'
            log_msg_detail = f"推播到「{target_name}」。結果: 成功 {success}, 失敗 {failed}。內容: {log_msg_content}"
            self.data_manager.add_log('broadcast', log_status, log_msg_detail, user_name)
        
        self.user_states[user_id] = {'state': UserState.IDLE}

    async def process_set_name(self, user_id: int, message: Message):
        state_data = self.user_states.get(user_id, {})
        set_id = state_data.get('set_id', 0)
        state_data.update({'state': UserState.SELECTING_GROUPS_FOR_SET, 'set_name': message.text})
        self.data_manager.add_log('manage_set', 'INFO', f"使用者開始為組合命名: {message.text}", message.from_user.first_name)
        all_channels = await info_service.get_all_channel_details(self.client, config.TARGET_CHANNELS_STR)
        panel_data = panels.create_broadcast_set_editor_panel(set_id, message.text, all_channels, state_data.get('selected_channels', []))
        await self.client.edit_message_text(chat_id=config.CONTROL_GROUP, message_id=state_data['message_id'], **panel_data)
