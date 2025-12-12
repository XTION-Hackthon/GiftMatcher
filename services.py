import json
import random
import time
from typing import Dict, List, Tuple

from fastapi import HTTPException
from openai import OpenAI

from config import settings
from models import MatchResult, Participant

# 初始化 AI
client = OpenAI(api_key=settings.API_KEY, base_url=settings.BASE_URL)

# =========================================================
#  Part 1: AI 语义分析 (带安全校验)
# =========================================================


def get_ai_score_matrix(participants: List[Participant]) -> List[Dict]:
    """
    第一阶段：AI 语义分析
    """
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

        content = response.choices[0].message.content
        if not content:
            print("Warning: AI returned empty content.")
            return []

        result = json.loads(content)
        return result.get("matches", [])

    except Exception as e:
        print(f"AI Error: {e}")
        return []


# =========================================================
#  Part 2: 自适应混合模因算法 (Memetic Algorithm)
#  算法核心逻辑：GA (全局) + Local Search (局部)
# =========================================================


class Individual:
    def __init__(self, chain: List[int], score: int):
        self.chain = chain
        self.score = score


def calc_score(chain: List[int], weights: List[List[int]], n: int) -> int:
    """O(N) 计算链条总分"""
    s = 0
    for i in range(n):
        # chain[i] -> chain[i+1]
        s += weights[chain[i]][chain[(i + 1) % n]]
    return s


def local_search(chain: List[int], weights: List[List[int]], n: int) -> Individual:
    """
    【局部改良】Swap Mutation 变种
    尝试交换任意两个节点，如果分数变高就保留
    """
    current_chain = chain[:]
    current_score = calc_score(current_chain, weights, n)

    # 限制最大尝试次数，防止在平局情况下死循环
    MAX_IMPROVE_STEPS = 50

    improved = True
    step = 0

    while improved and step < MAX_IMPROVE_STEPS:
        improved = False
        step += 1

        # 尝试交换 i 和 j
        for i in range(n):
            for j in range(i + 1, n):
                # 模拟交换
                current_chain[i], current_chain[j] = current_chain[j], current_chain[i]
                new_score = calc_score(current_chain, weights, n)

                if new_score > current_score:
                    current_score = new_score
                    improved = True
                    # 贪心策略：一旦发现更好的，立刻锁定，进入下一轮大循环
                    # 这样比遍历完所有可能性更快
                    break
                else:
                    # 没变好，换回去
                    current_chain[i], current_chain[j] = (
                        current_chain[j],
                        current_chain[i],
                    )

            if improved:
                break

    return Individual(current_chain, current_score)


def crossover_ox1(
    parent1: Individual, parent2: Individual, weights: List[List[int]], n: int
) -> Individual:
    """
    【繁衍】顺序交叉算子 (Order Crossover, OX1)
    比简单的填充更安全，能保证生成的绝对是合法排列
    """
    if n < 3:
        # 如果人数太少，没法切片，直接返回变异后的父亲
        return local_search(parent1.chain, weights, n)

    # 1. 随机选择两个切点
    cx_point1 = random.randint(0, n - 2)
    cx_point2 = random.randint(cx_point1 + 1, n - 1)

    child_chain = [-1] * n

    # 2. 继承父代1的中间段
    child_chain[cx_point1:cx_point2] = parent1.chain[cx_point1:cx_point2]

    # 3. 用父代2的基因填补剩余空位 (保持父代2的相对顺序)
    # 获取父代2中所有不在 child_chain 里的元素
    p1_segment_set = set(child_chain[cx_point1:cx_point2])
    available_genes = [x for x in parent2.chain if x not in p1_segment_set]

    # 填补
    current_gene_idx = 0
    for i in range(n):
        if child_chain[i] == -1:
            child_chain[i] = available_genes[current_gene_idx]
            current_gene_idx += 1

    # 4. 生下来的孩子立刻进行“教育”
    return local_search(child_chain, weights, n)


