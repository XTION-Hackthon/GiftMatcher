import json
import logging
import random
import re
import time
import statistics
from typing import Dict, List, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from config import settings
from models import MatchResult, Participant

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.API_KEY, base_url=settings.BASE_URL)

#MARK: --- Data Structures ---

class StoryItem(BaseModel):
    giver_id: str
    receiver_id: str
    match_reason: str
    gift_short_name: str

#MARK: --- Helpers ---

def has_valid_mbti(mbti: str) -> bool:
    if not mbti: return False
    return len(mbti.strip()) == 4

def get_proxy_id(index: int) -> str:
    return f"U{index}"

def parse_proxy_id(proxy_id: str) -> int:
    try:
        clean = re.sub(r"[^0-9]", "", str(proxy_id))
        return int(clean)
    except:
        return -1

def print_section_header(title: str):
    print(f"\n{'='*20} [ {title} ] {'='*20}")

#MARK: --- Phase 1: Parallel Regex Scoring ---

def fetch_scores_for_receiver(
    r_idx: int, 
    receiver: Participant, 
    all_gifts_text: str, 
    n_participants: int,
    max_retries: int = 3
) -> Tuple[int, Dict[int, int]]:
    
    r_pid = get_proxy_id(r_idx)
    # 构建画像
    quiz_summary = ", ".join([q.selected_option for q in receiver.quiz_data])
    mbti_info = receiver.mbti if has_valid_mbti(receiver.mbti) else "N/A"
    receiver_desc = f"ID: {r_pid} | Name: {receiver.name} | MBTI: {mbti_info} | Habits: {quiz_summary}"

    system_prompt = f"""
You are a Match Scoring Engine.
Task: Rate compatibility (0-100) for ONE Receiver against ALL Gifts.
Receiver: {receiver_desc}
Gifts List:
{all_gifts_text}
OUTPUT RULES:
1. Rate ALL {n_participants} gifts.
2. Format: "GiftID Score" (e.g., "U0 85", "U1: 20").
3. NO JSON. NO MARKDOWN. Just a simple list.
"""

    for attempt in range(max_retries):
        scores = {}
        try:
            response = client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Output scores list now."}
                ],
                temperature=0.1 + (0.1 * attempt),
            )
            content = response.choices[0].message.content
            
            # 暴力正则提取
            matches = re.findall(r"U(\d+)\D+(\d{1,3})", content)
            for g_id_str, score_str in matches:
                try:
                    g_idx = int(g_id_str)
                    val = int(score_str)
                    if 0 <= val <= 100 and 0 <= g_idx < n_participants:
                        scores[g_idx] = val
                except: continue
            
            # 成功判定
            if len(scores) >= n_participants // 2:
                return r_idx, scores
            
            logger.warning(f"⚠️  [Retry {attempt+1}] {receiver.name} (U{r_idx}): Got only {len(scores)}/{n_participants} scores.")
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"❌ [Error] {receiver.name}: {e}")
            time.sleep(1)

    return r_idx, {}

