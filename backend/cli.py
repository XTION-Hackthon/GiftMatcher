"""
CLI 命令入口
用于手动运行飞书数据读取和礼物匹配分析
"""
import sys
from typing import List, Optional

from feishu_reader import fetch_feishu_data, print_feishu_records
from models import Participant, QuizItem
from services import solve_gift_circle
from email_service import email_service


def parse_feishu_to_participants(feishu_records: List[dict]) -> List[Participant]:
    """
    将飞书表格数据转换为 Participant 对象列表
    
    飞书表格字段映射（根据用户提供的示例）：
    - 选手名 -> name
    - 邮箱 -> email
    - 微信账号 -> wechat
    - MBTI -> mbti
    - 准备的礼物描述 -> gift_description
    - 用户选择题的答案 -> quiz_data
    - 用户祝福话语 -> (可选，暂不使用)
    - 用户星座 -> (可选，暂不使用)
    - 礼物是否收到 -> (可选，暂不使用)
    """
    participants = []
    
    for idx, record in enumerate(feishu_records):
        fields = record.get("数据", {})
        record_id = record.get("record_id", f"user_{idx}")
        
        # 提取基本字段
        name = fields.get("选手名", fields.get("姓名", f"用户{idx+1}"))
        email = fields.get("邮箱", fields.get("email", ""))
        wechat = fields.get("微信账号", fields.get("微信", ""))
        # MBTI 处理：如果为空或无效值，保持为空字符串，让服务层处理
        mbti_raw = fields.get("MBTI", fields.get("mbti", ""))
        mbti = str(mbti_raw).strip() if mbti_raw else ""
        gift_description = fields.get("准备的礼物描述", fields.get("礼物描述", "神秘礼物"))
        
        # 处理问卷数据
        quiz_answer = fields.get("用户选择题的答案", "")
        quiz_data = []
        
        # 如果有问卷答案，解析为 QuizItem 列表
        if quiz_answer:
            if isinstance(quiz_answer, str):
                # 解析多行格式的问卷答案
                # 格式: "Q5: A. 壁炉里跳动的橙色火光\nQ4: C. 带有金属光泽的丝绸披肩\n..."
                lines = quiz_answer.strip().split("\n")
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    # 尝试解析 "Q5: A. xxx" 格式
                    if ": " in line:
                        parts = line.split(": ", 1)
                        question_id = parts[0].strip()  # Q5
                        answer = parts[1].strip() if len(parts) > 1 else ""  # A. xxx
                        quiz_data.append(QuizItem(
                            question_text=question_id,
                            selected_option=answer
                        ))
                    else:
                        # 无法解析的格式，整行作为答案
                        quiz_data.append(QuizItem(
                            question_text="问题",
                            selected_option=line
                        ))
            elif isinstance(quiz_answer, list):
                for i, ans in enumerate(quiz_answer):
                    quiz_data.append(QuizItem(
                        question_text=f"问题{i+1}",
                        selected_option=str(ans)
                    ))
        
        # 如果没有问卷数据，添加默认值
        if not quiz_data:
            quiz_data.append(QuizItem(
                question_text="默认问题",
                selected_option="未作答"
            ))
        
        participant = Participant(
            id=record_id,
            name=str(name) if name else f"用户{idx+1}",
            email=str(email) if email else "",
            wechat=str(wechat) if wechat else "",
            mbti=mbti,  # 保持原始值，可能为空
            gift_description=str(gift_description) if gift_description else "神秘礼物",
            quiz_data=quiz_data
        )
        participants.append(participant)
    
    return participants


def run_analysis():
    """
    主分析流程：
    1. 从飞书读取数据
    2. 转换为参与者列表
    3. 运行礼物匹配算法
    4. 输出结果
    """
    print("\n" + "="*60)
    print("🎄 圣诞礼物匹配系统 - CLI 模式")
    print("="*60)
    
    # Step 1: 读取飞书数据
    print("\n📡 Step 1: 正在从飞书多维表格读取数据...")
    try:
        feishu_records = fetch_feishu_data()
    except Exception as e:
        print(f"❌ 读取飞书数据失败: {e}")
        print("请检查飞书配置是否正确（.env 文件中的 FEISHU_* 配置项）")
        return
    
    if not feishu_records:
        print("❌ 未读取到任何记录，请检查飞书表格是否有数据")
        return
    
    # 打印原始数据
    print_feishu_records(feishu_records)
    
    # Step 2: 转换数据
    print("🔄 Step 2: 正在转换数据格式...")
    participants = parse_feishu_to_participants(feishu_records)
    
    print(f"✅ 成功解析 {len(participants)} 位参与者:")
    for p in participants:
        mbti_display = p.mbti if p.mbti else "未提供MBTI"
        print(f"   - {p.name} ({mbti_display}) | 礼物: {p.gift_description[:20]}...")
    
    if len(participants) < 2:
        print("❌ 参与者少于2人，无法进行匹配")
        return
    
    # Step 3: 运行匹配算法
    print("\n🎁 Step 3: 正在运行礼物匹配算法...")
    print("   (这可能需要一些时间，请耐心等待...)\n")
    
    try:
        results = solve_gift_circle(participants)
    except Exception as e:
        print(f"❌ 匹配算法执行失败: {e}")
        return
    
    # Step 4: 输出结果
    print("\n" + "="*60)
    print("🎉 匹配结果")
    print("="*60)
    
    for i, result in enumerate(results, 1):
        print(f"\n🎁 匹配 {i}:")
        print(f"   送礼人: {result.giver_name} (微信: {result.giver_wechat})")
        print(f"   收礼人: {result.receiver_name} (微信: {result.receiver_wechat})")
        print(f"   礼物: {result.gift_summary}")
        print(f"   匹配理由: {result.match_reason}")
    
    print("\n" + "="*60)
    print(f"✨ 匹配完成！共 {len(results)} 对匹配")
    print("="*60 + "\n")
    
    return results, participants


