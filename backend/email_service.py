"""
邮件发送服务
用于在匹配确认后发送匹配信息到参与者邮箱
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from config import settings
from models import MatchResult, Participant

logger = logging.getLogger(__name__)


class EmailService:
    """邮件发送服务"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.sender_email = settings.SENDER_EMAIL or self.smtp_user
        self.sender_name = settings.SENDER_NAME or "圣诞礼物匹配系统"
    
    def _create_giver_email_content(self, match: MatchResult, receiver_email: str) -> str:
        """创建送礼人邮件内容（HTML格式）"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #c41e3a; margin: 0; }}
        .header .emoji {{ font-size: 48px; }}
        .info-box {{ background: #fff8f0; border-left: 4px solid #c41e3a; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0; }}
        .info-label {{ color: #666; font-size: 14px; margin-bottom: 5px; }}
        .info-value {{ color: #333; font-size: 16px; font-weight: bold; }}
        .reason-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="emoji">🎄🎁</div>
            <h1>圣诞礼物匹配结果</h1>
            <p>你的神秘礼物接收者已揭晓！</p>
        </div>
        
        <p>亲爱的 <strong>{match.giver_name}</strong>，</p>
        <p>恭喜你！你的圣诞礼物匹配已完成。以下是你需要送礼的对象信息：</p>
        
        <div class="info-box">
            <div class="info-label">🎯 你要送礼给</div>
            <div class="info-value">{match.receiver_name}</div>
        </div>
        
        <div class="info-box">
            <div class="info-label">💬 对方微信</div>
            <div class="info-value">{match.receiver_wechat}</div>
        </div>
        
        <div class="info-box">
            <div class="info-label">🎁 你准备的礼物</div>
            <div class="info-value">{match.gift_summary}</div>
        </div>
        
        <div class="reason-box">
            <div style="font-size: 14px; opacity: 0.9; margin-bottom: 8px;">✨ 匹配理由</div>
            <div>{match.match_reason}</div>
        </div>
        
        <p>请尽快通过微信联系对方，安排礼物的交付方式哦！</p>
        <p>祝你圣诞快乐！🎅</p>
        
        <div class="footer">
            <p>此邮件由圣诞礼物匹配系统自动发送</p>
        </div>
    </div>
</body>
</html>
"""

    def _create_receiver_email_content(self, match: MatchResult, giver_email: str) -> str:
        """创建收礼人邮件内容（HTML格式）"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .header h1 {{ color: #228b22; margin: 0; }}
        .header .emoji {{ font-size: 48px; }}
        .info-box {{ background: #f0fff0; border-left: 4px solid #228b22; padding: 15px; margin: 20px 0; border-radius: 0 8px 8px 0; }}
        .info-label {{ color: #666; font-size: 14px; margin-bottom: 5px; }}
        .info-value {{ color: #333; font-size: 16px; font-weight: bold; }}
        .gift-box {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }}
        .gift-box .gift-name {{ font-size: 24px; font-weight: bold; margin: 10px 0; }}
        .reason-box {{ background: #f8f8f8; padding: 15px; border-radius: 8px; margin: 20px 0; font-style: italic; color: #555; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="emoji">🎁✨</div>
            <h1>你有一份圣诞礼物！</h1>
            <p>有人为你准备了特别的惊喜</p>
        </div>
        
        <p>亲爱的 <strong>{match.receiver_name}</strong>，</p>
        <p>圣诞快乐！有一位神秘的朋友为你准备了一份特别的礼物：</p>
        
        <div class="gift-box">
            <div>🎁</div>
            <div class="gift-name">{match.gift_summary}</div>
        </div>
        
        <div class="info-box">
            <div class="info-label">🎅 送礼人</div>
            <div class="info-value">{match.giver_name}</div>
        </div>
        
        <div class="info-box">
            <div class="info-label">💬 对方微信</div>
            <div class="info-value">{match.giver_wechat}</div>
        </div>
        
        <div class="reason-box">
            <div style="font-size: 12px; color: #999; margin-bottom: 8px;">💝 为什么是这份礼物？</div>
            {match.match_reason}
        </div>
        
        <p>对方会通过微信联系你安排礼物交付，请留意消息哦！</p>
        <p>愿这份礼物为你带来温暖和快乐！🎄</p>
        
        <div class="footer">
            <p>此邮件由圣诞礼物匹配系统自动发送</p>
        </div>
    </div>
</body>
</html>
"""

    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """发送单封邮件"""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            logger.error("邮件配置不完整，请检查 SMTP 相关环境变量")
            return False
        
        if not to_email:
            logger.warning("收件人邮箱为空，跳过发送")
            return False
        
        import ssl
        server = None
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email  # QQ邮箱要求From必须是发件邮箱
            msg['To'] = to_email
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 优先使用 TLS (587)，更稳定；SSL (465) 作为备选
            if self.smtp_port == 587:
                server = smtplib.SMTP(self.smtp_host, 587, timeout=30)
                server.starttls()
            elif self.smtp_port == 465:
                # 先尝试 SSL，失败则回退到 TLS
                try:
                    context = ssl.create_default_context()
                    server = smtplib.SMTP_SSL(self.smtp_host, 465, context=context, timeout=30)
                except ssl.SSLError:
                    server = smtplib.SMTP(self.smtp_host, 587, timeout=30)
                    server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30)
                server.starttls()
            
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.sender_email, to_email, msg.as_string())
            
            logger.info(f"✅ 邮件发送成功: {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ 邮件发送失败 ({to_email}): 认证失败 - {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ 邮件发送失败 ({to_email}): SMTP错误 - {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 邮件发送失败 ({to_email}): {type(e).__name__} - {e}")
            return False
        finally:
            # 确保关闭连接
            if server:
                try:
                    server.quit()
                except:
                    pass

    def send_match_notifications(
        self, 
        matches: List[MatchResult], 
        participants: List[Participant]
    ) -> dict:
        """
        发送匹配通知邮件给所有参与者
        
        Args:
            matches: 匹配结果列表
            participants: 参与者列表（用于获取邮箱信息）
        
        Returns:
            发送结果统计 {"success": int, "failed": int, "skipped": int}
        """
        import time
        
        # 构建 name -> email 映射
        email_map = {p.name: p.email for p in participants}
        
        stats = {"success": 0, "failed": 0, "skipped": 0}
        
        for match in matches:
            giver_email = email_map.get(match.giver_name, "")
            receiver_email = email_map.get(match.receiver_name, "")
            
            # 发送给送礼人
            if giver_email:
                logger.info(f"准备发送送礼通知给 {match.giver_name} ({giver_email})")
                giver_content = self._create_giver_email_content(match, receiver_email)
                if self.send_email(
                    giver_email, 
                    f"🎄 圣诞礼物匹配结果 - 你要送礼给 {match.receiver_name}", 
                    giver_content
                ):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                # 添加延迟避免频率限制
                time.sleep(1)
            else:
                logger.warning(f"送礼人 {match.giver_name} 没有邮箱，跳过")
                stats["skipped"] += 1
            
            # 发送给收礼人
            if receiver_email:
                logger.info(f"准备发送收礼通知给 {match.receiver_name} ({receiver_email})")
                receiver_content = self._create_receiver_email_content(match, giver_email)
                if self.send_email(
                    receiver_email, 
                    f"🎁 你有一份来自 {match.giver_name} 的圣诞礼物！", 
                    receiver_content
                ):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                # 添加延迟避免频率限制
                time.sleep(1)
            else:
                logger.warning(f"收礼人 {match.receiver_name} 没有邮箱，跳过")
                stats["skipped"] += 1
        
        return stats


# 单例实例
email_service = EmailService()