def get_numeric_score_matrix(participants: List[Participant]) -> List[List[int]]:
    n = len(participants)
    DEFAULT_LOW_SCORE = 30
    matrix = [[DEFAULT_LOW_SCORE] * n for _ in range(n)] 
    for i in range(n): matrix[i][i] = 0 

    # 准备礼物文本
    gifts_lines = []
    for idx, p in enumerate(participants):
        pid = get_proxy_id(idx)
        clean_desc = p.gift_description.replace("\n", " ")[:50]
        gifts_lines.append(f"{pid} {clean_desc}")
    all_gifts_text = "\n".join(gifts_lines)
    
    print_section_header(f"Phase 1: Scoring {n} Participants")
    
    MAX_WORKERS = 5
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_idx = {
            executor.submit(fetch_scores_for_receiver, i, participants[i], all_gifts_text, n): i 
            for i in range(n)
        }
        
        completed = 0
        for future in as_completed(future_to_idx):
            r_idx, scores = future.result()
            completed += 1
            name = participants[r_idx].name
            
            user_scores_vals = []
            for g_idx, score in scores.items():
                if g_idx != r_idx:
                    matrix[g_idx][r_idx] = score
                    user_scores_vals.append(score)
            
            avg_score = round(statistics.mean(user_scores_vals)) if user_scores_vals else 0
            count = len(user_scores_vals)
            target = n - 1
            
            if count >= target: status = "✅ OK "
            elif count >= target * 0.8: status = "⚠️ Good"
            else: status = "❌ Fail"
            
            print(f"   [{completed:2d}/{n}] {name[:10]:<10} | {count:2d}/{target} scores | Avg: {avg_score:3d} | {status}")

    duration = time.time() - start_time
    
    # --- 矩阵统计 (排除对角线) ---
    valid_scores = []
    for r in range(n):
        for c in range(n):
            if r != c: # 排除对角线
                val = matrix[r][c]
                # 统计所有非默认分、非0分（0是自环，30是默认）
                if val != DEFAULT_LOW_SCORE and val != 0:
                    valid_scores.append(val)
    
    filled_count = len(valid_scores)
    total_slots = n * (n - 1) # 不含对角线的总格子数
    global_avg = statistics.mean(valid_scores) if valid_scores else 0
    
    print("-" * 60)
    print(f"📊 Matrix Stats (Excluding Self-Diagonal):")
    print(f"   - Time Taken: {duration:.1f}s")
    print(f"   - Filled:     {filled_count}/{total_slots} ({(filled_count/total_slots)*100:.1f}%)")
    print(f"   - Global Avg: {global_avg:.1f}")
    if filled_count < total_slots:
        print(f"   - Note: Unfilled slots use default score: {DEFAULT_LOW_SCORE}")
    print("-" * 60)

    # --- 打印完整矩阵 (Compact View) ---
    print("\n   [Full Score Matrix]")
    print("   Rows = Givers, Cols = Receivers")
    print("   " + " ".join([f"U{i:<2}" for i in range(n)])) # Header
    for r in range(n):
        row_str = " ".join([f"{val:3d}" if val != 0 else "  -" for val in matrix[r]])
        print(f"U{r:<2} {row_str}")
    print("\n")

    return matrix

#MARK: --- Phase 2: Memetic Algorithm ---

class Individual:
    def __init__(self, chain: List[int], score: int):
        self.chain = chain
        self.score = score

def calc_score(chain, weights, n):
    return sum(weights[chain[i]][chain[(i + 1) % n]] for i in range(n))

def local_search(chain, weights, n):
    curr = chain[:]
    best_s = calc_score(curr, weights, n)
    for _ in range(50):
        improved = False
        for i in range(n):
            for j in range(i+1, n):
                curr[i], curr[j] = curr[j], curr[i]
                new_s = calc_score(curr, weights, n)
                if new_s > best_s: best_s = new_s; improved = True; break
                else: curr[i], curr[j] = curr[j], curr[i]
        if not improved: break
    return Individual(curr, best_s)

def crossover_ox1(p1, p2, weights, n):
    if n<3: return local_search(p1.chain, weights, n)
    cx1, cx2 = sorted(random.sample(range(n), 2))
    child = [-1]*n
    child[cx1:cx2] = p1.chain[cx1:cx2]
    avail = [x for x in p2.chain if x not in child[cx1:cx2]]
    curr=0
    for i in range(n):
        if child[i]==-1: child[i]=avail[curr]; curr+=1
    return local_search(child, weights, n)

def solve_with_memetic_algorithm(n: int, weights: List[List[int]]) -> List[int]:
    if n < 2: return [0] if n==1 else []
    
    print_section_header("Phase 2: Memetic Algorithm")
    
    POP_SIZE = 40
    GENERATIONS = 50
    
    pop = [local_search(random.sample(range(n), n), weights, n) for _ in range(POP_SIZE)]
    pop.sort(key=lambda x:x.score, reverse=True)
    best_global = pop[0]
    initial_score = best_global.score
    
    no_imp = 0
    for gen in range(GENERATIONS):
        new_pop = pop[:5]
        while len(new_pop) < POP_SIZE:
            p1 = max(random.sample(pop, 3), key=lambda x:x.score)
            p2 = max(random.sample(pop, 3), key=lambda x:x.score)
            new_pop.append(crossover_ox1(p1, p2, weights, n))
        pop = new_pop
        pop.sort(key=lambda x:x.score, reverse=True)
        if pop[0].score > best_global.score:
            best_global = pop[0]; no_imp = 0
        else: no_imp += 1
        if no_imp > 15: 
            pop[10:] = [local_search(random.sample(range(n), n), weights, n) for _ in range(30)]
            no_imp = 0

    print(f"   Initial Score: {initial_score} -> Final Score: {best_global.score}")
    print(f"   Avg Compatibility: {best_global.score / n:.1f} / 100")
    
    return best_global.chain

#MARK: --- Phase 3: Story Generation ---

