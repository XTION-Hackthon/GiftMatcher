from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# 飞书配置
FEISHU_CONFIG = {
    "app_id": "cli_a8088174413b900b",
    "app_secret": "RIQ9eph9dVicJfXseZjCE8ESUD2C8BmX",
    "app_token": "T2WsbFLR3aNNnlscrQCchqjGn7c",
    "table_id": "tblZPt93lnlPzIM8"
}

TOKEN_REFRESH_THRESHOLD = 300  # 提前刷新阈值（秒），提前5分钟刷新


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
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") != 0:
            raise Exception(f"获取token失败: {data.get('msg')} (错误码: {data.get('code')})")
        
        self.tenant_access_token = data.get("tenant_access_token")
        expire_seconds = data.get("expire", 7200)  # 默认2小时有效期
        self.token_expire_time = datetime.now() + timedelta(seconds=expire_seconds)
        print(f"✅ 成功获取新token，有效期至: {self.token_expire_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return self.tenant_access_token
    
    def get_token(self) -> str:
        """获取有效的 tenant_access_token（自动刷新）"""
        if (not self.tenant_access_token or not self.token_expire_time or
            datetime.now() >= self.token_expire_time - timedelta(seconds=TOKEN_REFRESH_THRESHOLD)):
            return self._get_new_tenant_token()
        return self.tenant_access_token


# 全局 Token 管理器实例（单例模式，复用 token）
token_manager = FeishuTokenManager(
    app_id=FEISHU_CONFIG["app_id"],
    app_secret=FEISHU_CONFIG["app_secret"]
)


@app.route('/api/submit', methods=['POST'])
def submit_to_feishu():
    """接收前端数据并提交到飞书多维表格"""
    try:
        form_data = request.json
        if not form_data:
            return jsonify({"code": -1, "msg": "无效的请求数据"}), 400
        
        # 获取 access token（自动刷新）
        access_token = token_manager.get_token()
        
        # 提交到飞书
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['app_token']}/tables/{FEISHU_CONFIG['table_id']}/records"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json={"fields": form_data}, headers=headers)
        result = response.json()
        
        if result.get("code") != 0:
            return jsonify({"code": result.get("code"), "msg": result.get("msg")}), 400
        
        return jsonify({"code": 0, "msg": "success", "data": result.get("data")})
    
    except Exception as e:
        return jsonify({"code": -1, "msg": str(e)}), 500

if __name__ == '__main__':
    from flask import send_from_directory
    import os

    # Get the project root directory (parent of api directory)
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    @app.route('/')
    def serve_index():
        return send_from_directory(PROJECT_ROOT, 'index.html')

    @app.route('/<path:filename>')
    def serve_static(filename):
        return send_from_directory(PROJECT_ROOT, filename)

    print(f"Starting local server at http://localhost:5000")
    print(f"Serving files from {PROJECT_ROOT}")
    app.run(port=5000, debug=True)
