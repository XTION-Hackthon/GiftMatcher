"""
模拟数据插入脚本
向飞书多维表格插入40条模拟用户数据
"""
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List

import requests

# 飞书配置
FEISHU_CONFIG = {
    "app_id": "cli_a8088174413b900b",
    "app_secret": "RIQ9eph9dVicJfXseZjCE8ESUD2C8BmX",
    "app_token": "T2WsbFLR3aNNnlscrQCchqjGn7c",
    "table_id": "tblZPt93lnlPzIM8"
}

TOKEN_REFRESH_THRESHOLD = 300


class FeishuTokenManager:
    """飞书 Token 管理器"""
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_access_token = None
        self.token_expire_time = None
    
    def _get_new_tenant_token(self) -> str:
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") != 0:
            raise Exception(f"获取token失败: {data.get('msg')}")
        
        self.tenant_access_token = data.get("tenant_access_token")
        expire_seconds = data.get("expire", 7200)
        self.token_expire_time = datetime.now() + timedelta(seconds=expire_seconds)
        print(f"✅ 成功获取新token，有效期至: {self.token_expire_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return self.tenant_access_token
    
    def get_token(self) -> str:
        if (not self.tenant_access_token or not self.token_expire_time or
            datetime.now() >= self.token_expire_time - timedelta(seconds=TOKEN_REFRESH_THRESHOLD)):
            return self._get_new_tenant_token()
        return self.tenant_access_token


# 模拟数据池
GIFT_DESCRIPTIONS = [
    "3D打印的小鹿",
    "手工编织的围巾",
    "复古风格的机械键盘",
    "定制的星空投影灯",
    "手绘的水彩画册",
    "精致的茶具套装",
    "蓝牙音箱小夜灯",
    "手工皮革钱包",
    "迷你多肉植物盆栽",
    "复古胶片相机",
    "手工香薰蜡烛套装",
    "定制姓名项链",
    "智能手环",
    "手工陶瓷杯",
    "创意台灯",
    "手工巧克力礼盒",
    "精装版小说",
    "手工编织毛毯",
    "复古留声机摆件",
    "手工刺绣挂画",
    "迷你无人机",
    "手工皂礼盒",
    "创意书签套装",
    "手工木质音乐盒",
    "智能保温杯",
    "手绘帆布包",
    "复古怀表",
    "手工果酱礼盒",
    "创意拼图",
    "手工编织帽子",
    "迷你投影仪",
    "手工饼干礼盒",
    "创意笔筒",
    "手工皮革手链",
    "智能台历",
    "手绘明信片套装",
    "复古打字机摆件",
    "手工干花相框",
    "创意存钱罐",
    "手工编织手套"
]

NAMES = [
    "悠一", "小明", "阿杰", "晓雪", "子涵", "雨萱", "浩然", "思琪",
    "俊杰", "雅婷", "志强", "美玲", "文博", "诗涵", "天宇", "欣怡",
    "建国", "婉儿", "伟明", "静雯", "嘉豪", "梦瑶", "泽宇", "雨晴",
    "鹏飞", "佳琪", "子轩", "雪儿", "浩宇", "诗雨", "明辉", "婷婷",
    "博文", "雅琪", "志远", "美琪", "天翔", "欣悦", "建华", "婉婷"
]

MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP"
]

ZODIACS = [
    "白羊座", "金牛座", "双子座", "巨蟹座",
    "狮子座", "处女座", "天秤座", "天蝎座",
    "射手座", "摩羯座", "水瓶座", "双鱼座"
]

BLESSINGS = [
    "开心每一天",
    "圣诞快乐！",
    "新年快乐，万事如意！",
    "愿你幸福安康",
    "祝你心想事成",
    "愿生活充满阳光",
    "祝一切顺利",
    "愿你每天都开心",
    "祝福满满",
    "愿梦想成真",
    "祝你好运连连",
    "愿你笑口常开",
    "祝平安喜乐",
    "愿你前程似锦",
    "祝你天天开心",
    "愿你幸福美满",
    "祝你事事顺心",
    "愿你快乐无忧",
    "祝你健康平安",
    "愿你如愿以偿"
]