def generate_single_backup_reason(giver, receiver) -> Dict:
    try:
        quiz_summary = ", ".join([q.selected_option for q in receiver.quiz_data])
        prompt = f"""
Input: 
- Gift: "{giver.gift_description}" (from {giver.name})
- Receiver: {receiver.name} (Habits: {quiz_summary})
Task: Write a short, warm match reason in Chinese.
Rules:
1. NO robotic logic ("Because you chose A").
2. NO IDs (U0, U1).
3. Output JSON: {{ "match_reason": "...", "gift_short_name": "..." }}
"""
        response = client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except:
        return {"match_reason": "这是一份充满心意的礼物，希望能点亮你的生活。", "gift_short_name": "神秘礼物"}

def generate_stories_for_chain(
    chain_indices: List[int], 
    participants: List[Participant],
    score_matrix: List[List[int]] 
) -> List[MatchResult]:
    
    n = len(participants)
    print_section_header(f"Phase 3: Writing Stories for {n} Pairs")
    
    # --- 打印链条可视化 ---
    chain_names = [participants[i].name for i in chain_indices]
    print("🔗 [Matching Chain Visualization]")
    chain_str = " -> ".join(chain_names) + " -> " + chain_names[0]
    print(f"   {chain_str}\n")
    
    results = []
    pairs = []
    for i in range(n):
        g_idx = chain_indices[i]
        r_idx = chain_indices[(i + 1) % n]
        pairs.append((g_idx, r_idx))
    
    BATCH_SIZE = 5
    story_map = {} 
    
    for i in range(0, n, BATCH_SIZE):
        batch = pairs[i : i + BATCH_SIZE]
        context_lines = []
        for (g_idx, r_idx) in batch:
            g = participants[g_idx]
            r = participants[r_idx]
            quiz_vibe = ", ".join([q.selected_option for q in r.quiz_data])
            mbti_str = f"MBTI:{r.mbti}" if has_valid_mbti(r.mbti) else ""
            line = (
                f"Link: GiverID={get_proxy_id(g_idx)} (Name: {g.name}, Gift: {g.gift_description}) "
                f"-> ReceiverID={get_proxy_id(r_idx)} (Name: {r.name}, Traits: {mbti_str}, Habits: {quiz_vibe})"
            )
            context_lines.append(line)
        
        system_prompt = """
You are a warm Gift Curator.
Task: Write a personalized match reason (1-2 sentences) in Chinese.
WRITING RULES:
1. **Natural & Warm**: Interpret their lifestyle.
2. **NO Privacy Leaks**: Never say "Because you chose Option A".
3. **NO Internal IDs**: Use Real Names.
Output Format (JSON):
{"stories": [{"giver_id": "U0", "receiver_id": "U1", "match_reason": "...", "gift_short_name": "..."}]}
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
            raw = json.loads(response.choices[0].message.content)
            if "stories" in raw:
                for item in raw["stories"]:
                    try:
                        story = StoryItem(**item)
                        g_res = parse_proxy_id(story.giver_id)
                        r_res = parse_proxy_id(story.receiver_id)
                        if g_res != -1 and r_res != -1:
                            story_map[(g_res, r_res)] = story
                    except: continue
        except Exception as e:
            logger.error(f"Story Batch Error: {e}")

    # --- 完整输出文案 ---
    print("📝 [Final Match Stories]")
    
    for (g_idx, r_idx) in pairs:
        g = participants[g_idx]
        r = participants[r_idx]
        
        story = story_map.get((g_idx, r_idx))
        if story:
            reason = story.match_reason
            gift_name = story.gift_short_name
        else:
            bk = generate_single_backup_reason(g, r)
            reason = bk.get("match_reason", "Unique match.")
            gift_name = bk.get("gift_short_name", g.gift_description[:10])

        # 卡片式打印，不截断
        print(f"   ┌── {g.name} (Gift: {gift_name})")
        print(f"   └──► {r.name}")
        print(f"       Reason: {reason}")
        print("   " + "-"*40)

        results.append(MatchResult(
            giver_name=g.name,
            giver_wechat=g.wechat,
            receiver_name=r.name,
            receiver_wechat=r.wechat,
            gift_summary=gift_name,
            match_reason=reason
        ))
        
    return results

#MARK: --- Main ---

def solve_gift_circle(participants: List[Participant]) -> List[MatchResult]:
    if len(participants) < 2: return []
    
    score_matrix = get_numeric_score_matrix(participants)
    best_chain = solve_with_memetic_algorithm(len(participants), score_matrix)
    final_results = generate_stories_for_chain(best_chain, participants, score_matrix)
    
    return final_results