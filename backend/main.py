from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from models import MatchResponse, MatchResult, Participant
from services import solve_gift_circle
from email_service import email_service

app = FastAPI(title="Modular Gift Matcher")


class EmailSendRequest(BaseModel):
    """邮件发送请求"""
    matches: List[MatchResult]
    participants: List[Participant]


class EmailSendResponse(BaseModel):
    """邮件发送响应"""
    success: int
    failed: int
    skipped: int
    message: str


@app.post("/match", response_model=MatchResponse)
async def match_gifts(participants: List[Participant]):
    # 1. 校验
    if len(participants) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 people.")

    print(f"🚀 Received request for {len(participants)} participants. Starting process...")

    # 2. 调用服务层 (Services)
    # 新的函数内部封装了 Phase 1(打分) -> Phase 2(算法) -> Phase 3(文案)
    final_chain = solve_gift_circle(participants)
    
    # 3. 返回结果
    return MatchResponse(
        chain=final_chain,
        total_participants=len(participants)
    )


@app.post("/send-emails", response_model=EmailSendResponse)
async def send_match_emails(request: EmailSendRequest):
    """
    发送匹配结果邮件给所有参与者
    
    在前端确认匹配结果后调用此接口发送邮件通知
    """
    if not request.matches:
        raise HTTPException(status_code=400, detail="No matches provided.")
    
    if not request.participants:
        raise HTTPException(status_code=400, detail="No participants provided.")
    
    print(f"📧 Sending emails for {len(request.matches)} matches...")
    
    stats = email_service.send_match_notifications(
        request.matches, 
        request.participants
    )
    
    return EmailSendResponse(
        success=stats["success"],
        failed=stats["failed"],
        skipped=stats["skipped"],
        message=f"邮件发送完成: {stats['success']}封成功, {stats['failed']}封失败, {stats['skipped']}封跳过"
    )


@app.post("/match-and-send", response_model=MatchResponse)
async def match_and_send_emails(participants: List[Participant], send_email: bool = False):
    """
    匹配礼物并可选发送邮件
    
    Args:
        participants: 参与者列表
        send_email: 是否发送邮件通知（默认False）
    """
    # 1. 校验
    if len(participants) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 people.")

    print(f"🚀 Received request for {len(participants)} participants. Starting process...")

    # 2. 运行匹配
    final_chain = solve_gift_circle(participants)
    
    # 3. 如果需要发送邮件
    if send_email:
        print(f"📧 Auto-sending emails...")
        stats = email_service.send_match_notifications(final_chain, participants)
        print(f"📊 Email stats: {stats}")
    
    # 4. 返回结果
    return MatchResponse(
        chain=final_chain,
        total_participants=len(participants)
    )

