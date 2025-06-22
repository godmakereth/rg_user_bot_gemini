# 檔案：ui/panels.py
# 職責：介面產生器 (View)，專門生成使用者看到的文字介面與按鈕。

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# [修正] 導入 ParseMode Enum
from pyrogram.enums import ParseMode
import config

# --- Helper ---
def create_back_button(callback_data: str) -> InlineKeyboardButton:
    """創建一個標準的返回按鈕"""
    return InlineKeyboardButton("🔙 返回", callback_data=callback_data)

# --- 主選單 & 導航 ---
def create_main_panel(stats: dict) -> dict:
    text = f"""🤖 **RG 自動推播 Userbot**

📊 **系統資訊:**
- 推播組合: {stats.get('set_count', 0)} 組
- 目標群組: {stats.get('total_target_count', 0)} 個
- 24H內推播: {stats.get('today_broadcasts', 0)} 次

💡 使用 `{config.COMMAND_PREFIX}start` 可刷新此面板。"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 立即推播", callback_data="main:broadcast")],
        [InlineKeyboardButton("⏰ 時間管理", callback_data="main:schedule"), InlineKeyboardButton("📝 草稿管理", callback_data="main:drafts")],
        [InlineKeyboardButton("👥 群組管理", callback_data="main:groups"), InlineKeyboardButton("📊 推播記錄", callback_data="main:logs_all")]])
    # [修正] 使用 ParseMode.MARKDOWN
    return {'text': text, 'reply_markup': keyboard, 'parse_mode': ParseMode.MARKDOWN}

# --- 推播流程 ---
def create_broadcast_target_panel(sets: list) -> dict:
    text = "請選擇本次的推播目標："
    buttons = [[InlineKeyboardButton("📢 所有群組", callback_data="broadcast:target:all")]]
    buttons.extend([[InlineKeyboardButton(f"🎯 {s['name']} ({len(s['channels'])}個)", callback_data=f"broadcast:target_set:{s['id']}")] for s in sets])
    buttons.append([create_back_button("back:main")])
    return {'text': text, 'reply_markup': InlineKeyboardMarkup(buttons)}

# --- 群組管理 ---
def create_group_management_panel() -> dict:
    text = "管理您的推播組合或進行群組測試。"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 推播組合管理", callback_data="groups:manage_sets")],
        [InlineKeyboardButton("🔗 測試群組連線", callback_data="groups:test_all")],
        [create_back_button("back:main")]])
    return {'text': text, 'reply_markup': keyboard}

def create_broadcast_set_management_panel(sets: list) -> dict:
    text = "管理您的推播組合。\n點擊組合可進行編輯。"
    buttons = [[InlineKeyboardButton(f"⚙️ {s['name']} ({len(s['channels'])}個)", callback_data=f"set:view:{s['id']}")] for s in sets]
    buttons.append([InlineKeyboardButton("➕ 新增組合", callback_data="set:add:0")])
    buttons.append([create_back_button("back:groups")])
    return {'text': text, 'reply_markup': InlineKeyboardMarkup(buttons)}

def create_broadcast_set_editor_panel(set_id: int, set_name: str, all_channels: list, selected_channels: list) -> dict:
    text = f"正在編輯組合: **{set_name}**\n已選 {len(selected_channels)} / {len(all_channels)} 個群組。"
    buttons = []
    row = []
    for ch in all_channels:
        ch_id = int(ch['id']) if isinstance(ch['id'], str) and ch['id'].lstrip('-').isdigit() else ch['id']
        prefix = "✅" if ch_id in selected_channels else "⬜️"
        button = InlineKeyboardButton(f"{prefix} {ch['title'][:20]}", callback_data=f"set:edit_toggle:{set_id}:{ch_id}")
        row.append(button)
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    
    buttons.extend([
        [InlineKeyboardButton("✅ 全選", callback_data=f"set:edit_all:{set_id}"), InlineKeyboardButton("⬜️ 清空", callback_data=f"set:edit_none:{set_id}")],
        [InlineKeyboardButton(f"💾 儲存組合 ({len(selected_channels)}個)", callback_data=f"set:save:{set_id}")],
    ])
    if set_id != 0:
        buttons.append([InlineKeyboardButton("🗑️ 刪除此組合", callback_data=f"set:delete_confirm:{set_id}")])
    buttons.append([create_back_button("back:manage_sets")])
    # [修正] 使用 ParseMode.MARKDOWN
    return {'text': text, 'reply_markup': InlineKeyboardMarkup(buttons), 'parse_mode': ParseMode.MARKDOWN}

def create_delete_confirmation_panel(set_id: int, set_name: str) -> dict:
    text = f"⚠️ **您確定要刪除「{set_name}」這個組合嗎？\n此操作無法復原。**"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❗️ 確認刪除", callback_data=f"set:delete_execute:{set_id}")],
        [create_back_button(f"set:view:{set_id}")]])
    # [修正] 使用 ParseMode.MARKDOWN
    return {'text': text, 'reply_markup': keyboard, 'parse_mode': ParseMode.MARKDOWN}
