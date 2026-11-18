# 知间 AI · 私人云端知识库

包含：原版中文知识库界面、SQLite 持久化、访问密钥认证、日常快速录入 API、Markdown 导入 API、可选 OpenAI 检索问答、Docker 部署。

## 本地试用

1. `cp .env.example .env`，将 `KB_ACCESS_TOKEN` 替换为随机长密钥，按需填写 `OPENAI_API_KEY`。
2. `pip install -r requirements.txt`
3. `set -a; source .env; set +a; KB_SECURE_COOKIE=false uvicorn server:app --host 127.0.0.1 --port 8000`（Windows 请使用 PowerShell 环境变量设置方式）。
4. 打开 `http://127.0.0.1:8000`，先在下方的云端登录框输入访问密钥。

## 云端部署

在自己的 Linux VPS 上安装 Docker 与 Compose，配置 `.env` 后运行 `docker compose up -d --build`。此配置**仅监听本机** 127.0.0.1:8000。使用 Caddy/Nginx 或可信隧道代理到域名，开启 HTTPS，才可在手机远程访问。请勿直接把 8000 端口暴露公网。

API 文档 `/docs` 需要带认证 Cookie 或 `Authorization: Bearer <KB_ACCESS_TOKEN>`。例如：

```bash
curl -X POST https://YOUR_DOMAIN/api/daily/quick \
 -H 'Authorization: Bearer YOUR_TOKEN' -H 'Content-Type: application/json' \
 -d '{"content":"今天学习了 Python，晚上跑步半小时","mood":"不错"}'
```

AI 接口 `POST /api/ai/ask`，JSON `{"question":"最近我的学习进展如何？"}`。基于关键词召回已有记录，非向量数据库；仅召回的片段会发送到配置的 AI 服务，**并非完全离线**。请不要把隐私内容发送到不信任的模型服务。AI 不会自动写回记忆，避免误记。

Markdown 导入 `POST /api/import/markdown`，JSON `{"title":"学习","content":"# 学习..."}`。已有的 Markdown 合集可以按章节逐项导入；当前未自动导入私人档案。

## 安全注意

本项目为个人 MVP：单用户共享访问密钥，没有多因素认证、细粒度权限、端到端加密或成熟的速率限制。生产环境建议加反向代理限流、备份、日志脱敏和密钥轮换。SQLite 数据库应放在持久卷中并定期加密备份。使用 HTTPS 时 `KB_SECURE_COOKIE=true`。前端旧版界面已增加登录和 AI 入口。
