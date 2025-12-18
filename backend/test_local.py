"""
本地测试脚本
不依赖飞书，使用模拟数据测试匹配算法和邮件功能
"""
import sys
from typing import List

from models import Participant, QuizItem
from services import solve_gift_circle
from email_service import email_service


def create_test_participants() -> List[Participant]:
    """创建测试参与者数据"""
    
    # 测试数据：包含有MBTI和无MBTI的情况
    test_data = [
        {
            "id": "user_1",
            "name": "张三",
            "email": "zhangsan@example.com",  # 替换为你的测试邮箱
            "wechat": "wx_zhangsan",
            "mbti": "INTJ",  # 有MBTI
            "gift_description": "手工编织的围巾，温暖柔软",
            "quiz_answers": [
                ("周末活动", "A. 在家看书"),
                ("度假方式", "B. 安静的山区"),
                ("喜欢的颜色", "C. 深蓝色")
            ]
        },
        {
            "id": "user_2",
            "name": "李四",
            "email": "lisi@example.com",  # 替换为你的测试邮箱
            "wechat": "wx_lisi",
            "mbti": "",  # 无MBTI
            "gift_description": "复古风格的机械键盘",
            "quiz_answers": [
                ("周末活动", "D. 打游戏"),
                ("度假方式", "A. 热闹的城市"),
                ("喜欢的颜色", "A. 黑色")
            ]
        },
        {
            "id": "user_3",
            "name": "王五",
            "email": "wangwu@example.com",  # 替换为你的测试邮箱
            "wechat": "wx_wangwu",
            "mbti": "ENFP",  # 有MBTI
            "gift_description": "手工香薰蜡烛套装",
            "quiz_answers": [
                ("周末活动", "C. 和朋友聚会"),
                ("度假方式", "C. 海边度假"),
                ("喜欢的颜色", "D. 粉色")
            ]
        },
        {
            "id": "user_4",
            "name": "赵六",
            "email": "zhaoliu@example.com",  # 替换为你的测试邮箱
            "wechat": "wx_zhaoliu",
            "mbti": "ISTP",  # 有MBTI
            "gift_description": "迷你无人机",
            "quiz_answers": [
                ("周末活动", "B. 户外运动"),
                ("度假方式", "D. 探险旅行"),
                ("喜欢的颜色", "B. 灰色")
            ]
        },
        {
            "id": "user_5",
            "name": "孙七",
            "email": "sunqi@example.com",  # 替换为你的测试邮箱
            "wechat": "wx_sunqi",
            "mbti": "",  # 无MBTI
            "gift_description": "精致的茶具套装",
            "quiz_answers": [
                ("周末活动", "A. 在家看书"),
                ("度假方式", "B. 安静的山区"),
                ("喜欢的颜色", "C. 绿色")
            ]
        }
    ]
    
    participants = []
    for data in test_data:
        quiz_data = [
            QuizItem(question_text=q, selected_option=a)
            for q, a in data["quiz_answers"]
        ]
        
        participant = Participant(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            wechat=data["wechat"],
            mbti=data["mbti"],
            gift_description=data["gift_description"],
            quiz_data=quiz_data
        )
        participants.append(participant)
    
    return participants


