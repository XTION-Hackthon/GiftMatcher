# 🎄 圣诞礼物交换系统

一个基于大语言模型（LLM）与混合模因算法（Memetic Algorithm）的智能礼物交换匹配系统。

## 项目简介

本系统旨在解决多人场景下的礼物分配与满意度优化问题。通过收集参与者的性格特征（MBTI）、问卷答案和礼物描述，利用 AI 进行智能匹配，确保每个人都能收到最适合自己的礼物。

## 项目结构

```
shengdan/
├── frontend/           # 前端项目
│   ├── index.html      # 主页面
│   ├── api/            # Flask API（提交数据到飞书）
│   ├── vercel.json     # Vercel 部署配置
│   ├── requirements.txt
│   └── *.png           # 图片资源
│
├── backend/            # 后端项目
│   ├── main.py         # FastAPI 主入口
│   ├── cli.py          # CLI 命令行工具
│   ├── services.py     # 核心匹配算法
│   ├── models.py       # 数据模型
│   ├── config.py       # 配置管理
│   ├── feishu_reader.py # 飞书表格读取
│   └── README.md       # 后端文档
│
├── .gitignore
└── README.md           # 本文件
```

## 工作流程

### 1. 数据收集阶段（前端）

1. 用户访问前端页面
2. 填写个人信息（姓名、邮箱、微信、MBTI）
3. 描述准备的礼物
4. 完成问卷调查
5. 提交数据 → 存入飞书多维表格

### 2. 匹配分析阶段（后端）

1. 运行 CLI 命令读取飞书表格数据
2. AI 分析每对参与者的匹配度（评分矩阵）
3. 混合模因算法寻找最优匹配链
4. AI 生成匹配理由文案
5. 输出最终匹配结果

## 快速开始

### 前端

```bash
cd frontend
pip install -r requirements.txt
python api/index.py
# 访问 http://localhost:5000
```

### 后端

```bash
cd backend
pip install fastapi uvicorn openai pydantic python-dotenv requests

# 方式一：启动 API 服务
python run.py

# 方式二：CLI 命令行模式
python cli.py fetch     # 仅读取飞书数据
python cli.py analyze   # 读取数据并运行匹配分析
```

## 技术架构

### 前端
- **UI**: HTML + TailwindCSS
- **API**: Flask + Flask-CORS
- **部署**: Vercel
- **数据存储**: 飞书多维表格

### 后端
- **框架**: FastAPI
- **AI**: OpenAI API（可配置其他兼容接口）
- **算法**: 混合模因算法（Memetic Algorithm）
- **数据读取**: 飞书开放平台 API

## 核心算法

系统采用三阶段处理流程：

1. **评分阶段**: LLM 计算每对参与者的匹配度（0-100分）
   - 50% MBTI 性格契合度
   - 50% 问卷行为细节匹配度

2. **优化阶段**: 混合模因算法寻找最优哈密顿回路
   - OX1 顺序交叉
   - 局部搜索优化
   - 动态逃逸机制

3. **文案阶段**: LLM 为确定的匹配关系生成解释文案

## 配置说明

### 后端环境变量（.env）

```bash
# AI 配置
AI_API_KEY=your_api_key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL_NAME=gpt-4

# 飞书配置
FEISHU_APP_TOKEN=xxx
FEISHU_TABLE_ID=xxx
FEISHU_TENANT_ACCESS_TOKEN=xxx
```

## 注意事项

- 飞书 `tenant_access_token` 有效期为 **2小时**，过期需重新获取
- 建议在所有用户提交完数据后再运行后端匹配分析
- 匹配算法需要至少 2 位参与者

## 许可证

MIT License
