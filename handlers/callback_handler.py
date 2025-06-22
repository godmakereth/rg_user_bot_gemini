# 檔案：handlers/callback_handler.py
# 職責：控制器(Controller)，處理所有按鈕點擊事件。

import logging
from pyrogram import Client, filters
from pyrogram.handlers import CallbackQueryHandler as PyrogramCallbackQueryHandler
from pyrogram.enums import ParseMode
from pyrogram.types import CallbackQuery
from pyrogram.errors import MessageNotModified
import config
from .states import UserState
from data.data_manager import DataManager
import services.info_service as info_service
import ui.panels as panels

class CallbackHandler:
    def __init__(self, client: Client, user_states: dict, data_manager: DataManager):
        self.client = client
        self.user_states = user_states
        self.data_manager = data_manager
        client.add_handler(
            PyrogramCallbackQueryHandler(
                self.handle_callback,
                filters=filters.user(config.ADMIN_USERS)
            )
        )

    async def handle_callback(self, client: Client, query: CallbackQuery):
        user_id = query.from_user.id
        data = query.data
        parts = data.split(':')
        action = parts[0]
        
        try:
            if action == "back":
                await self.handle_back_navigation(query, parts[1])
            elif action == "main":
                await self.handle_main_menu(query, parts[1])
            elif action == "broadcast":
                await self.handle_broadcast_flow(query, parts)
            elif action == "groups":
                await self.handle_group_management(query, parts[1])
            elif action == "set":
                await self.handle_set_management(query, parts)
            elif action == "scan":
                 await self.handle_scan_flow(query, parts)
        except Exception as e:
            logging.error(f"處理回調時發生錯誤 ({data}): {e}", exc_info=True)
            await query.answer(f"處理時發生錯誤: {type(e).__name__}", show_alert=True)

        try:
            await query.answer()
        except Exception: pass

    async def handle_back_navigation(self, query: CallbackQuery, target: str):
        if target == "main":
            stats = await info_service.get_system_stats(self.data_manager)
            await query.message.edit_text(**panels.create_main_panel(stats))
        elif target == "groups":
            await query.message.edit_text(**panels.create_group_management_panel())
        elif target == "manage_sets":
            sets = self.data_manager.get_broadcast_sets()
            await query.message.edit_text(**panels.create_broadcast_set_management_panel(sets))

    async def handle_main_menu(self, query: CallbackQuery, command: str):
        if command == "broadcast":
            sets = self.data_manager.get_broadcast_sets()
            await query.message.edit_text(**panels.create_broadcast_target_panel(sets))
        elif command == "groups":
            await query.message.edit_text(**panels.create_group_management_panel())
        else:
            await query.answer(f"功能「{command}」尚未開放。", show_alert=True)

    async def handle_broadcast_flow(self, query: CallbackQuery, parts: list):
        user_id = query.from_user.id
        target_type = parts[1]
        state = {'state': UserState.AWAITING_BROADCAST_MESSAGE}
        
        if target_type == 'target' and parts[2] == 'all':
            state.update({'target_type': 'all'})
            await query.message.edit_text("✅ **目標：所有群組**\n\n請直接發送或回覆您要推播的訊息。", parse_mode=ParseMode.MARKDOWN)
        elif target_type == 'target_set':
            set_id = int(parts[2])
            state.update({'target_type': 'set', 'target_id': set_id})
            set_info = self.data_manager.get_broadcast_set_by_id(set_id)
            if set_info:
                await query.message.edit_text(f"✅ **目標：組合「{set_info['name']}」**\n\n請直接發送或回覆您要推播的訊息。", parse_mode=ParseMode.MARKDOWN)
            else:
                await query.answer("❌ 找不到此組合。", show_alert=True)
                return
        self.user_states[user_id] = state

    async def handle_group_management(self, query: CallbackQuery, command: str):
        if command == "manage_sets":
            sets = self.data_manager.get_broadcast_sets()
            await query.message.edit_text(**panels.create_broadcast_set_management_panel(sets))
        elif command == "test_all":
            await query.answer("正在測試所有目標群組連線...", show_alert=False)
            all_channels = await info_service.get_all_channel_details(self.client, config.TARGET_CHANNELS_STR)
            results = [f"• {ch['title']}: {ch['members_count']} 人" for ch in all_channels]
            text = f"👥 **群組連線測試結果 ({len(all_channels)}個):**\n\n" + "\n".join(results)
            await query.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        elif command == "scan_all":
            await query.message.edit_text("📡 正在掃描您帳號中的所有群組與頻道，請稍候...")
            dialogs = await info_service.scan_all_dialogs(self.client)
            
            # --- 【新邏輯】將掃描操作寫入日誌 ---
            log_message = f"掃描完成，找到 {len(dialogs)} 個群組/頻道。"
            self.data_manager.add_log(
                action='scan_groups',
                message=log_message,
                user=query.from_user.first_name
            )
            
            # 將結果存儲在狀態中以便翻頁
            self.user_states[query.from_user.id] = {'scanned_dialogs': dialogs}
            await query.message.edit_text(**panels.create_scan_results_panel(dialogs))
    
    async def handle_scan_flow(self, query: CallbackQuery, parts: list):
        """處理群組掃描結果的翻頁。"""
        command = parts[1]
        if command == "page":
            page = int(parts[2])
            dialogs = self.user_states.get(query.from_user.id, {}).get('scanned_dialogs', [])
            if not dialogs:
                return await query.answer("掃描結果已過期，請重新掃描。", show_alert=True)
            
            await query.message.edit_text(**panels.create_scan_results_panel(dialogs, page=page))

    async def handle_set_management(self, query: CallbackQuery, parts: list):
        user_id = query.from_user.id
        command = parts[1]
        set_id = int(parts[2]) if len(parts) > 2 else 0

        if command in ["add", "view"]:
            if command == "add":
                state = {'state': UserState.AWAITING_SET_NAME, 'set_id': 0, 'message_id': query.message.message_id, 'selected_channels': []}
                self.user_states[user_id] = state
                await query.message.edit_text("📝 請輸入新組合的名稱：(可隨時用 .cancel 取消)")
            else: # view
                b_set = self.data_manager.get_broadcast_set_by_id(set_id)
                if not b_set: return await query.answer("❌ 找不到此組合。", show_alert=True)
                self.user_states[user_id] = {'state': UserState.SELECTING_GROUPS_FOR_SET, 'set_id': set_id, 'set_name': b_set['name'], 'message_id': query.message.message_id, 'selected_channels': b_set.get('channels', [])}
                all_channels = await info_service.get_all_channel_details(self.client, config.TARGET_CHANNELS_STR)
                await query.message.edit_text(**panels.create_broadcast_set_editor_panel(set_id, b_set['name'], all_channels, b_set.get('channels', [])))
        
        elif command in ["edit_toggle", "edit_all", "edit_none"]:
            state_data = self.user_states.get(user_id)
            if not (state_data and state_data.get('state') == UserState.SELECTING_GROUPS_FOR_SET): return
            
            if command == "edit_toggle":
                channel_id = int(parts[3])
                if channel_id in state_data['selected_channels']: state_data['selected_channels'].remove(channel_id)
                else: state_data['selected_channels'].append(channel_id)
            else:
                all_channels_details = await info_service.get_all_channel_details(self.client, config.TARGET_CHANNELS_STR)
                all_channel_ids = [int(c['id']) for c in all_channels_details if isinstance(c['id'], int) or (isinstance(c['id'], str) and c['id'].lstrip('-').isdigit())]
                state_data['selected_channels'] = all_channel_ids if command == "edit_all" else []

            all_channels = await info_service.get_all_channel_details(self.client, config.TARGET_CHANNELS_STR)
            try:
                await query.message.edit_text(**panels.create_broadcast_set_editor_panel(set_id, state_data['set_name'], all_channels, state_data['selected_channels']))
            except MessageNotModified: pass

        elif command == "save":
            state_data = self.user_states.get(user_id)
            if state_data and state_data.get('state') == UserState.SELECTING_GROUPS_FOR_SET:
                self.data_manager.save_broadcast_set(state_data['set_name'], state_data['selected_channels'], set_id if set_id != 0 else None)
                self.user_states[user_id] = {'state': UserState.IDLE}
                sets = self.data_manager.get_broadcast_sets()
                await query.message.edit_text(**panels.create_broadcast_set_management_panel(sets))
                await query.answer("💾 組合已儲存！", show_alert=True)
        
        elif command == "delete_confirm":
            b_set = self.data_manager.get_broadcast_set_by_id(set_id)
            if b_set: await query.message.edit_text(**panels.create_delete_confirmation_panel(set_id, b_set['name']))

        elif command == "delete_execute":
            self.data_manager.delete_broadcast_set(set_id)
            self.user_states[user_id] = {'state': UserState.IDLE}
            sets = self.data_manager.get_broadcast_sets()
            await query.message.edit_text(**panels.create_broadcast_set_management_panel(sets))
            await query.answer("🗑️ 組合已刪除！", show_alert=True)
