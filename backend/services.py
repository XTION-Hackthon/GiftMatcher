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

#MARK: 数据结构校验 (Pydantic)

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

#MARK: Helper: 检查是否有有效的 MBTI

def has_valid_mbti(mbti: str) -> bool:
    """检查 MBTI 是否有效（非空且不是占位符）"""
    if not mbti:
        return False
    mbti_upper = mbti.upper().strip()
    # 无效的 MBTI 值
    invalid_values = {"", "无", "未知", "不知道", "没有", "N/A", "NA", "NONE", "NULL", "-", "未填写"}
    if mbti_upper in invalid_values:
        return False
    # 检查是否是有效的 MBTI 类型格式（4个字母）
    valid_mbti_types = {
        "INTJ", "INTP", "ENTJ", "ENTP",
        "INFJ", "INFP", "ENFJ", "ENFP",
        "ISTJ", "ISFJ", "ESTJ", "ESFJ",
        "ISTP", "ISFP", "ESTP", "ESFP"
    }
    return mbti_upper in valid_mbti_types


#MARK: Phase 1: 纯数值评分 (The Mathematician)

def get_numeric_score_matrix(participants: List[Participant]) -> List[List[int]]:
    n = len(participants)
    p_ids = [p.id for p in participants]
    
    # 默认低分设为 30
    DEFAULT_LOW_SCORE = 30
    matrix = [[DEFAULT_LOW_SCORE] * n for _ in range(n)] 
    
    for i in range(n):
        matrix[i][i] = 0 # 自环永远为 0

    gifts_context = "\n".join([f"ID: {p.id} | Gift: {p.gift_description}" for p in participants])
    BATCH_SIZE = 5
    
    logger.info(f"Phase 1: Calculating scores for {n} users...")

    for i in range(0, n, BATCH_SIZE):
        batch = participants[i : i + BATCH_SIZE]
        
        # 根据是否有 MBTI 构建不同的上下文
        receivers_context_lines = []
        for p in batch:
            quiz_str = "|".join([f"{q.question_text[:10]}..->{q.selected_option}" for q in p.quiz_data])
            if has_valid_mbti(p.mbti):
                receivers_context_lines.append(f"ID: {p.id} | MBTI: {p.mbti} | Quiz: {quiz_str}")
            else:
                receivers_context_lines.append(f"ID: {p.id} | MBTI: [未提供] | Quiz: {quiz_str}")
        receivers_context = "\n".join(receivers_context_lines)

        # 【升级】评分权重：根据是否有 MBTI 动态调整
        # 如果有 MBTI: 50% MBTI + 50% Quiz
        # 如果无 MBTI: 100% Quiz（生活方式匹配）
        system_prompt = """
You are a Dual-Core Matching Engine.
Input: Receivers (MBTI + Quiz) and Gifts.
Task: Rate compatibility (0-100).

SCORING WEIGHTS:
1. **For receivers WITH MBTI**:
   - 50% MBTI RESONANCE: Does the gift fit their cognitive functions? (e.g., INTJ likes efficiency, ESFP likes sensory experiences).
   - 50% LIFESTYLE FIT: Does the gift specifically fit their Quiz Answers (Weekend habits/Vacation preferences)?
2. **For receivers WITHOUT MBTI (marked as [未提供])**:
   - 100% LIFESTYLE FIT: Focus entirely on Quiz Answers to determine compatibility.
   - Analyze their preferences, habits, and lifestyle from quiz responses.
3. **SCORING GUIDE**:
   - **90-100**: Perfect Storm. Excellent fit based on available data.
   - **70-89**: Strong match. Good alignment with preferences.
   - **< 60**: Weak match.
4. Output JSON: {"results": [{"receiver_id": "...", "scores": [{"gift_from_id": "...", "score": 88}, ...]}]}
5. Return Top 5 matches per receiver.
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

    # DEBUG: 打印评分矩阵
    print("\n" + "="*40)
    print("🔍 [DEBUG] Phase 1 - Score Matrix:")
    print(f"   (Rows=Givers, Cols=Receivers, Default={DEFAULT_LOW_SCORE})")
    print(f"   Format: [Score_to_User0, Score_to_User1, ...]")
    for idx, row in enumerate(matrix):
        name = participants[idx].name[:10].ljust(10)
        print(f"   {name}: {row}")
    print("="*40 + "\n")

    return matrix

#MARK: Phase 2: 自适应混合模因算法 (The Strategist)

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
    MAX_STEPS = 50 
    
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
                    break 
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
    if n < 2: return [0] if n==1 else []

    POP_SIZE = 40
    GENERATIONS = 50 
    ELITISM = 5
    
    population = []
    for _ in range(POP_SIZE):
        c = list(range(n))
        random.shuffle(c)
        population.append(local_search(c, weights, n))
    
    population.sort(key=lambda x: x.score, reverse=True)
    best_global = population[0]
    no_imp = 0
    
    for gen in range(GENERATIONS):
        new_pop = population[:ELITISM]
        while len(new_pop) < POP_SIZE:
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
            
        if no_imp > 15:
            replace_idx = int(POP_SIZE * 0.7)
            for i in range(replace_idx, POP_SIZE):
                c = list(range(n))
                random.shuffle(c)
                population[i] = local_search(c, weights, n)
            no_imp = 0
            
    return best_global.chain

#MARK: Phase 3: 纯文案生成 (The Writer)

def generate_single_backup_reason(giver: Participant, receiver: Participant) -> Dict:
    logger.info(f"⚡ Triggering backup generation for {giver.name} -> {receiver.name}")
    
    # 根据是否有 MBTI 构建不同的提示词
    has_mbti = has_valid_mbti(receiver.mbti)
    if has_mbti:
        receiver_info = f"MBTI: {receiver.mbti}, Quiz: {[q.selected_option for q in receiver.quiz_data]}"
        mbti_rule = '1. **INTEGRATE MBTI & DETAILS**: You CAN mention their MBTI (e.g. "As an ENTP..."), but you MUST connect it to specific gift features and quiz habits.'
    else:
        receiver_info = f"Quiz: {[q.selected_option for q in receiver.quiz_data]}"
        mbti_rule = '1. **FOCUS ON LIFESTYLE**: Since no MBTI is provided, focus entirely on their quiz answers and lifestyle preferences to explain the match.'
    
    prompt = f"""
