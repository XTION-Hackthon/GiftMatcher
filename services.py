import json
import random
from typing import Dict, List

from fastapi import HTTPException
from openai import OpenAI

from config import settings
from models import MatchResult, Participant

# 初始化 AI 客户端
client = OpenAI(api_key=settings.API_KEY, base_url=settings.BASE_URL)


def get_ai_score_matrix(participants: List[Participant]) -> List[Dict]:
    """业务逻辑：调用 AI 打分"""

    profiles_text = []
    for p in participants:
        quiz_summary = " | ".join(
            [f"Q: {q.question_text} -> Ans: {q.selected_option}" for q in p.quiz_data]
        )
        user_str = (
            f"--- User ID: {p.id} ---\n"
            f"Name: {p.name}, MBTI: {p.mbti}\n"
            f'Gift Description: "{p.gift_description}"\n'
            f"Quiz Choices: {quiz_summary}\n"
        )
        profiles_text.append(user_str)

    full_context = "\n".join(profiles_text)

    system_prompt = """
    You are an AI Gift Matching Expert. 
    Analyze the participants' quiz answers (personality/taste) and their gift descriptions.
    
    GOAL: Calculate a "Desire Score" (0-100) for every pair (Receiver, Gift).
    
    RULES:
    1. Receiver cannot get their own gift (Score = 0).
    2. Extract a short 'gift_short_name' from the description.
    3. Output JSON format only: {"matches": [{"receiver_id": "...", "gift_from_id": "...", "score": 80, "reason": "...", "gift_short_name": "..."}]}
    """

    try:
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,  # 使用配置文件里的模型名
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Data:\n{full_context}"},
            ],
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("matches", [])
    except Exception as e:
        print(f"AI Error: {e}")
        # 如果出错返回空列表，避免程序直接崩溃
        return []


def solve_gift_circle(
    participants: List[Participant], matches: List[Dict]
) -> List[MatchResult]:
    """业务逻辑：算法求解哈密顿回路"""
    if not matches:
        raise HTTPException(status_code=500, detail="AI returned no data")

    p_ids = [p.id for p in participants]
    n = len(p_ids)

    # 构建查找表
    score_map = {}
    for m in matches:
        score_map[(m["receiver_id"], m["gift_from_id"])] = (
            m["score"],
            m["reason"],
            m.get("gift_short_name", "Gift"),
        )

    # 简化的随机寻找算法
    best_chain = None
    best_total_score = -1
    best_reasons = []
    best_gifts = []

    for _ in range(200):  # 尝试200次
        current_chain = p_ids[:]
        random.shuffle(current_chain)

        score = 0
        valid = True
        reasons = []
        gifts = []

        for i in range(n):
            giver = current_chain[i]
            receiver = current_chain[(i + 1) % n]

            if giver == receiver:
                valid = False
                break

            data = score_map.get((receiver, giver))
            if not data:
                s, r, g = 0, "No data", "Unknown"
            else:
                s, r, g = data

            score += s
            reasons.append(r)
            gifts.append(g)

        if valid and score > best_total_score:
            best_total_score = score
            best_chain = current_chain
            best_reasons = reasons
            best_gifts = gifts

    # 组装结果
    results = []
    p_map = {p.id: p for p in participants}

    # 兜底：如果找不到链（极少情况），直接按顺序
    if not best_chain:
        best_chain = p_ids
        best_reasons = ["Random Fallback"] * n
        best_gifts = ["Gift"] * n

    for i in range(n):
        giver_id = best_chain[i]
        receiver_id = best_chain[(i + 1) % n]
        results.append(
            MatchResult(
                giver_name=p_map[giver_id].name,
                giver_wechat=p_map[giver_id].wechat,
                receiver_name=p_map[receiver_id].name,
                receiver_wechat=p_map[receiver_id].wechat,
                gift_summary=best_gifts[i],
                match_reason=best_reasons[i],
            )
        )

    return results
