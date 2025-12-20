#!/usr/bin/env python3
"""
圣诞礼物匹配系统 - 交互式入口
"""
import sys
import smtplib
import ssl
from typing import List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import settings
from models import Participant, QuizItem
from services import solve_gift_circle
from email_service import email_service


# ============================================================
# 工具函数
# ============================================================

def clear_screen():
    print("\033[2J\033[H", end="")


def print_banner():
    print("""
    ╔══════════════════════════════════════════╗
    ║       圣诞礼物匹配系统                   ║
    ╚══════════════════════════════════════════╝
    """)


def print_menu():
    print("    请选择操作:\n")
    print("    [1] 演示模式    使用模拟数据测试匹配流程")
    print("    [2] 正式运行    从飞书读取数据并匹配")
    print("    [3] 邮件测试    验证邮件配置是否正确")
    print("    [4] 启动服务    启动 API 服务器")
    print("    [0] 退出\n")


def input_choice(prompt: str, valid: List[str]) -> str:
    while True:
        choice = input(prompt).strip().lower()
        if choice in valid:
            return choice
        print(f"    无效输入，请输入: {', '.join(valid)}")


def confirm(prompt: str) -> bool:
    """确认操作，需要输入 yes"""
    print(f"\n    {prompt}")
    response = input("    输入 'yes' 确认，其他取消: ").strip().lower()
    return response == 'yes'


def pause():
    input("\n    按回车继续...")


# ============================================================
# Mock 数据
# ============================================================

def create_mock_participants() -> List[Participant]:
    """创建模拟参与者"""
    mock_data = [
        ("张小明", "INTJ", "zhangxm@test.com", "手工编织羊毛围巾", "Q1:A.看书|Q2:B.山区"),
        ("李思思", "", "lisisi@test.com", "复古机械键盘RGB", "Q1:D.游戏|Q2:A.城市"),
        ("王大力", "ENFP", "wangdl@test.com", "香薰蜡烛套装", "Q1:C.聚会|Q2:C.海边"),
        ("赵小雨", "ISTP", "zhaoxy@test.com", "迷你无人机", "Q1:B.运动|Q2:D.探险"),
    ]
    
    participants = []
    for i, (name, mbti, email, gift, quiz_str) in enumerate(mock_data):
        quiz_data = [QuizItem(question_text=p.split(":")[0], selected_option=p.split(":")[1]) 
                     for p in quiz_str.split("|")]
        participants.append(Participant(
            id=f"mock_{i}", name=name, email=email, wechat=f"wx_{name}",
            mbti=mbti, gift_description=gift, quiz_data=quiz_data
        ))
    return participants


# ============================================================
# 飞书数据
# ============================================================

def load_feishu_participants() -> Optional[List[Participant]]:
    """从飞书加载参与者（自动去重）"""
    from feishu_reader import fetch_feishu_data
    
    print("\n    正在从飞书读取数据...")
    try:
        records = fetch_feishu_data()
        if not records:
            print("    [!] 未读取到数据")
            return None
        
        participants = []
        seen_keys = set()  # 用于去重：(选手名, 邮箱)
        duplicates = 0
        
        for idx, record in enumerate(records):
            fields = record.get("数据", {})
            
            name = fields.get("选手名", f"用户{idx+1}")
            email = fields.get("邮箱", "")
            wechat = fields.get("微信账号", "")
            mbti = str(fields.get("MBTI", "")).strip()
            gift = fields.get("准备的礼物描述", "神秘礼物")
            
            # 去重检查：基于选手名+邮箱
            dedup_key = (str(name).strip().lower(), str(email).strip().lower())
            if dedup_key in seen_keys:
                duplicates += 1
                continue
            seen_keys.add(dedup_key)
            
            quiz_data = []
            quiz_answer = fields.get("用户选择题的答案", "")
            if quiz_answer:
                for line in str(quiz_answer).strip().split("\n"):
                    if ": " in line:
                        parts = line.split(": ", 1)
                        quiz_data.append(QuizItem(question_text=parts[0], selected_option=parts[1]))
            if not quiz_data:
                quiz_data.append(QuizItem(question_text="Q", selected_option="-"))
            
            participants.append(Participant(
                id=record.get("record_id", f"u{idx}"),
                name=str(name), email=str(email), wechat=str(wechat),
                mbti=mbti, gift_description=str(gift), quiz_data=quiz_data
            ))
        
        print(f"    已加载 {len(participants)} 位参与者（去重 {duplicates} 条重复记录）")
        return participants
        
    except Exception as e:
        print(f"    [!] 读取失败: {e}")
        return None


