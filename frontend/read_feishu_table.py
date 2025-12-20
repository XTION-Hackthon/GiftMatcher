import requests
import time
from datetime import datetime, timedelta
import json

# 飞书配置 (来自 api/index.py)
FEISHU_CONFIG = {
    "app_id": "cli_a8088174413b900b",
    "app_secret": "RIQ9eph9dVicJfXseZjCE8ESUD2C8BmX",
    "app_token": "T2WsbFLR3aNNnlscrQCchqjGn7c",
    "table_id": "tblZPt93lnlPzIM8"
}

class FeishuTokenManager:
    """飞书 Token 管理器，支持自动刷新"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_access_token = None
        self.token_expire_time = None
    
    def _get_new_tenant_token(self) -> str:
        """调用接口获取新的 tenant_access_token"""
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == 0:
                self.tenant_access_token = data.get("tenant_access_token")
                return self.tenant_access_token
            else:
                raise Exception(f"获取Token失败: {data.get('msg')}")
        else:
            raise Exception(f"请求失败: {response.status_code}")
    
    def get_token(self) -> str:
        return self._get_new_tenant_token()

def read_feishu_table():
    print("正在获取 Token...")
    try:
        token_manager = FeishuTokenManager(FEISHU_CONFIG["app_id"], FEISHU_CONFIG["app_secret"])
        token = token_manager.get_token()
        print(f"Token 获取成功: {token[:10]}...")
    except Exception as e:
        print(f"Token 获取失败: {e}")
        return

    print("正在读取表格数据...")
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['app_token']}/tables/{FEISHU_CONFIG['table_id']}/records"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 支持分页读取所有数据
    all_records = []
    page_token = None
    
    while True:
        params = {}
        if page_token:
            params['page_token'] = page_token
            
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 0:
                items = data['data']['items']
                all_records.extend(items)
                
                # 检查是否有下一页
                if data['data'].get('has_more'):
                    page_token = data['data']['page_token']
                else:
                    break
            else:
                print(f"读取失败: {data['msg']}")
                break
        else:
            print(f"请求失败: {response.status_code}")
            break
            
    print(f"\n成功读取到 {len(all_records)} 条记录:\n")
    print("-" * 50)
    for i, record in enumerate(all_records):
        print(f"记录 #{i+1}:")
        print(json.dumps(record['fields'], ensure_ascii=False, indent=2))
        print("-" * 50)

if __name__ == "__main__":
    read_feishu_table()