def send_match_emails(results: List, participants: List[Participant]):
    """
    发送匹配结果邮件给所有参与者
    """
    print("\n" + "="*60)
    print("📧 发送匹配结果邮件")
    print("="*60)
    
    # 检查邮件配置
    from config import settings
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
        print("❌ 邮件配置不完整，请在 .env 文件中配置以下项：")
        print("   - SMTP_HOST (如: smtp.qq.com)")
        print("   - SMTP_PORT (如: 465)")
        print("   - SMTP_USER (发件邮箱)")
        print("   - SMTP_PASSWORD (邮箱授权码)")
        return
    
    print(f"📤 正在发送邮件通知给 {len(participants)} 位参与者...")
    
    stats = email_service.send_match_notifications(results, participants)
    
    print(f"\n📊 发送统计:")
    print(f"   ✅ 成功: {stats['success']} 封")
    print(f"   ❌ 失败: {stats['failed']} 封")
    print(f"   ⏭️ 跳过(无邮箱): {stats['skipped']} 封")
    print("="*60 + "\n")


def show_help():
    """显示帮助信息"""
    print("""
🎄 圣诞礼物匹配系统 - CLI 命令帮助

使用方法:
    python cli.py <命令>

可用命令:
    fetch       仅读取并显示飞书表格数据（不进行匹配分析）
    analyze     读取飞书数据并运行完整的礼物匹配分析（不发送邮件）
    match       运行匹配分析并在确认后发送邮件通知
    help        显示此帮助信息

示例:
    python cli.py fetch      # 查看飞书表格中的数据
    python cli.py analyze    # 运行完整分析流程（不发邮件）
    python cli.py match      # 运行分析并发送邮件通知

配置说明:
    请确保 .env 文件中包含以下配置:
    
    飞书配置:
    - FEISHU_APP_TOKEN=xxx
    - FEISHU_TABLE_ID=xxx
    - FEISHU_TENANT_ACCESS_TOKEN=xxx
    
    邮件配置（用于 match 命令）:
    - SMTP_HOST=smtp.qq.com (或其他邮件服务商)
    - SMTP_PORT=465
    - SMTP_USER=your_email@qq.com
    - SMTP_PASSWORD=your_auth_code (邮箱授权码，非登录密码)
    - SENDER_NAME=圣诞礼物匹配系统 (可选)
""")


def run_match_with_email():
    """
    运行匹配分析并在确认后发送邮件
    """
    result = run_analysis()
    if not result:
        return
    
    results, participants = result
    
    # 询问用户是否确认发送邮件
    print("\n" + "="*60)
    print("📧 邮件发送确认")
    print("="*60)
    print("匹配结果已生成，是否发送邮件通知给所有参与者？")
    print("(每位参与者将收到两封邮件：一封告知送礼对象，一封告知收礼信息)")
    
    while True:
        confirm = input("\n请输入 'yes' 确认发送，或 'no' 取消: ").strip().lower()
        if confirm in ['yes', 'y']:
            send_match_emails(results, participants)
            break
        elif confirm in ['no', 'n']:
            print("❌ 已取消邮件发送")
            break
        else:
            print("请输入 'yes' 或 'no'")


def main():
    """CLI 主入口"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "fetch":
        print("\n📡 正在从飞书多维表格读取数据...")
        try:
            records = fetch_feishu_data()
            if records:
                print_feishu_records(records)
            else:
                print("❌ 未读取到任何记录")
        except Exception as e:
            print(f"❌ 读取失败: {e}")
    
    elif command == "analyze":
        run_analysis()
    
    elif command == "match":
        run_match_with_email()
    
    elif command == "help" or command == "-h" or command == "--help":
        show_help()
    
    else:
        print(f"❌ 未知命令: {command}")
        show_help()


if __name__ == "__main__":
    main()