# ============================================================
# 显示函数
# ============================================================

def show_participants(participants: List[Participant]):
    """显示参与者列表"""
    print("\n    参与者列表:")
    print("    " + "-" * 50)
    print(f"    {'#':<3} {'姓名':<10} {'MBTI':<6} {'邮箱':<20} {'礼物'}")
    print("    " + "-" * 50)
    for i, p in enumerate(participants, 1):
        mbti = p.mbti if p.mbti else "-"
        email = p.email[:18] + ".." if len(p.email) > 18 else p.email
        gift = p.gift_description[:15] + ".." if len(p.gift_description) > 15 else p.gift_description
        print(f"    {i:<3} {p.name:<10} {mbti:<6} {email:<20} {gift}")
    print("    " + "-" * 50)


def show_results(results):
    """显示匹配结果"""
    print("\n    匹配结果:")
    print("    " + "=" * 50)
    for i, r in enumerate(results, 1):
        print(f"\n    [{i}] {r.giver_name}  --->  {r.receiver_name}")
        print(f"        礼物: {r.gift_summary}")
        print(f"        理由: {r.match_reason}")
    print("\n    " + "=" * 50)


def show_email_preview(results, participants):
    """显示邮件发送预览"""
    print("\n    邮件发送预览:")
    print("    " + "-" * 50)
    
    email_map = {p.name: p.email for p in participants}
    total = 0
    skip = 0
    
    for r in results:
        giver_email = email_map.get(r.giver_name, "")
        receiver_email = email_map.get(r.receiver_name, "")
        
        if giver_email:
            print(f"    -> {r.giver_name} ({giver_email}): 送礼通知")
            total += 1
        else:
            print(f"    -> {r.giver_name}: [跳过-无邮箱]")
            skip += 1
            
        if receiver_email:
            print(f"    -> {r.receiver_name} ({receiver_email}): 收礼通知")
            total += 1
        else:
            print(f"    -> {r.receiver_name}: [跳过-无邮箱]")
            skip += 1
    
    print("    " + "-" * 50)
    print(f"    共 {total} 封邮件待发送，{skip} 封跳过")
    return total


# ============================================================
# 核心流程
# ============================================================

def run_matching(participants: List[Participant]) -> Optional[List]:
    """运行匹配算法"""
    if len(participants) < 2:
        print("\n    [!] 参与者少于2人，无法匹配")
        return None
    
    show_participants(participants)
    
    print("\n    开始匹配...")
    print("    Phase 1: AI 评分")
    print("    Phase 2: 优化算法")
    print("    Phase 3: 生成文案")
    print()
    
    results = solve_gift_circle(participants)
    show_results(results)
    
    return results


def send_emails_with_confirm(results, participants):
    """带确认的邮件发送"""
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
        print("\n    [!] 邮件配置不完整，无法发送")
        print("    请在 .env 中配置 SMTP_HOST, SMTP_USER, SMTP_PASSWORD")
        return
    
    total = show_email_preview(results, participants)
    
    if total == 0:
        print("\n    没有可发送的邮件")
        return
    
    # 第一次确认
    if not confirm(f"即将发送 {total} 封邮件，是否继续?"):
        print("    已取消")
        return
    
    # 第二次确认
    print("\n    [!] 警告: 邮件发送后无法撤回")
    if not confirm("再次确认发送?"):
        print("    已取消")
        return
    
    print("\n    正在发送邮件...")
    stats = email_service.send_match_notifications(results, participants)
    print(f"\n    发送完成: 成功 {stats['success']}, 失败 {stats['failed']}, 跳过 {stats['skipped']}")


# ============================================================
# 模式入口
# ============================================================

