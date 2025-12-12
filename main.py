from typing import List

from fastapi import FastAPI, HTTPException

from models import MatchResponse, Participant
from services import get_ai_score_matrix, solve_gift_circle

app = FastAPI(title="Modular Gift Matcher")

@app.post("/match", response_model=MatchResponse)
async def match_gifts(participants: List[Participant]):
    # 1. 校验
    if len(participants) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 people.")

    # 2. 调用服务层 (Services)
    print("AI is thinking...") # 可以在终端打印日志
    ai_scores = get_ai_score_matrix(participants)
    
    print("Calculating best chain...")
    final_chain = solve_gift_circle(participants, ai_scores)
    
    # 3. 返回结果
    return MatchResponse(
        chain=final_chain,
        total_participants=len(participants)
    )