def test_matching_only():
    """测试1: 仅测试匹配算法（不发送邮件）"""
    print("\n" + "="*60)
    print("🧪 测试1: 匹配算法测试")
    print("="*60)
    
    participants = create_test_participants()
    
    print(f"\n📋 测试参与者 ({len(participants)}人):")
    for p in participants:
        mbti_display = p.mbti if p.mbti else "❌ 无MBTI"
        print(f"   - {p.name} ({mbti_display}) | 礼物: {p.gift_description[:20]}...")
    
    print("\n🔄 开始运行匹配算法...\n")
    
    try:
        results = solve_gift_circle(participants)
        
        print("\n" + "="*60)
        print("✅ 匹配结果")
        print("="*60)
        
        for i, result in enumerate(results, 1):
            print(f"\n🎁 匹配 {i}:")
            print(f"   送礼人: {result.giver_name} (微信: {result.giver_wechat})")
            print(f"   收礼人: {result.receiver_name} (微信: {result.receiver_wechat})")
            print(f"   礼物: {result.gift_summary}")
            print(f"   匹配理由: {result.match_reason}")
        
        print("\n" + "="*60)
        print(f"✨ 测试完成！共 {len(results)} 对匹配")
        print("="*60 + "\n")
        
        return results, participants
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_email_sending(results, participants):
    """测试2: 测试邮件发送功能"""
    print("\n" + "="*60)
    print("🧪 测试2: 邮件发送测试")
    print("="*60)
    
    # 检查邮件配置
    from config import settings
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
        print("\n❌ 邮件配置不完整，请在 .env 文件中配置以下项：")
        print("   - SMTP_HOST (如: smtp.qq.com)")
        print("   - SMTP_PORT (如: 465)")
        print("   - SMTP_USER (发件邮箱)")
        print("   - SMTP_PASSWORD (邮箱授权码)")
        print("\n💡 提示: 复制 .env.example 为 .env 并填写配置")
        return
    
    print(f"\n📧 邮件配置:")
    print(f"   SMTP服务器: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
    print(f"   发件邮箱: {settings.SMTP_USER}")
    print(f"   发件人名称: {settings.SENDER_NAME}")
    
    print(f"\n📤 将发送邮件给 {len(participants)} 位参与者")
    print("   (每人收到2封邮件: 送礼通知 + 收礼通知)")
    
    # 确认发送
    confirm = input("\n⚠️  确认发送测试邮件? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ 已取消邮件发送")
        return
    
    print("\n📨 开始发送邮件...\n")
    
    try:
        stats = email_service.send_match_notifications(results, participants)
        
        print("\n" + "="*60)
        print("📊 发送统计")
        print("="*60)
        print(f"   ✅ 成功: {stats['success']} 封")
        print(f"   ❌ 失败: {stats['failed']} 封")
        print(f"   ⏭️  跳过(无邮箱): {stats['skipped']} 封")
        print("="*60 + "\n")
        
        if stats['success'] > 0:
            print("💡 请检查测试邮箱，查看收到的邮件")
        
    except Exception as e:
        print(f"\n❌ 邮件发送失败: {e}")
        import traceback
        traceback.print_exc()


def test_single_email():
    """测试3: 发送单封测试邮件"""
    print("\n" + "="*60)
    print("🧪 测试3: 单封邮件测试")
    print("="*60)
    
    from config import settings
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
        print("\n❌ 邮件配置不完整")
        return
    
    test_email = input("\n请输入测试邮箱地址: ").strip()
    if not test_email:
        print("❌ 邮箱地址不能为空")
        return
    
    print(f"\n📧 将发送测试邮件到: {test_email}")
    
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; color: #c41e3a; }
        .emoji { font-size: 48px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="emoji">🎄✨</div>
            <h1>邮件服务测试</h1>
        </div>
        <p>这是一封测试邮件，用于验证邮件服务配置是否正确。</p>
        <p>如果你收到这封邮件，说明邮件服务配置成功！</p>
        <p style="text-align: center; color: #999; font-size: 12px; margin-top: 30px;">
            此邮件由圣诞礼物匹配系统自动发送
        </p>
    </div>
</body>
</html>
"""
    
    try:
        success = email_service.send_email(
            test_email,
            "🎄 圣诞礼物匹配系统 - 邮件测试",
            html_content
        )
        
        if success:
            print(f"\n✅ 测试邮件发送成功！")
            print(f"💡 请检查邮箱 {test_email} 是否收到邮件")
        else:
            print(f"\n❌ 测试邮件发送失败")
            
    except Exception as e:
        print(f"\n❌ 发送失败: {e}")
        import traceback
        traceback.print_exc()


def show_menu():
    """显示测试菜单"""
    print("\n" + "="*60)
    print("🎄 圣诞礼物匹配系统 - 本地测试")
    print("="*60)
    print("\n请选择测试项目:")
    print("  1. 测试匹配算法（不发送邮件）")
    print("  2. 测试完整流程（匹配 + 邮件）")
    print("  3. 发送单封测试邮件")
    print("  4. 查看测试数据")
    print("  0. 退出")
    print("="*60)


def show_test_data():
    """显示测试数据"""
    print("\n" + "="*60)
    print("📋 测试数据预览")
    print("="*60)
    
    participants = create_test_participants()
    
    for i, p in enumerate(participants, 1):
        print(f"\n👤 参与者 {i}:")
        print(f"   姓名: {p.name}")
        print(f"   邮箱: {p.email}")
        print(f"   微信: {p.wechat}")
        print(f"   MBTI: {p.mbti if p.mbti else '❌ 未提供'}")
        print(f"   礼物: {p.gift_description}")
        print(f"   问卷: {', '.join([q.selected_option for q in p.quiz_data])}")
    
    print("\n" + "="*60)
    print("💡 提示: 请将测试数据中的邮箱地址替换为你的真实邮箱")
    print("   编辑文件: backend/test_local.py")
    print("="*60)


def main():
    """主测试流程"""
    results = None
    participants = None
    
    while True:
        show_menu()
        choice = input("\n请输入选项 (0-4): ").strip()
        
        if choice == "1":
            results, participants = test_matching_only()
        
        elif choice == "2":
            if not results or not participants:
                results, participants = test_matching_only()
            if results and participants:
                test_email_sending(results, participants)
        
        elif choice == "3":
            test_single_email()
        
        elif choice == "4":
            show_test_data()
        
        elif choice == "0":
            print("\n👋 再见！")
            break
        
        else:
            print("\n❌ 无效选项，请重新输入")


if __name__ == "__main__":
    main()
