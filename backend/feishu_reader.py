"""
飞书多维表格读取模块
用于从飞书多维表格中读取用户数据
支持 tenant_access_token 自动刷新
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from config import settings

logger = logging.getLogger(__name__)


class FeishuBitableClient:
    """飞书多维表格客户端，支持 token 自动刷新"""
    
    def __init__(self, app_id: str, app_secret: str, app_token: str, table_id: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.app_token = app_token
        self.table_id = table_id
        self.tenant_access_token: Optional[str] = None
        self.token_expire_time: Optional[datetime] = None
        self.refresh_threshold = settings.FEISHU_TOKEN_REFRESH_THRESHOLD
    
    def _get_new_tenant_token(self) -> str:
        """调用接口获取新的 tenant_access_token"""
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") != 0:
                raise Exception(f"获取token失败: {data.get('msg')} (错误码: {data.get('code')})")
            
            self.tenant_access_token = data.get("tenant_access_token")
            expire_seconds = data.get("expire", 7200)  # 默认2小时有效期
            self.token_expire_time = datetime.now() + timedelta(seconds=expire_seconds)
            logger.info(f"✅ 成功获取新token，有效期至: {self.token_expire_time.strftime('%Y-%m-%d %H:%M:%S')}")
            return self.tenant_access_token
        
        except Exception as e:
            logger.error(f"❌ 获取token失败: {str(e)}")
            raise
    
    def get_token(self) -> str:
        """获取有效的 tenant_access_token（自动刷新）"""
        if (not self.tenant_access_token or not self.token_expire_time or
            datetime.now() >= self.token_expire_time - timedelta(seconds=self.refresh_threshold)):
            return self._get_new_tenant_token()
        return self.tenant_access_token
    
    def read_table_records(self, page_size: int = 100) -> List[Dict]:
        """读取多维表格所有记录（自动处理 token 刷新）"""
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.app_token}/tables/{self.table_id}/records"
        all_records = []
        page_token = None
        
        while True:
            headers = {"Authorization": f"Bearer {self.get_token()}"}
            params = {"page_size": page_size}
            if page_token:
                params["page_token"] = page_token
            
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") != 0:
                    raise Exception(f"读取表格失败: {data.get('msg')} (错误码: {data.get('code')})")
                
                records = data.get("data", {}).get("items", [])
                all_records.extend(records)
                logger.info(f"📄 已读取 {len(all_records)} 条记录（当前页: {len(records)}）")
                
                if not data.get("data", {}).get("has_more", False):
                    break
                page_token = data.get("data", {}).get("page_token")
                
            except Exception as e:
                logger.error(f"❌ 读取表格失败: {str(e)}")
                raise
        
        return all_records


# 全局客户端实例（单例模式，复用 token）
_feishu_client: Optional[FeishuBitableClient] = None


def get_feishu_client() -> FeishuBitableClient:
    """获取飞书客户端实例（单例）"""
    global _feishu_client
    if _feishu_client is None:
        _feishu_client = FeishuBitableClient(
            app_id=settings.FEISHU_APP_ID,
            app_secret=settings.FEISHU_APP_SECRET,
            app_token=settings.FEISHU_APP_TOKEN,
            table_id=settings.FEISHU_TABLE_ID
        )
    return _feishu_client


def format_records(records: List[Dict]) -> List[Dict]:
    """格式化记录数据，提取字段值"""
    formatted = []
    for record in records:
        fields = record.get("fields", {})
        formatted_record = {
            "record_id": record.get("record_id"),
            "数据": fields
        }
        formatted.append(formatted_record)
    return formatted


def fetch_feishu_data() -> List[Dict]:
    """
    从飞书多维表格获取数据
    使用自动刷新的 token
    """
    client = get_feishu_client()
    records = client.read_table_records()
    return format_records(records)


def print_feishu_records(records: List[Dict]) -> None:
    """打印飞书表格记录"""
    print(f"\n{'='*50}")
    print(f"📊 共读取到 {len(records)} 条记录")
    print('='*50)
    
    for i, record in enumerate(records, 1):
        print(f"\n📝 记录 {i} (ID: {record['record_id']}):")
        for field_name, value in record["数据"].items():
            print(f"   {field_name}: {value}")
    
    print('='*50 + "\n")
