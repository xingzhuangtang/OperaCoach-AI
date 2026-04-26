# 前端 MVP 设计文档

> 日期：2026-04-25

## 概述

OperaCoach-AI 前端最小化 MVP，4 个页面，国风梦幻视觉风格。

## 需求确认

| 项目 | 决策 |
|------|------|
| 页面范围 | 登录/注册 + 作品列表 + 上传 + 唱段详情 |
| 视觉风格 | 国风梦幻（水墨渐变、青/金/白、戏曲元素） |
| 用户流程 | 手动分步（上传 → 提取音频 → 创建唱段 → 切片） |
| 认证方式 | 独立登录页 |
| 交付方式 | 一次完整交付 |

## 架构

### 技术选型
- **框架**: Vue 3 + TypeScript + Composition API
- **UI 库**: Element Plus（按国风主题定制）
- **路由**: Vue Router 4
- **HTTP**: Axios（封装统一拦截器）
- **状态**: 组件级 reactive/ref（MVP 不需要 Pinia）

### 目录结构
```
frontend/src/
  api/          # HTTP 请求封装
    index.ts      # Axios 实例 + 拦截器
    auth.ts       # 登录/注册
    upload.ts     # 文件上传
    segments.ts   # 作品/唱段/切片
  router/
    index.ts      # 路由配置 + 导航守卫
  styles/
    theme.css     # 国风主题覆盖
    global.css    # 全局样式
  views/
    LoginView.vue       # 登录/注册页
    WorksView.vue       # 作品列表
    UploadView.vue      # 上传管理
    SegmentView.vue     # 唱段详情
  components/
    AppHeader.vue       # 顶部导航
  types/
    index.ts      # 共享类型
  main.ts         # 入口
  App.vue         # 根组件
```

## 页面设计

### 1. LoginView — 登录/注册
- 水墨风格背景，居中卡片
- 切换标签：登录 / 注册
- 登录：手机号 + 密码
- 注册：手机号 + 用户名 + 密码 + 确认密码
- 成功后跳转作品列表

### 2. WorksView — 作品列表
- 顶部导航栏（Logo + 用户名 + 退出）
- 戏曲作品卡片网格（名称、类别、描述）
- "新建作品"按钮 → 弹窗表单
- 点击卡片 → 进入唱段详情页

### 3. UploadView — 上传管理
- 视频上传区（拖拽 + 点击）
- 音频上传区
- 已上传文件列表
- "提取音频"按钮（视频 → 音频，后端 TODO）
- "创建唱段"按钮 → 选择作品 + 填写名称 → 创建

### 4. SegmentView — 唱段详情
- 唱段基本信息（名称、所属作品）
- 音频/视频播放器
- 切片列表（时间、歌词、指令）
- "执行切片"按钮（调用 TODO 端点）
- 返回作品列表

## 数据流

```
LoginView → auth.login() → localStorage(token) → router.push('/works')
WorksView → segments.listWorks() → 渲染卡片 → 点击 → router.push('/segment/:id')
UploadView → upload.video() → 返回 url → segments.createSegment()
SegmentView → segments.getDetail(id) → 渲染切片列表
```

## 错误处理

- Axios 响应拦截器：401 自动跳转登录页
- 统一 Toast 提示（Element Plus ElMessage）
- 网络错误友好提示

## 实施状态

✅ 全部完成（2026-04-25）

- 基础设施：vue-router、Axios、类型定义
- 国风梦幻主题：global.css + theme.css
- 路由配置：导航守卫
- LoginView：登录/注册
- WorksView：作品列表
- UploadView：上传管理
- SegmentView：唱段详情
- App.vue + main.ts：入口

构建验证：`vite build` 通过，`npm run dev` 正常启动（端口 3000）

## 主题色

- 主色：`#2B6CB0`（青蓝，如水墨）
- 强调：`#D69E2E`（金色，戏曲华彩）
- 背景：`#F7FAFC` → `#E2E8F0`（水墨渐变）
- 文字：`#1A202C`（深墨色）
