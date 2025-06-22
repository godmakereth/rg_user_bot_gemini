# 檔案：data/data_manager.py
# 職責：資料庫核心 (Model)，所有JSON檔案的讀寫都由它負責。

import json
import logging
from datetime import datetime
from threading import Lock

class DataManager:
    """負責所有 data.json 的讀寫操作，確保多執行緒安全。"""

    def __init__(self, db_path: str = 'data.json'):
        self.db_path = db_path
        self.lock = Lock()
        self.data = self._load()

    def _load(self) -> dict:
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logging.warning(f"無法讀取 {self.db_path}，將建立新的資料檔案。")
            return {'schedules': [], 'drafts': [], 'logs': [], 'broadcast_sets': []}

    def _save(self):
        with self.lock:
            try:
                with open(self.db_path, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                logging.error(f"寫入資料到 {self.db_path} 失敗: {e}")

    def _get_next_id(self, key: str) -> int:
        if not self.data.get(key):
            return 1
        return max((item.get('id', 0) for item in self.data[key]), default=0) + 1

    # --- Log Management (日誌管理) ---
    def add_log(self, action: str, status: str, message: str, user: str = "System"):
        """
        新增一筆結構化的日誌。
        :param action: 操作類型 (e.g., 'broadcast', 'command_start')
        :param status: 操作狀態 ('SUCCESS', 'FAILURE', 'INFO', 'PARTIAL_SUCCESS')
        :param message: 日誌的詳細訊息
        :param user: 操作者名稱
        """
        log_entry = {
            'time': datetime.now().isoformat(),
            'action': action,
            'status': status,
            'message': message,
            'user': user
        }
        self.data.get('logs', []).append(log_entry)
        self._save()
        logging.info(f"Log [{status}] added: {action} - {message}")

    def get_logs(self) -> list:
        """獲取所有日誌記錄。"""
        return self.data.get('logs', [])

    # --- Broadcast Set Management (推播組合管理) ---
    def get_broadcast_sets(self):
        return self.data.get('broadcast_sets', [])

    def get_broadcast_set_by_id(self, set_id: int):
        for s in self.data.get('broadcast_sets', []):
            if s.get('id') == set_id:
                return s
        return None

    def save_broadcast_set(self, set_name: str, channel_ids: list, set_id: int = None):
        sets = self.data.get('broadcast_sets', [])
        if set_id is None:
            new_id = self._get_next_id('broadcast_sets')
            sets.append({'id': new_id, 'name': set_name, 'channels': channel_ids})
        else:
            for s in sets:
                if s.get('id') == set_id:
                    s['name'], s['channels'] = set_name, channel_ids
                    break
        self._save()

    def delete_broadcast_set(self, set_id: int):
        sets = self.data.get('broadcast_sets', [])
        self.data['broadcast_sets'] = [s for s in sets if s.get('id') != set_id]
        self._save()
