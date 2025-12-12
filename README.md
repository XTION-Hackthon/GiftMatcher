# 接口文档

- **接口地址**: `http://<服务器IP>:8000/match`
- **请求方式**: `POST`
- **数据格式**: `application/json`

## 请求参数示例

前端需要把所有参与者的信息打包成一个数组发送过来。
**注意**：`gift_description` 直接传用户填写的长文本，`quiz_data` 传题目和选项的完整文字。

```json
[
  {
    "id": "user_01",
    "name": "钢铁侠",
    "email": "tony@stark.com",
    "wechat": "iron_man",
    "mbti": "ENTP",
    "gift_description": "我做了一个方舟反应堆模型，会发蓝光，虽然不能发电但摆在桌上非常赛博朋克。",
    "quiz_data": [
      {
        "question_text": "出门参加圣诞派对，你会选择哪条围巾搭配？",
        "selected_option": "D. 黑色机能风防风面罩围脖"
      },
      {
        "question_text": "周末一般怎么过？",
        "selected_option": "B. 在实验室搞科研"
      }
    ]
  },
  {
    "id": "user_02",
    "name": "美队",
    "email": "steve@usa.com",
    "wechat": "cap_america",
    "mbti": "ISFJ",
    "gift_description": "一本二战时期的素描本复刻版，包含一套专业绘画铅笔。",
    "quiz_data": [
      {
        "question_text": "出门参加圣诞派对，你会选择哪条围巾搭配？",
        "selected_option": "A. 纯灰色的羊绒围巾"
      },
      {
        "question_text": "周末一般怎么过？",
        "selected_option": "C. 去看画展"
      }
    ]
  }
]
```

## 返回结果示例

后端会返回一个排好序的链表 (`chain`)，前端按顺序展示即可。
`match_reason` 是 AI 结合性格和礼物生成的推荐理由。

```json
{
  "chain": [
    {
      "giver_name": "钢铁侠",
      "giver_wechat": "iron_man",
      "receiver_name": "美队",
      "receiver_wechat": "cap_america",
      "gift_summary": "方舟反应堆模型",
      "match_reason": "虽然美队喜好复古，但AI分析认为该模型具有极高的收藏价值..."
    },
    {
      "giver_name": "美队",
      "giver_wechat": "cap_america",
      "receiver_name": "钢铁侠",
      "receiver_wechat": "iron_man",
      "gift_summary": "素描本复刻版",
      "match_reason": "托尼其实内心细腻，素描本能帮助他记录灵感..."
    }
  ],
  "total_participants": 2
}
```

---

## 环境依赖

请确保安装 Python 3.8+，并安装以下库：

```bash
pip install fastapi uvicorn openai pydantic python-dotenv
```

## 启动服务

在根目录下运行：

```bash
python run.py
```

启动后：

- 接口地址: `http://localhost:8000/match`
- 在线文档: `http://localhost:8000/docs`

---

# 核心算法逻辑

本项目的核心挑战在于：如何在一个多人参与的礼物交换中，根据非结构化的性格描述，找到一条**全局满意度最高**且**闭环**的赠送链条。

我们将此问题建模为图论中的 **“最大权值哈密顿回路问题” (Maximum Weight Hamiltonian Cycle Problem)**。

## 1. 数学建模

我们将匹配过程抽象为一个**有向带权完全图 (Directed Weighted Complete Graph)** $G=(V, E)$：

- **节点 (Vertices)**: 每一个参赛者 $P$ 视为图中的一个节点。
- **边 (Edges)**: 任意两个人 $P_i$ 到 $P_j$ 的赠送关系视为一条有向边。
- **权重 (Weights)**: 边上的数值 $W_{ij}$ 代表 $P_j$ (收礼者) 对 $P_i$ (送礼者) 带来的礼物的**满意度分数 (0-100)**。
  - _注：权重的计算由 LLM 基于语义分析完成，且强制 $W_{ii} = 0$ (自己不能送自己)。_

**目标函数**：
寻找一个节点排列（路径）$\pi$，使得：

1.  **拓扑约束**：形成单一闭环 (A $\to$ B $\to$ C $\to$ ... $\to$ A)，确保每人送出一份且收且仅收到一份。
2.  **效用约束**：最大化路径上的总权重 $\sum W$。

## 2. 求解策略：随机重启启发式算法

由于寻找哈密顿回路属于 **NP-Hard** 问题，且全排列的时间复杂度为 $O(N!)$。当人数 $N > 15$ 时，暴力穷举在 API 请求的有限时间内不可行。

考虑到本项目场景中 $N$ 通常较小 ($N < 50$) 且对“绝对最优解”要求不严苛（“足够好”即可），我们放弃了复杂的精确解算法（如动态规划），采用了**随机重启爬山算法**。

### 算法具体步骤：

#### 步骤 1：构建 O(1) 查找表

将 AI 返回的稀疏或列表数据转换为哈希映射 (Hash Map)：
$$Map[(Receiver, Giver)] = Score$$
这确保了在计算路径总分时，查询任意两人的匹配分数为常数时间复杂度。

#### 步骤 2：随机拓扑生成 (Stochastic Generation)

利用 Fisher-Yates 洗牌算法（即 Python 的 `random.shuffle`）生成一个随机的参与者 ID 序列。

- 例如序列 `[A, C, B, D]` 隐式代表了环：$A \to C \to B \to D \to A$。
- 这一步保证了生成的解天然满足**“单一闭环”**的硬性约束，无需后续校验连通性。

#### 步骤 3：贪心评估与迭代 (Evaluation & Iteration)

我们设定一个迭代次数 $K$ (本项目设为 200-500 次)。在每一轮迭代中：

1.  生成一个新的随机序列。
2.  遍历序列，累加相邻节点之间的权重（即礼物满意度）。
3.  如果当前序列的总分 > 历史最高分，则更新全局最优解。

```python
# 伪代码逻辑
Best_Chain = None
Max_Score = -1

Loop K times:
    Chain = Shuffle(Participants)  # 随机生成一个环
    Current_Score = Sum( Weights(Chain[i] -> Chain[i+1]) )

    If Current_Score > Max_Score:
        Max_Score = Current_Score
        Best_Chain = Chain
```

## 3. 算法复杂度与性能

- **时间复杂度**: $O(K \cdot N)$
  - $N$ 为人数，$K$ 为迭代次数。
  - 由于 $K$ 是常数，算法随人数呈线性增长，计算极其迅速。
- **空间复杂度**: $O(N^2)$
  - 主要消耗在于存储 $N \times N$ 的分数矩阵。

## 4. 为什么不使用其他算法？

- **为什么不用贪心算法 (Pure Greedy)?**
  - 单纯的贪心（每次选当前分最高的边）极易形成**多个小孤立环**（如 A$\leftrightarrow$B 互换，C$\leftrightarrow$D 互换），而不是一个连接所有人的大环。
- **为什么不用匈牙利算法 (Hungarian Algorithm)?**
  - 匈牙利算法解决的是“二分图匹配”问题，它能保证总分最高，但**无法保证形成环状结构**。它可能会生成“A送给B，但B送给C...”这样的开环链条，导致有人没收到礼物。
- **结论**: 随机化算法是解决此类“带特定拓扑约束”的小规模优化问题的性价比之选。
