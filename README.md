# 🎄 圣诞礼物交换系统 - 前端

圣诞礼物交换系统的数据收集前端，用于收集参与者信息并提交到飞书多维表格。

## 项目简介

本系统用于收集参与者的性格特征（MBTI）、问卷答案和礼物描述信息，并将数据存储到飞书多维表格中。

## 项目结构

```
shengdan/
├── frontend/           # 前端项目
│   ├── index.html      # 主页面
│   ├── api/            # Flask API（提交数据到飞书）
│   │   └── index.py    # Flask 服务入口
│   ├── vercel.json     # Vercel 部署配置
│   ├── requirements.txt
│   └── images/         # 图片资源
│
├── vercel.json         # 根目录 Vercel 配置
├── .gitignore
└── README.md           # 本文件
```

## 功能说明

1. 用户访问前端页面
2. 填写个人信息（姓名、邮箱、微信、MBTI）
3. 描述准备的礼物
4. 完成问卷调查
5. 提交数据 → 存入飞书多维表格

## 快速开始

### 安装依赖

```bash
cd frontend
pip install -r requirements.txt
```

### 本地运行

```bash
python api/index.py
```

启动后访问: http://localhost:5000

## 技术架构

- **UI**: HTML + TailwindCSS + JavaScript
- **API**: Flask + Flask-CORS
- **部署**: Vercel
- **数据存储**: 飞书多维表格

## Vercel 部署

项目已配置 Vercel 部署，直接推送到 Git 仓库即可自动部署。

## 注意事项

- 飞书 `tenant_access_token` 会自动刷新，有效期为 2 小时
- 飞书配置信息在 `frontend/api/index.py` 中

## 许可证

MIT License
