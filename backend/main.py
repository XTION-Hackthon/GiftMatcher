from typing import List

from fastapi import FastAPI, HTTPException

from models import MatchResponse, Participant
# 变化 1: 只导入 solve_gift_circle，不再需要 get_ai_score_matrix
from services import solve_gift_circle

app = FastAPI(title="Modular Gift Matcher")

@app.post("/match", response_model=MatchResponse)
async def match_gifts(participants: List[Participant]):
    # 1. 校验
    if len(participants) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 people.")

    print(f"🚀 Received request for {len(participants)} participants. Starting process...")

    # 2. 调用服务层 (Services)
    # 变化 2: 新的函数内部封装了 Phase 1(打分) -> Phase 2(算法) -> Phase 3(文案)
    # 主函数变得非常干净，不需要再传递中间变量
    final_chain = solve_gift_circle(participants)
    
    # 3. 返回结果
    return MatchResponse(
        chain=final_chain,
        total_participants=len(participants)
    )

