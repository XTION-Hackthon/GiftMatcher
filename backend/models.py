from typing import List, Optional

from pydantic import BaseModel


class QuizItem(BaseModel):
    """问卷题目和选项"""
    question_text: str
    selected_option: str

class Participant(BaseModel):
    """参赛者完整信息"""
    id: str
    name: str
    email: str
    wechat: str
    mbti: str
    gift_description: str
    quiz_data: List[QuizItem]

class MatchResult(BaseModel):
    """返回给前端的单个匹配结果"""
    giver_name: str
    giver_wechat: str
    receiver_name: str
    receiver_wechat: str
    gift_summary: str
    match_reason: str

class MatchResponse(BaseModel):
    """API 返回的总结构"""
    chain: List[MatchResult]
    total_participants: int
