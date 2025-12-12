import json
import random
import time
from typing import Dict, List

from fastapi import HTTPException
from openai import OpenAI

from config import settings
from models import MatchResult, Participant

# 初始化 AI
client = OpenAI(api_key=settings.API_KEY, base_url=settings.BASE_URL)


def get_ai_score_matrix(participants: List[Participant]) -> List[Dict]:
    """第一阶段：AI 语义分析 (保持不变)"""
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
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Data:\n{full_context}"},
            ],
            response_format={"type": "json_object"},
        )

        # 1. 先把内容取出来
        content = response.choices[0].message.content

        # 2. 只有当 content 不是 None 且不是空字符串时，才解析
        if not content:
            print("Warning: AI returned empty content.")
            return []

        # 3. 现在解析是安全的
        result = json.loads(content)
        return result.get("matches", [])
    except Exception as e:
        print(f"AI Error: {e}")
        return []


# =========================================================
#  核心算法：自适应混合模因算法 (Adaptive Memetic Algorithm)
#  结合了 GA (全局搜索) + LS (局部改良)
# =========================================================


class Individual:
    def __init__(self, chain, score):
        self.chain = chain
        self.score = score


def calc_score(chain, weights, n):
    """O(N) 快速计算链条总分"""
    s = 0
    for i in range(n):
        s += weights[chain[i]][chain[(i + 1) % n]]
    return s


def local_search(chain, weights, n):
    """
    【教育阶段】局部搜索 (2-Opt)
    利用文章结论：LS速度极快，用来快速改良子代
    """
    best_chain = chain[:]
    best_score = calc_score(chain, weights, n)
    improved = True

    # 为了速度，限制 LS 的最大迭代轮数
    limit = 50
    count = 0

    while improved and count < limit:
        improved = False
        count += 1
        # 尝试交换任意两点
        for i in range(n):
            for j in range(i + 1, n):
                # 模拟交换
                best_chain[i], best_chain[j] = best_chain[j], best_chain[i]
                new_score = calc_score(best_chain, weights, n)

                if new_score > best_score:
                    best_score = new_score
                    improved = True
                else:
                    # 撤销交换
                    best_chain[i], best_chain[j] = best_chain[j], best_chain[i]

    return Individual(best_chain, best_score)


def crossover(parent1, parent2, weights, n):
    """
    【繁衍阶段】PMX 交叉变种
    保留父代的部分优秀片段
    """
    # 随机选择片段
    start = random.randint(0, n - 2)
    end = random.randint(start + 1, n - 1)

    # 继承父代1的片段
    child_chain = [-1] * n
    child_chain[start:end] = parent1.chain[start:end]

    # 填充父代2的基因 (保持顺序)
    current_p2_idx = 0
    for i in range(n):
        if child_chain[i] == -1:
            while parent2.chain[current_p2_idx] in child_chain:
                current_p2_idx += 1
            child_chain[i] = parent2.chain[current_p2_idx]

    # 【关键创新】生下来的孩子立刻进行"教育"(局部搜索)
    return local_search(child_chain, weights, n)


def solve_with_memetic_algorithm(n, weights):
    """
    混合模因算法主流程
    """
    POP_SIZE = 50  # 种群大小 (不用太大，因为有LS加速)
    GENERATIONS = 100  # 迭代代数
    ELITISM = 10  # 精英保留数量

    # 1. 初始化种群 (50% 随机, 50% 贪婪)
    population = []

    # A. 随机个体
    for _ in range(POP_SIZE // 2):
        chain = list(range(n))
        random.shuffle(chain)
        # 即使是初始个体，也进行一次教育
        population.append(local_search(chain, weights, n))

    # B. 简单的贪婪生成 (保证起跑线高)
    # 这里简单起见，再生成一批随机并优化的
    for _ in range(POP_SIZE - len(population)):
        chain = list(range(n))
        random.shuffle(chain)
        population.append(local_search(chain, weights, n))

    # 按分数排序
    population.sort(key=lambda x: x.score, reverse=True)
    best_global = population[0]

    # 2. 进化循环
    for gen in range(GENERATIONS):
        new_pop = []

        # A. 精英策略：直接保留最好的 N 个
        new_pop.extend(population[:ELITISM])

        # B. 繁衍下一代
        while len(new_pop) < POP_SIZE:
            # 锦标赛选择父母 (从随机3个里选最好的)
            p1 = max(random.sample(population, 3), key=lambda x: x.score)
            p2 = max(random.sample(population, 3), key=lambda x: x.score)

            # 交叉 + 变异(内部包含了LS)
            child = crossover(p1, p2, weights, n)
            new_pop.append(child)

        # 更新种群
        population = new_pop
        population.sort(key=lambda x: x.score, reverse=True)

        # 记录最优
        if population[0].score > best_global.score:
            best_global = population[0]

        # 3. 逃逸机制 (如果连续 10 代最优解没变，且还没满分)
        # 简单实现：引入一批全新的随机血液
        if gen % 10 == 0:
            # 替换掉最差的 20%
            idx = int(POP_SIZE * 0.8)
            for i in range(idx, POP_SIZE):
                chain = list(range(n))
                random.shuffle(chain)
                population[i] = local_search(chain, weights, n)

    return best_global.chain


def solve_gift_circle(
    participants: List[Participant], matches: List[Dict]
) -> List[MatchResult]:
    if not matches:
        raise HTTPException(status_code=500, detail="AI 未返回数据")

    p_ids = [p.id for p in participants]
    n = len(p_ids)

    # 1. 映射 ID
    idx_map = {pid: i for i, pid in enumerate(p_ids)}

    # 2. 构建权重矩阵
    weights = [[0] * n for _ in range(n)]
    raw_data_map = {}

    for m in matches:
        u = idx_map.get(m["gift_from_id"])
        v = idx_map.get(m["receiver_id"])
        if u is not None and v is not None:
            weights[u][v] = m["score"]
            raw_data_map[(u, v)] = (
                m["score"],
                m.get("match_reason", ""),
                m.get("gift_short_name", "Gift"),
            )

    # 3. 运行混合模因算法
    if n > 1:
        path_indices = solve_with_memetic_algorithm(n, weights)
    else:
        path_indices = [0]

    # 4. 组装结果
    results = []
    p_map = {p.id: p for p in participants}

    for i in range(n):
        u_idx = path_indices[i]
        v_idx = path_indices[(i + 1) % n]

        data = raw_data_map.get((u_idx, v_idx))
        if not data:
            score, reason, gift = 0, "兜底匹配", "未知礼物"
        else:
            score, reason, gift = data

        giver = p_map[p_ids[u_idx]]
        receiver = p_map[p_ids[v_idx]]

        results.append(
            MatchResult(
                giver_name=giver.name,
                giver_wechat=giver.wechat,
                receiver_name=receiver.name,
                receiver_wechat=receiver.wechat,
                gift_summary=gift,
                match_reason=reason,
            )
        )

    return results
