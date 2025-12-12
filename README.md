## 接口文档

- **接口地址**: `http://<服务器IP>:8000/match`
- **请求方式**: `POST`
- **数据格式**: `application/json`

### 请求参数示例

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

### 返回结果示例

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

### 环境依赖

请确保安装 Python 3.8+，并安装以下库：

```bash
pip install fastapi uvicorn openai pydantic python-dotenv
```

### 启动服务

在根目录下运行：

```bash
python run.py
```

启动后：

- 接口地址: `http://localhost:8000/match`
- 在线文档: `http://localhost:8000/docs`

---
