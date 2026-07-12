<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'

const router = useRouter()

const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    localStorage.removeItem('token')
    router.push('/login')
  }).catch(() => {})
}
</script>

<template>
  <div class="home-container">
    <div class="home-content fade-in">
      <div class="brand">
        <h1 class="brand-title">影子戏</h1>
        <p class="brand-subtitle">以戏为影，以影传情</p>
      </div>

      <div class="entry-cards">
        <div class="entry-card" @click="router.push('/music')">
          <div class="card-glow"></div>
          <div class="card-icon">
            <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
              <path d="M26 42V22l16 10-16 10z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
            </svg>
          </div>
          <h2 class="card-title">音乐生成</h2>
          <p class="card-desc">AI 智能作曲，一键生成音乐</p>
          <span class="card-action">进入 →</span>
        </div>

        <div class="entry-card" @click="router.push('/hub')">
          <div class="card-glow"></div>
          <div class="card-icon">
            <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="32" cy="32" r="28" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
              <path d="M20 24h24M20 32h24M20 40h16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <h2 class="card-title">音乐拆解</h2>
          <p class="card-desc">作品 · 上传 · 唱段管理</p>
          <span class="card-action">进入 →</span>
        </div>
      </div>

      <div class="home-footer">
        <button class="logout-btn" @click="handleLogout">退出登录</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.home-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  position: relative;
  z-index: 1;
}

.home-content {
  text-align: center;
  max-width: 800px;
  width: 100%;
}

.brand {
  margin-bottom: 64px;
}

.brand-title {
  font-size: 48px;
  font-weight: 700;
  background: linear-gradient(135deg, #b8860b 0%, #daa520 50%, #b8860b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 12px;
  margin-bottom: 12px;
}

.brand-subtitle {
  color: rgba(255, 255, 255, 0.4);
  font-size: 16px;
  letter-spacing: 4px;
}

.entry-cards {
  display: flex;
  gap: 40px;
  justify-content: center;
  margin-bottom: 80px;
}

.entry-card {
  width: 280px;
  padding: 48px 32px;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  border: 1px solid rgba(184, 134, 11, 0.15);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.card-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, rgba(184, 134, 11, 0.4) 50%, transparent 100%);
  opacity: 0.5;
  transition: opacity 0.4s ease;
}

.entry-card:hover {
  transform: translateY(-8px);
  border-color: rgba(184, 134, 11, 0.4);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4), 0 0 40px rgba(184, 134, 11, 0.08);
}

.entry-card:hover .card-glow {
  opacity: 1;
  background: linear-gradient(90deg, transparent 0%, #b8860b 50%, transparent 100%);
}

.entry-card:hover .card-action {
  color: #b8860b;
  letter-spacing: 4px;
}

.card-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 24px;
  color: rgba(184, 134, 11, 0.6);
  transition: color 0.3s ease;
}

.entry-card:hover .card-icon {
  color: rgba(184, 134, 11, 0.9);
}

.card-icon svg {
  width: 100%;
  height: 100%;
}

.card-title {
  font-size: 24px;
  color: #e0e0e0;
  letter-spacing: 4px;
  margin-bottom: 12px;
  font-weight: 600;
}

.card-desc {
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  letter-spacing: 2px;
  margin-bottom: 24px;
}

.card-action {
  font-size: 13px;
  color: rgba(184, 134, 11, 0.5);
  letter-spacing: 2px;
  transition: all 0.3s ease;
}

.home-footer {
  margin-top: 20px;
}

.logout-btn {
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.3);
  padding: 8px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  letter-spacing: 2px;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  border-color: rgba(139, 0, 0, 0.4);
  color: rgba(139, 0, 0, 0.6);
}

.fade-in {
  animation: fadeIn 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(30px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
