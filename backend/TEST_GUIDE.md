# 测试指南

## 快速开始

### 1. 配置环境

复制配置模板并填写你的配置：

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件，填写必要的配置项。

### 2. 运行本地测试

```bash
python test_local.py
```

## 测试项目说明

### 测试1: 匹配算法测试（不发送邮件）

**目的**: 验证匹配算法是否正常工作，包括：
- 有MBTI和无MBTI的处理
- 评分矩阵生成
- 匹配链优化
- 文案生成

**操作**: 选择菜单选项 `1`

**预期结果**:
- 显示5位测试参与者信息
- 运行匹配算法（会调用AI API）
- 输出匹配结果和理由
- 无MBTI的参与者文案不应提及MBTI

### 测试2: 完整流程测试（匹配 + 邮件）

**目的**: 验证完整的匹配和邮件发送流程

**前置条件**:
- 已配置邮件服务（SMTP相关配置）
- 已在 `test_local.py` 中填写真实的测试邮箱地址

**操作**: 选择菜单选项 `2`

**预期结果**:
- 完成匹配算法
- 发送邮件到所有参与者
- 每人收到2封邮件：
  - 送礼通知（告知要送礼给谁）
  - 收礼通知（告知谁会送礼给自己）

### 测试3: 单封邮件测试

**目的**: 快速验证邮件服务配置是否正确

**操作**: 
1. 选择菜单选项 `3`
2. 输入你的测试邮箱地址

**预期结果**:
- 收到一封测试邮件
- 邮件格式正确，显示HTML样式

### 测试4: 查看测试数据

**目的**: 查看测试使用的模拟数据

**操作**: 选择菜单选项 `4`

## 邮件配置指南

### QQ邮箱配置

1. 登录 [QQ邮箱网页版](https://mail.qq.com)
2. 点击 **设置** → **账户**
3. 找到 **POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务**
4. 开启 **IMAP/SMTP服务**
5. 点击 **生成授权码**
6. 用手机QQ扫码验证
7. 复制生成的授权码（16位字符）

配置示例：
```env
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_USER=your_email@qq.com
SMTP_PASSWORD=abcdefghijklmnop  # 这里填授权码，不是QQ密码
```

### 163邮箱配置

1. 登录 [163邮箱](https://mail.163.com)
2. 点击 **设置** → **POP3/SMTP/IMAP**
3. 开启 **IMAP/SMTP服务**
4. 设置授权密码（需要手机验证）

配置示例：
```env
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USER=your_email@163.com
SMTP_PASSWORD=your_auth_password
```

### Outlook/Hotmail 配置

Outlook 使用 TLS 加密，配置最简单，直接使用登录密码即可。

**注意事项**:
1. 如果开启了两步验证，需要生成应用密码
2. 确保账户没有被标记为可疑活动

配置示例：
```env
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your_email@outlook.com
SMTP_PASSWORD=your_outlook_password  # 直接使用登录密码
```

**如果开启了两步验证**:
1. 登录 [Microsoft账户安全页面](https://account.microsoft.com/security)
2. 选择 **高级安全选项**
3. 找到 **应用密码**
4. 创建新的应用密码
5. 复制生成的密码

### Gmail配置

1. 开启 [两步验证](https://myaccount.google.com/security)
2. 生成 [应用专用密码](https://myaccount.google.com/apppasswords)
3. 选择"邮件"和你的设备
4. 复制生成的16位密码

配置示例：
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # 16位应用密码
```

## 修改测试数据

编辑 `test_local.py` 文件中的 `create_test_participants()` 函数：

```python
test_data = [
    {
        "id": "user_1",
        "name": "张三",
        "email": "zhangsan@example.com",  # 改为你的邮箱
        "wechat": "wx_zhangsan",
        "mbti": "INTJ",  # 设为空字符串 "" 测试无MBTI情况
        "gift_description": "手工编织的围巾",
        "quiz_answers": [...]
    },
    # 添加更多测试数据...
]
```

## 使用飞书数据测试

如果你已经配置了飞书，可以使用真实数据测试：

```bash
# 查看飞书数据
python cli.py fetch

# 运行匹配分析（不发邮件）
python cli.py analyze

# 运行匹配并发送邮件
python cli.py match
```

## 常见问题

### Q: 邮件发送失败，提示"535 Login Fail"

**A**: 授权码错误，请检查：
- 是否使用授权码而不是登录密码
- 授权码是否复制完整（无空格）
- 是否开启了SMTP服务

### Q: 邮件发送失败，提示"Connection refused"

**A**: SMTP服务器或端口配置错误，请检查：
- SMTP_HOST 是否正确
- SMTP_PORT 是否为 465（SSL）或 587（TLS）
- 网络是否能访问邮件服务器

### Q: 无MBTI的参与者文案还是提到了MBTI

**A**: 检查：
- `test_local.py` 中 MBTI 字段是否为空字符串 `""`
- 不要使用 `"无"`, `"未知"` 等文字，应该是空字符串

### Q: 匹配算法运行很慢

**A**: 这是正常的，因为需要调用AI API进行评分和文案生成。
- Phase 1 评分: 约需要 10-30秒（取决于参与者数量）
- Phase 2 算法: 约需要 1-5秒
- Phase 3 文案: 约需要 10-30秒

## API测试

如果你想测试API接口，可以启动服务：

```bash
# 安装依赖
pip install fastapi uvicorn

# 启动服务
uvicorn main:app --reload --port 8000
```

然后使用curl或Postman测试：

```bash
# 测试匹配接口
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d @test_data.json

# 测试邮件发送接口
curl -X POST http://localhost:8000/send-emails \
  -H "Content-Type: application/json" \
  -d @email_request.json
```

## 下一步

测试通过后，你可以：
1. 在前端集成邮件发送功能
2. 添加邮件发送确认界面
3. 优化邮件模板样式
4. 添加邮件发送日志记录
