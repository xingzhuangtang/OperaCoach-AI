# AGENTS.md — OperaCoach-AI V2 (MVP)

## 项目概要
戏曲（京剧/昆曲等）AI 助教 MVP。用户上传演唱视频/音频，系统智能切片并可视化展示。

- **后端**: FastAPI + SQLAlchemy + SQLite (可切 PostgreSQL)
- **前端**: Vue 3 + TypeScript + Vite + Element Plus
- **AI**: OpenAI Whisper + Librosa + MoviePy

## 关键命令

```bash
# 启动 PostgreSQL (可选，默认用 SQLite)
docker compose up -d

# 后端
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend && npm run dev

# 构建前端
cd frontend && npm run build   # 含 vue-tsc 类型检查
```

## 架构要点

**API 路由** (`/api/v1`):
- `auth` — 注册/登录（JWT，7天过期）
- `upload` — 视频/音频上传（存 `backend/uploads/`）
- `segments` — 戏曲作品/唱段管理 + 音频切片

**数据模型**: `OperaWork`(作品) → `OperaSegment`(唱段) → `SegmentSlice`(切片)

**认证**: 手机号+密码，SHA-256 哈希（MVP 级别，`passlib[bcrypt]` 在依赖中但未使用）

**配置**: `backend/app/core/config.py`，支持 `.env` 文件覆盖默认值

## 重要注意事项

1. **数据库表在启动时自动创建** (`main.py:15`)，无需迁移工具
2. **音频切片端点是 TODO** — `/segments/{id}/slice` 返回模拟数据，`processors/audio.py` 有基础实现但未接入
3. **前端几乎为空** — `views/`、`components/`、`api/` 目录均为空，待开发
4. **无测试框架** — 项目中没有测试配置
5. **无 lint/format 工具** — 没有 ESLint、Prettier、Ruff 等配置
6. **uploads/ 在 .gitignore 中** — 上传文件不会提交
7. **Docker Compose 只定义了 PostgreSQL** — 不包含后端/前端服务

## 文件结构

```
backend/
  app/
    api/v1/   auth.py, upload.py, segments.py
    core/     config.py, database.py
    models/   User, OperaWork, OperaSegment, SegmentSlice
    schemas/  user.py (含所有 Pydantic 模型)
    processors/ audio.py (AudioProcessor, AudioSlicer)
    main.py
  uploads/    运行时生成

frontend/     仅有 package.json，源代码待开发
```

## CI/CD
无。无 GitHub Actions 或 pre-commit 配置。
