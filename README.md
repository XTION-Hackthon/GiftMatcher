# 智能礼物交换系统接口文档

本项目是一个基于大语言模型（LLM）与混合模因算法（Memetic Algorithm）的礼物交换匹配系统，旨在解决多人场景下的礼物分配与满意度优化问题。

## 接口说明

- **接口地址**: `http://<服务器IP>:8000/match`
- **请求方式**: `POST`
- **数据格式**: `application/json`

### 1. 请求参数

前端需提交包含所有参与者信息的 JSON 数组。

**字段说明**：
- `gift_description`: 用户填写的礼物自然语言描述。
- `quiz_data`: 用户填写的性格问卷数据。

**请求示例**:

```json
[
  {
    "id": "u001",
    "name": "User A",
    "wechat": "user_a_wechat",
    "mbti": "ENTP",
    "gift_description": "微型方舟反应堆模型，虽然不能发电，但在夜里发蓝光，具有赛博朋克风格。",
    "quiz_data": [
      { "question_text": "周末安排", "selected_option": "B. 在实验室搞科研" }
    ]
  },
  {
    "id": "u002",
    "name": "User B",
    "wechat": "user_b_wechat",
    "mbti": "ISFJ",
    "gift_description": "二战复古素描本，附带一套专业炭笔。",
    "quiz_data": [
      { "question_text": "周末安排", "selected_option": "C. 去看画展" }
    ]
  }
]
```

### 2. 返回结果

后端返回一个排序好的链表 (`chain`)，形成闭环结构（如 A -> B -> C -> A）。

**返回示例**:

```json
{
  "chain": [
    {
      "giver_name": "User A",
      "giver_wechat": "user_a_wechat",
      "receiver_name": "User B",
      "receiver_wechat": "user_b_wechat",
      "gift_summary": "方舟反应堆模型",
      "match_reason": "虽然风格迥异，但这能带给接收者从未体验过的科技感，是一次打破常规的尝试。"
    },
    {
      "giver_name": "User B",
      "giver_wechat": "user_b_wechat",
      "receiver_name": "User A",
      "receiver_wechat": "user_a_wechat",
      "gift_summary": "复古素描本",
      "match_reason": "ENTP 内心其实渴望平静，这本素描本能帮助他记录那些稍纵即逝的灵感。"
    }
  ],
  "total_participants": 2
}
```

---

## 快速启动

### 环境依赖

需安装 Python 3.8+ 及以下依赖库：

```bash
pip install fastapi uvicorn openai pydantic python-dotenv
```

### 启动服务

```bash
python run.py
```

启动后：
- 接口地址: `http://localhost:8000/match`
- 在线文档: `http://localhost:8000/docs`

---

## 技术架构详解

系统采用“关注点分离”原则，将非结构化数据处理流程拆解为三个独立阶段，结合启发式算法进行求解。

### 阶段一：数值评分 (Scoring Phase)

**目标**：将非结构化文本转化为高鲁棒性的数值权重矩阵。

- **逻辑**：LLM 仅负责计算匹配度评分 (0-100)，不生成任何文本理由。
- **实现**：
  - 使用 `Pydantic` 进行严格的数据结构校验。
  - 仅输出 `Receiver_ID` 与 `Score` 的对应关系。
  - **优势**：降低 Token 消耗，避免自然语言生成带来的格式解析错误。

### 阶段二：算法求解 (Optimization Phase)

**目标**：在数值矩阵中寻找全局满意度最高的哈密顿回路 (Hamiltonian Cycle)。

- **算法**：自适应混合模因算法 (Adaptive Memetic Algorithm)。
- **核心机制**：
  1.  **OX1 顺序交叉**：从数学层面保证生成的子代为合法的环形排列（无重复、无遗漏）。
  2.  **局部搜索 (2-Opt)**：对生成的子代进行局部优化，通过交换节点位置提升总分。
  3.  **动态逃逸**：当种群陷入局部最优超过一定代数时，引入随机个体以跳出局部极值。

### 阶段三：文案生成 (Generation Phase)

**目标**：为确定的匹配关系生成解释文案。

- **逻辑**：算法已确定赠送关系，此阶段仅进行文本生成。
- **实现**：提取最终链条中的 N 对关系，批量请求 LLM 生成匹配理由。
- **优势**：实现逻辑解耦，即使文案生成失败，也不影响核心匹配结果的准确性。

---

## 数据流转示例

以 3 位用户（A、B、C）为例：

### 1. 输入处理
接收包含 3 人信息的 JSON 列表。

### 2. 评分矩阵构建
系统分析性格与礼物匹配度，输出数值矩阵（忽略对角线）：

| (收) \ (送) | User A | User B | User C |
| :--- | :---: | :---: | :---: |
| **User A** | 0 | 30 | 95 |
| **User B** | 40 | 0 | 60 |
| **User C** | 90 | 50 | 0 |

### 3. 路径规划
算法寻找最大权重的闭环路径。
- 路径 1: A->B->C->A (总分: 40+50+95 = 185)
- 路径 2: A->C->B->A (总分: 90+60+30 = 180)

**选定路径 1**：`User A -> User B -> User C -> User A`

### 4. 结果生成
系统请求 LLM 为以下配对生成文案：
1. A (科技礼物) -> B (保守性格)
2. B (艺术礼物) -> C (感性性格)
3. C (趣味礼物) -> A (探索性格)

最终输出包含完整文案的 JSON 结果。

---

## 系统稳定性设计

1.  **数据类型校验**
    利用 `Pydantic` 模型在阶段一拦截格式错误的数据。若 LLM 返回格式有误，该条目将被丢弃并填入默认分值，防止程序崩溃。

2.  **约束控制**
    - **逻辑层**：矩阵对角线强制置零。
    - **算法层**：OX1 交叉算子保证排列中无重复节点，杜绝自环现象。

3.  **降级策略**
    - **评分失败**：填入默认分值 (5分)，依赖算法寻找次优解。
    - **文案失败**：使用预设的通用文案替代，确保前端展示完整。