import json
import logging
import random
from typing import Dict, List

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from config import settings
from models import MatchResult, Participant

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.API_KEY, base_url=settings.BASE_URL)

# =========================================================
#  数据结构校验 (Pydantic)
# =========================================================

class ScoreItem(BaseModel):
    gift_from_id: str
    score: int

class ScoreBatchResponse(BaseModel):
    receiver_id: str
    scores: List[ScoreItem]

class StoryItem(BaseModel):
    giver_id: str
    receiver_id: str
    match_reason: str
    gift_short_name: str

# =========================================================
#  Phase 1: 纯数值评分 (The Mathematician)
# =========================================================

def get_numeric_score_matrix(participants: List[Participant]) -> List[List[int]]:
    n = len(participants)
    p_ids = [p.id for p in participants]
    matrix = [[5] * n for _ in range(n)] # 默认 5 分
    for i in range(n):
        matrix[i][i] = 0 # 自环为 0

    gifts_context = "\n".join([f"ID: {p.id} | Gift: {p.gift_description}" for p in participants])
    BATCH_SIZE = 5
    
    logger.info(f"Phase 1: Calculating scores for {n} users...")

    for i in range(0, n, BATCH_SIZE):
        batch = participants[i : i + BATCH_SIZE]
        receivers_context = "\n".join([
            f"ID: {p.id} | MBTI: {p.mbti} | Quiz: " + 
            "|".join([f"{q.question_text[:5]}->{q.selected_option}" for q in p.quiz_data]) 
            for p in batch
        ])

        system_prompt = """
You are a Scoring Engine. 
Input: Receivers and Gifts.
Task: Rate the compatibility (0-100) for each Receiver against ALL Gifts.
Rules:
1. Output JSON only.
2. Structure: {"results": [{"receiver_id": "...", "scores": [{"gift_from_id": "...", "score": 88}, ...]}]}
3. High score = Good personality match.
4. Return Top 5 matches per receiver is enough.
"""
        try:
            response = client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Receivers:\n{receivers_context}\n\nGifts:\n{gifts_context}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            
            raw_json = json.loads(response.choices[0].message.content)
            results_list = raw_json.get("results", [])
            
            for item in results_list:
                try:
                    data = ScoreBatchResponse(**item)
                    if data.receiver_id in p_ids:
                        r_idx = p_ids.index(data.receiver_id)
                        for s_item in data.scores:
                            if s_item.gift_from_id in p_ids:
                                g_idx = p_ids.index(s_item.gift_from_id)
                                if r_idx != g_idx:
                                    matrix[g_idx][r_idx] = s_item.score
                except ValidationError:
                    continue
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            continue

    return matrix

# =========================================================
#  Phase 2: 自适应混合模因算法 (The Strategist)
#  (此处恢复了完整的算法逻辑)
# =========================================================

class Individual:
    def __init__(self, chain: List[int], score: int):
        self.chain = chain
        self.score = score

def calc_score(chain: List[int], weights: List[List[int]], n: int) -> int:
    s = 0
    for i in range(n):
        s += weights[chain[i]][chain[(i + 1) % n]]
    return s

def local_search(chain: List[int], weights: List[List[int]], n: int) -> Individual:
    current_chain = chain[:]
    current_score = calc_score(current_chain, weights, n)
    MAX_STEPS = 50 # 局部搜索深度
    
    improved = True
    step = 0
    while improved and step < MAX_STEPS:
        improved = False
        step += 1
        for i in range(n):
            for j in range(i + 1, n):
                current_chain[i], current_chain[j] = current_chain[j], current_chain[i]
                new_score = calc_score(current_chain, weights, n)
                if new_score > current_score:
                    current_score = new_score
                    improved = True
                    break # 贪心：一有改进立刻应用
                else:
                    current_chain[i], current_chain[j] = current_chain[j], current_chain[i]
            if improved: break
    return Individual(current_chain, current_score)

def crossover_ox1(parent1: Individual, parent2: Individual, weights: List[List[int]], n: int) -> Individual:
    if n < 3: return local_search(parent1.chain, weights, n)
    
    cx1 = random.randint(0, n - 2)
    cx2 = random.randint(cx1 + 1, n - 1)
    
    child_chain = [-1] * n
    child_chain[cx1:cx2] = parent1.chain[cx1:cx2]
    
    p1_set = set(child_chain[cx1:cx2])
    available = [x for x in parent2.chain if x not in p1_set]
    
    curr = 0
    for i in range(n):
        if child_chain[i] == -1:
            child_chain[i] = available[curr]
            curr += 1
            
    return local_search(child_chain, weights, n)