def mode_demo():
    """演示模式"""
    clear_screen()
    print("\n    === 演示模式 ===")
    print("    使用模拟数据，不会发送真实邮件\n")
    
    participants = create_mock_participants()
    results = run_matching(participants)
    
    if results:
        choice = input_choice("\n    是否测试邮件发送? [y/n]: ", ['y', 'n', 'yes', 'no'])
        if choice in ['y', 'yes']:
            mode_email_test()


def mode_production():
    """正式运行模式"""
    clear_screen()
    print("\n    === 正式运行 ===")
    print("    从飞书读取真实数据\n")
    
    participants = load_feishu_participants()
    if not participants:
        pause()
        return
    
    results = run_matching(participants)
    if not results:
        pause()
        return
    
    choice = input_choice("\n    是否发送邮件通知? [y/n]: ", ['y', 'n', 'yes', 'no'])
    if choice in ['y', 'yes']:
        send_emails_with_confirm(results, participants)


def mode_email_test():
    """邮件测试模式"""
    clear_screen()
    print("\n    === 邮件配置测试 ===\n")
    
    print("    当前配置:")
    print(f"    SMTP 服务器: {settings.SMTP_HOST or '(未配置)'}")
    print(f"    SMTP 端口:   {settings.SMTP_PORT}")
    print(f"    发件邮箱:    {settings.SMTP_USER or '(未配置)'}")
    print(f"    授权码:      {'已配置' if settings.SMTP_PASSWORD else '(未配置)'}")
    
    if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD]):
        print("\n    [!] 配置不完整，请先配置 .env 文件")
        pause()
        return
    
    print(f"\n    默认收件人: {settings.SMTP_USER}")
    to_email = input("    输入测试收件邮箱 (回车使用默认): ").strip()
    if not to_email:
        to_email = settings.SMTP_USER
    
    if not confirm(f"发送测试邮件到 {to_email}?"):
        print("    已取消")
        return
    
    print("\n    发送中...")
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "圣诞礼物匹配系统 - 测试邮件"
    msg['From'] = settings.SMTP_USER
    msg['To'] = to_email
    msg.attach(MIMEText("<h2>测试成功</h2><p>邮件配置正常</p>", 'html', 'utf-8'))
    
    try:
        server = None
        # 优先尝试 TLS (587)，更稳定
        if settings.SMTP_PORT == 587:
            print("    使用 TLS 连接...")
            server = smtplib.SMTP(settings.SMTP_HOST, 587, timeout=30)
            server.starttls()
        elif settings.SMTP_PORT == 465:
            # 尝试 SSL，如果失败则回退到 TLS
            try:
                print("    尝试 SSL 连接...")
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, 465, context=context, timeout=30)
            except ssl.SSLError:
                print("    SSL 失败，切换到 TLS...")
                server = smtplib.SMTP(settings.SMTP_HOST, 587, timeout=30)
                server.starttls()
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
            server.starttls()
        
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, to_email, msg.as_string())
        server.quit()
        
        print(f"\n    [OK] 测试邮件已发送到 {to_email}")
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n    [!] 认证失败: {e}")
        print("    请检查: 1.授权码是否正确 2.是否开启SMTP服务")
    except Exception as e:
        print(f"\n    [!] 发送失败: {type(e).__name__}: {e}")


def mode_server():
    """启动 API 服务"""
    clear_screen()
    print("\n    === 启动 API 服务 ===")
    print("    服务地址: http://0.0.0.0:8000")
    print("    按 Ctrl+C 停止\n")
    
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


# ============================================================
# 主入口
# ============================================================

def main():
    while True:
        clear_screen()
        print_banner()
        print_menu()
        
        choice = input("    请输入选项: ").strip()
        
        if choice == '1':
            mode_demo()
            pause()
        elif choice == '2':
            mode_production()
            pause()
        elif choice == '3':
            mode_email_test()
            pause()
        elif choice == '4':
            mode_server()
        elif choice == '0' or choice.lower() in ['q', 'quit', 'exit']:
            print("\n    再见!\n")
            break
        else:
            print("\n    无效选项")
            pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n    已退出\n")