# 20道问题及选项
QUIZ_QUESTIONS = {
    "Q1": {
        "question": "你更喜欢哪种圣诞树装饰风格？",
        "options": ["A. 传统红绿配色", "B. 现代简约白银", "C. 温馨暖色调", "D. 梦幻彩虹色"]
    },
    "Q2": {
        "question": "圣诞节你最期待的活动是？",
        "options": ["A. 家庭聚餐", "B. 朋友派对", "C. 独自看电影", "D. 户外滑雪"]
    },
    "Q3": {
        "question": "你理想的圣诞礼物是？",
        "options": ["A. 实用的电子产品", "B. 温暖的手工制品", "C. 有趣的体验券", "D. 精美的饰品"]
    },
    "Q4": {
        "question": "你喜欢什么材质的礼物包装？",
        "options": ["A. 环保牛皮纸", "B. 闪亮的金属纸", "C. 带有金属光泽的丝绸披肩", "D. 透明玻璃纸"]
    },
    "Q5": {
        "question": "你最喜欢的圣诞元素是？",
        "options": ["A. 壁炉里跳动的橙色火光", "B. 窗外飘落的雪花", "C. 圣诞老人", "D. 驯鹿雪橇"]
    },
    "Q6": {
        "question": "圣诞节你会选择什么饮品？",
        "options": ["A. 热可可", "B. 红酒", "C. 苹果汁", "D. 姜饼拿铁"]
    },
    "Q7": {
        "question": "你喜欢什么类型的圣诞音乐？",
        "options": ["A. 经典圣诞颂歌", "B. 现代流行翻唱", "C. 轻柔的钢琴曲", "D. 充满铃铛声的欢快儿歌"]
    },
    "Q8": {
        "question": "你会如何度过圣诞夜？",
        "options": ["A. 早早入睡等圣诞老人", "B. 通宵派对", "C. 看圣诞电影马拉松", "D. 和家人聊天"]
    },
    "Q9": {
        "question": "你喜欢什么风格的圣诞服装？",
        "options": ["A. 纯白色的高领细针织衫", "B. 红色圣诞毛衣", "C. 优雅的晚礼服", "D. 舒适的睡衣"]
    },
    "Q10": {
        "question": "你最喜欢的圣诞甜点是？",
        "options": ["A. 姜饼人", "B. 圣诞布丁", "C. 水果蛋糕", "D. 巧克力"]
    },
    "Q11": {
        "question": "你会给圣诞老人留什么？",
        "options": ["A. 牛奶和饼干", "B. 一封感谢信", "C. 胡萝卜给驯鹿", "D. 什么都不留"]
    },
    "Q12": {
        "question": "你喜欢什么颜色的圣诞灯？",
        "options": ["A. 暖黄色", "B. 彩色闪烁", "C. 冷白色", "D. 蓝色"]
    },
    "Q13": {
        "question": "圣诞节你会做什么善事？",
        "options": ["A. 捐赠物资", "B. 做志愿者", "C. 给邻居送礼物", "D. 陪伴家人"]
    },
    "Q14": {
        "question": "你喜欢什么类型的圣诞电影？",
        "options": ["A. 温馨家庭片", "B. 浪漫爱情片", "C. 搞笑喜剧片", "D. 奇幻冒险片"]
    },
    "Q15": {
        "question": "你会如何装饰你的房间？",
        "options": ["A. 挂满彩灯", "B. 摆放圣诞树", "C. 贴窗花", "D. 简单的花环"]
    },
    "Q16": {
        "question": "你最想收到谁的圣诞祝福？",
        "options": ["A. 家人", "B. 朋友", "C. 恋人", "D. 偶像"]
    },
    "Q17": {
        "question": "圣诞节你会吃什么主食？",
        "options": ["A. 烤火鸡", "B. 烤鸡", "C. 牛排", "D. 火锅"]
    },
    "Q18": {
        "question": "你喜欢什么样的圣诞卡片？",
        "options": ["A. 手绘风格", "B. 照片卡片", "C. 立体贺卡", "D. 电子贺卡"]
    },
    "Q19": {
        "question": "你喜欢什么尺寸的礼物？",
        "options": ["A. 小巧精致", "B. 越大越好，比如一套家具", "C. 中等大小", "D. 不在乎大小"]
    },
    "Q20": {
        "question": "圣诞节后你会做什么？",
        "options": ["A. 整理礼物", "B. 写感谢卡", "C. 计划新年", "D. 继续休息"]
    }
}


def generate_quiz_answers() -> str:
    """随机生成5道问题的答案"""
    selected_questions = random.sample(list(QUIZ_QUESTIONS.keys()), 5)
    answers = []
    for q_id in selected_questions:
        option = random.choice(QUIZ_QUESTIONS[q_id]["options"])
        answers.append(f"{q_id}: {option}")
    return "\n".join(answers)


def generate_mock_record(index: int) -> Dict:
    """生成一条模拟记录"""
    name = NAMES[index % len(NAMES)]
    # 生成唯一的微信和邮箱
    wechat = f"wx_{name}_{random.randint(100, 999)}"
    email = f"{name.lower()}_{random.randint(100, 999)}@gmail.com"
    
    return {
        "准备的礼物描述": random.choice(GIFT_DESCRIPTIONS),
        "选手名": name,
        "MBTI": random.choice(MBTI_TYPES),
        "邮箱": email,
        "微信账号": wechat,
        "用户选择题的答案": generate_quiz_answers(),
        "用户祝福话语": random.choice(BLESSINGS),
        "用户星座": random.choice(ZODIACS),
        "选择卡面": f"卡面{random.randint(1, 4)}",
        "选择装饰": f"装饰{random.randint(1, 4)}"
    }


def insert_record(token_manager: FeishuTokenManager, record: Dict) -> bool:
    """插入一条记录到飞书表格"""
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{FEISHU_CONFIG['app_token']}/tables/{FEISHU_CONFIG['table_id']}/records"
    headers = {
        "Authorization": f"Bearer {token_manager.get_token()}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json={"fields": record}, headers=headers)
        result = response.json()
        
        if result.get("code") != 0:
            print(f"❌ 插入失败: {result.get('msg')}")
            return False
        return True
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False


def main():
    print("=" * 60)
    print("🎄 圣诞礼物交换系统 - 模拟数据插入脚本")
    print("=" * 60)
    
    token_manager = FeishuTokenManager(
        app_id=FEISHU_CONFIG["app_id"],
        app_secret=FEISHU_CONFIG["app_secret"]
    )
    
    total = 40
    success_count = 0
    fail_count = 0
    
    print(f"\n📝 开始插入 {total} 条模拟数据...\n")
    
    for i in range(total):
        record = generate_mock_record(i)
        print(f"[{i+1}/{total}] 插入: {record['选手名']} - {record['准备的礼物描述'][:15]}...", end=" ")
        
        if insert_record(token_manager, record):
            print("✅")
            success_count += 1
        else:
            print("❌")
            fail_count += 1
        
        # 避免请求过快
        time.sleep(0.3)
    
    print("\n" + "=" * 60)
    print(f"🎉 插入完成！成功: {success_count}, 失败: {fail_count}")
    print("=" * 60)


if __name__ == "__main__":
    main()