def solve_with_memetic_algorithm(n: int, weights: List[List[int]]) -> List[int]:
    """算法主入口"""

    # 参数配置
    POP_SIZE = 40  # 种群大小
    GENERATIONS = 80  # 迭代代数
    ELITISM = 5  # 精英保留数

    # 1. 初始化种群
    population = []

    # 为了保证起跑线，先生成一批随机解并立刻优化
    for _ in range(POP_SIZE):
        chain = list(range(n))
        random.shuffle(chain)
        population.append(local_search(chain, weights, n))

    # 排序
    population.sort(key=lambda x: x.score, reverse=True)
    best_global = population[0]

    # 2. 进化循环
    no_improvement_count = 0

    for gen in range(GENERATIONS):
        new_pop = []

        # A. 精英保留
        new_pop.extend(population[:ELITISM])

        # B. 繁衍
        while len(new_pop) < POP_SIZE:
            # 锦标赛选择：随机选3个，挑最好的做父母
            candidates = random.sample(population, min(3, len(population)))
            p1 = max(candidates, key=lambda x: x.score)
            candidates = random.sample(population, min(3, len(population)))
            p2 = max(candidates, key=lambda x: x.score)

            child = crossover_ox1(p1, p2, weights, n)
            new_pop.append(child)

        # C. 更新种群
        population = new_pop
        population.sort(key=lambda x: x.score, reverse=True)

        # 记录最优
        current_best = population[0]
        if current_best.score > best_global.score:
            best_global = current_best
            no_improvement_count = 0
        else:
            no_improvement_count += 1

        # D. 逃逸机制 (如果 15 代都没有进步，说明陷入局部最优)
        if no_improvement_count > 15:
            # 引入"鲶鱼"：替换掉后 30% 的人口为纯随机新个体
            replace_idx = int(POP_SIZE * 0.7)
            for i in range(replace_idx, POP_SIZE):
                chain = list(range(n))
                random.shuffle(chain)
                population[i] = local_search(chain, weights, n)
            no_improvement_count = 0  # 重置计数器

    return best_global.chain


# =========================================================
#  Part 3: 业务调度入口
# =========================================================


def solve_gift_circle(
    participants: List[Participant], matches: List[Dict]
) -> List[MatchResult]:
    """
    主调度函数 (兼容无AI情况)
    """
    p_ids = [p.id for p in participants]
    n = len(p_ids)

    # 1. 映射 ID -> 0..n-1
    idx_map = {pid: i for i, pid in enumerate(p_ids)}

    # 2. 构建权重矩阵
    # 默认全0
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

    # 3. 运行算法
    if n > 1:
        # 这里是核心算法调用
        path_indices = solve_with_memetic_algorithm(n, weights)
    else:
        path_indices = [0]  # 只有一个人，虽然前端应该拦截

    # 4. 组装结果
    results = []
    p_map = {p.id: p for p in participants}

    for i in range(n):
        u_idx = path_indices[i]
        v_idx = path_indices[(i + 1) % n]  # 闭环连接

        # 查原始数据
        data = raw_data_map.get((u_idx, v_idx))

        giver = p_map[p_ids[u_idx]]
        receiver = p_map[p_ids[v_idx]]

        # 兜底逻辑
        if not data:
            match_reason = (
                "由于 AI 服务暂时不可用，系统已自动为您随机匹配最有缘的伙伴。"
            )
            # 尝试截取描述
            desc = giver.gift_description
            gift_summary = (
                (desc[:15] + "...") if desc and len(desc) > 15 else (desc or "神秘礼物")
            )
        else:
            _, match_reason, gift_summary = data

        results.append(
            MatchResult(
                giver_name=giver.name,
                giver_wechat=giver.wechat,
                receiver_name=receiver.name,
                receiver_wechat=receiver.wechat,
                gift_summary=gift_summary,
                match_reason=match_reason,
            )
        )

    return results
