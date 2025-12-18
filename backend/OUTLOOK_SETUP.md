# Outlook 邮箱配置指南

## 快速配置（3分钟）

### 步骤1: 编辑配置文件

编辑 `backend/.env` 文件，添加以下配置：

```env
# Outlook 邮件配置
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your_email@outlook.com
SMTP_PASSWORD=your_password
SENDER_EMAIL=your_email@outlook.com
SENDER_NAME=圣诞礼物匹配系统
```

### 步骤2: 填写你的信息

将以下内容替换为你的真实信息：
- `your_email@outlook.com` → 你的 Outlook 邮箱地址
- `your_password` → 你的 Outlook 登录密码

**支持的邮箱域名**:
- `@outlook.com`
- `@hotmail.com`
- `@live.com`
- `@msn.com`

### 步骤3: 测试邮件发送

```bash
cd backend
python test_local.py
```

选择 `3` - 发送单封测试邮件，输入你的邮箱地址测试。

---

## 常见问题

### ❌ 错误: "535 5.7.3 Authentication unsuccessful"

**原因**: 密码错误或账户安全设置问题

**解决方案**:

#### 方案1: 检查密码
- 确认密码正确（可以先在网页版登录测试）
- 密码中如果有特殊字符，确保正确转义

#### 方案2: 开启"安全性较低的应用访问"
1. 登录 [Microsoft 账户](https://account.microsoft.com)
2. 进入 **安全性** → **高级安全选项**
3. 关闭 **需要使用我的 Microsoft 身份验证器应用进行登录**

#### 方案3: 使用应用密码（推荐）
如果你的账户开启了两步验证：

1. 访问 [Microsoft 账户安全页面](https://account.microsoft.com/security)
2. 选择 **高级安全选项**
3. 找到 **应用密码** 部分
4. 点击 **创建新的应用密码**
5. 输入名称（如"礼物匹配系统"）
6. 复制生成的密码
7. 在 `.env` 中使用这个应用密码

```env
SMTP_PASSWORD=abcd1234efgh5678  # 使用应用密码
```

### ❌ 错误: "Connection refused" 或 "Timeout"

**原因**: 网络问题或端口被封

**解决方案**:
1. 检查网络连接
2. 确认防火墙没有阻止 587 端口
3. 如果在公司网络，可能需要使用代理

### ❌ 错误: "554 5.2.0 STOREDRV.Submission.Exception"

**原因**: 邮件内容被 Outlook 安全策略拦截

**解决方案**:
1. 检查邮件内容是否包含敏感词
2. 尝试发送简单的测试邮件
3. 确认账户没有被标记为垃圾邮件发送者

### ⚠️ 邮件进入垃圾箱

**原因**: Outlook 的垃圾邮件过滤

**解决方案**:
1. 将发件人添加到联系人
2. 在垃圾邮件中标记为"非垃圾邮件"
3. 设置收件箱规则，将来自该地址的邮件标记为安全

---

## 完整配置示例

### 示例1: 基本配置（无两步验证）

```env
# AI 配置
AI_API_KEY=sk-xxxxxxxxxxxxx
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL_NAME=gpt-4

# Outlook 邮件配置
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=zhangsan@outlook.com
SMTP_PASSWORD=MyPassword123!
SENDER_EMAIL=zhangsan@outlook.com
SENDER_NAME=圣诞礼物匹配系统
```

### 示例2: 使用应用密码（开启两步验证）

```env
# AI 配置
AI_API_KEY=sk-xxxxxxxxxxxxx
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL_NAME=gpt-4

# Outlook 邮件配置
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=zhangsan@outlook.com
SMTP_PASSWORD=abcd1234efgh5678  # 应用密码
SENDER_EMAIL=zhangsan@outlook.com
SENDER_NAME=圣诞礼物匹配系统
```

---

## 测试流程

### 1. 快速测试（单封邮件）

```bash
python test_local.py
```

选择 `3`，输入你的邮箱，检查是否收到测试邮件。

### 2. 完整测试（匹配 + 邮件）

修改 `test_local.py` 中的测试数据：

```python
test_data = [
    {
        "email": "your_real_email@outlook.com",  # 改为你的邮箱
        # ... 其他字段
    },
    # ...
]
```

运行测试：

```bash
python test_local.py
```

选择 `2` - 测试完整流程

---

## 安全建议

1. **不要将 `.env` 文件提交到 Git**
   - 已在 `.gitignore` 中排除
   - 包含敏感信息（密码、API密钥）

2. **使用应用密码而非主密码**
   - 更安全
   - 可以随时撤销
   - 不影响主账户

3. **定期更换密码**
   - 特别是应用密码
   - 如果怀疑泄露，立即更换

4. **限制发送频率**
   - Outlook 有发送限制（每天约300封）
   - 避免短时间内大量发送

---

## 需要帮助？

如果遇到其他问题：
1. 查看 [TEST_GUIDE.md](./TEST_GUIDE.md) 了解更多邮箱配置
2. 检查 Outlook 的 [SMTP 设置文档](https://support.microsoft.com/zh-cn/office/pop-imap-和-smtp-设置-8361e398-8af4-4e97-b147-6c6c4ac95353)
3. 确认账户状态正常（登录网页版检查）