def solve_with_memetic_algorithm(n: int, weights: List[List[int]]) -> List[int]:
    """完整版 Memetic Algorithm 实现"""
    if n < 2: return [0] if n==1 else []

    POP_SIZE = 40
    GENERATIONS = 50 # 迭代代数
    ELITISM = 5
    
    # 1. 初始化种群
    population = []
    for _ in range(POP_SIZE):
        c = list(range(n))
        random.shuffle(c)
        population.append(local_search(c, weights, n))
    
    population.sort(key=lambda x: x.score, reverse=True)
    best_global = population[0]
    no_imp = 0
    
    # 2. 进化
    for gen in range(GENERATIONS):
        new_pop = population[:ELITISM]
        
        while len(new_pop) < POP_SIZE:
            # 锦标赛选择
            pool = random.sample(population, min(3, len(population)))
            p1 = max(pool, key=lambda x: x.score)
            pool = random.sample(population, min(3, len(population)))
            p2 = max(pool, key=lambda x: x.score)
            
            child = crossover_ox1(p1, p2, weights, n)
            new_pop.append(child)
            
        population = new_pop
        population.sort(key=lambda x: x.score, reverse=True)
        
        if population[0].score > best_global.score:
            best_global = population[0]
            no_imp = 0
        else:
            no_imp += 1
            
        # 逃逸机制
        if no_imp > 15:
            replace_idx = int(POP_SIZE * 0.7)
            for i in range(replace_idx, POP_SIZE):
                c = list(range(n))
                random.shuffle(c)
                population[i] = local_search(c, weights, n)
            no_imp = 0
            
    return best_global.chain

# =========================================================
#  Phase 3: 纯文案生成 (The Writer)
# =========================================================

def generate_stories_for_chain(chain_indices: List[int], participants: List[Participant]) -> List[MatchResult]:
    n = len(participants)
    results = []
    pairs_to_generate = []
    
    for i in range(n):
        giver_idx = chain_indices[i]
        receiver_idx = chain_indices[(i + 1) % n]
        pairs_to_generate.append({
            "giver": participants[giver_idx],
            "receiver": participants[receiver_idx]
        })
    
    BATCH_SIZE = 5
    logger.info(f"Phase 3: Generating stories for {n} pairs...")
    story_map = {}

    for i in range(0, n, BATCH_SIZE):
        batch_pairs = pairs_to_generate[i : i + BATCH_SIZE]
        context_lines = []
        for pair in batch_pairs:
            g, r = pair["giver"], pair["receiver"]
            context_lines.append(
                f"Pair: GiverID={g.id} (Gift: {g.gift_description}) -> ReceiverID={r.id} (MBTI: {r.mbti})"
            )
        
        system_prompt = """
You are a Gift Storyteller.
Task: Write a short, engaging reason for why this gift fits the receiver.
Rules:
1. Output JSON: {"stories": [{"giver_id": "...", "receiver_id": "...", "match_reason": "...", "gift_short_name": "..."}]}
2. Be polite and creative.
"""
        try:
            response = client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "\n".join(context_lines)}
                ],
                response_format={"type": "json_object"}
            )
            raw_json = json.loads(response.choices[0].message.content)
            if "stories" in raw_json:
                for item in raw_json["stories"]:
                    try:
                        story = StoryItem(**item)
                        story_map[(story.giver_id, story.receiver_id)] = story
                    except ValidationError:
                        continue
        except Exception as e:
            logger.error(f"Story generation failed: {e}")
            continue

    # 组装
    for pair in pairs_to_generate:
        g, r = pair["giver"], pair["receiver"]
        story = story_map.get((g.id, r.id))
        
        if story:
            reason = story.match_reason
            gift_name = story.gift_short_name
        else:
            reason = "这是一次神秘的匹配，也许冥冥之中自有天意。"
            gift_name = (g.gift_description[:10] + "...") if g.gift_description else "Gift"

        results.append(MatchResult(
            giver_name=g.name,
            giver_wechat=g.wechat,
            receiver_name=r.name,
            receiver_wechat=r.wechat,
            gift_summary=gift_name,
            match_reason=reason
        ))
        
    return results

# =========================================================
#  Main Entrypoint
# =========================================================

def solve_gift_circle(participants: List[Participant]) -> List[MatchResult]:
    if len(participants) < 2:
        return []
    # 1. 获取分数
    score_matrix = get_numeric_score_matrix(participants)
    # 2. 算法求解
    best_chain_indices = solve_with_memetic_algorithm(len(participants), score_matrix)
    # 3. 生成文案
    final_results = generate_stories_for_chain(best_chain_indices, participants)
    return final_results