Match: {giver.name} (Gift: {giver.gift_description}) -> {receiver.name} ({receiver_info})

Task: Write a match reason in Chinese.
CRITICAL RULES:
{mbti_rule}
2. **NO "ALTHOUGH...BUT..."**: Avoid adversative conjunctions. Use positive logic.
3. Output JSON: {{"match_reason": "...", "gift_short_name": "..."}}
"""
    try:
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Backup generation failed: {e}")
        return {
            "match_reason": "这是一次独特的跨界匹配，也许能带来意想不到的惊喜。", 
            "gift_short_name": giver.gift_description[:10]
        }

def generate_stories_for_chain(
    chain_indices: List[int], 
    participants: List[Participant],
    score_matrix: List[List[int]] 
) -> List[MatchResult]:
    
    n = len(participants)
    results = []
    pairs_to_generate = []
    
    total_chain_score = 0
    debug_pairs_str = []

    for i in range(n):
        giver_idx = chain_indices[i]
        receiver_idx = chain_indices[(i + 1) % n]
        
        score = score_matrix[giver_idx][receiver_idx]
        total_chain_score += score
        
        g_obj = participants[giver_idx]
        r_obj = participants[receiver_idx]
        
        pairs_to_generate.append({
            "giver": g_obj,
            "receiver": r_obj
        })
        debug_pairs_str.append(f"{g_obj.name}->{r_obj.name}(Score:{score})")

    print("\n" + "="*40)
    print(f"🔍 [DEBUG] Phase 3 - Final Chain Analysis")
    print(f"   Total Score: {total_chain_score}")
    print(f"   Avg Score: {total_chain_score / n:.1f}")
    print(f"   Details: {', '.join(debug_pairs_str)}")
    print("="*40 + "\n")
    
    BATCH_SIZE = 5
    logger.info(f"Phase 3: Generating stories for {n} pairs...")
    story_map = {}

    for i in range(0, n, BATCH_SIZE):
        batch_pairs = pairs_to_generate[i : i + BATCH_SIZE]
        context_lines = []
        for pair in batch_pairs:
            g, r = pair["giver"], pair["receiver"]
            quiz_str = "|".join([q.selected_option for q in r.quiz_data])
            # 根据是否有 MBTI 构建不同的上下文
            if has_valid_mbti(r.mbti):
                context_lines.append(
                    f"Pair: GiverID={g.id} (Gift: {g.gift_description}) -> ReceiverID={r.id} (MBTI: {r.mbti} | Quiz: {quiz_str})"
                )
            else:
                context_lines.append(
                    f"Pair: GiverID={g.id} (Gift: {g.gift_description}) -> ReceiverID={r.id} (MBTI: [未提供] | Quiz: {quiz_str})"
                )
        
        # 【升级】文案提示词：根据是否有 MBTI 动态调整
        system_prompt = """
You are an insightful Gift Curator.
Task: Write a clever, warm match reason (1-2 sentences, in Chinese).

WRITING RULES:
1. **FOR RECEIVERS WITH MBTI**: You CAN mention their MBTI type, but you MUST explain *how* that type interacts with the **Specific Gift Feature** and their **Quiz Habit**.
   - Bad: "You are an ENTP, so you will like this."
   - Good: "As an ENTP with a love for experiments, this Nixie Tube clock perfectly feeds your curiosity and fits your lab-style weekend."
2. **FOR RECEIVERS WITHOUT MBTI (marked as [未提供])**: Focus entirely on their quiz answers and lifestyle preferences. Do NOT mention MBTI at all.
   - Good: "Based on your love for cozy weekends at home, this warm blanket will be your perfect companion."
3. **NO ADVERSATIVE CONJUNCTIONS**: Do NOT use "虽然", "尽管", "但是". Use positive bridging logic.
4. Output JSON: {"stories": [{"giver_id": "...", "receiver_id": "...", "match_reason": "...", "gift_short_name": "..."}]}
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
            logger.error(f"Story generation batch failed: {e}")
            continue

    for pair in pairs_to_generate:
        g, r = pair["giver"], pair["receiver"]
        story = story_map.get((g.id, r.id))
        
        if story:
            reason = story.match_reason
            gift_name = story.gift_short_name
        else:
            backup_data = generate_single_backup_reason(g, r)
            reason = backup_data.get("match_reason", "Unique match")
            gift_name = backup_data.get("gift_short_name", g.gift_description[:15])

        results.append(MatchResult(
            giver_name=g.name,
            giver_wechat=g.wechat,
            receiver_name=r.name,
            receiver_wechat=r.wechat,
            gift_summary=gift_name,
            match_reason=reason
        ))
        
    return results

#MARK: Main Entrypoint

def solve_gift_circle(participants: List[Participant]) -> List[MatchResult]:
    if len(participants) < 2:
        return []
    
    score_matrix = get_numeric_score_matrix(participants)
    
    print(f"   >>> [DEBUG] Running Memetic Algorithm on {len(participants)}x{len(participants)} matrix...")
    best_chain_indices = solve_with_memetic_algorithm(len(participants), score_matrix)
    
    final_results = generate_stories_for_chain(best_chain_indices, participants, score_matrix)
    
    return final_results