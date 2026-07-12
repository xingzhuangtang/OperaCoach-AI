<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const sections = [
  {
    title: '作品管理',
    desc: '创建、浏览所有戏曲作品',
    icon: 'M4 6h16M4 12h16M4 18h10',
    route: '/works',
    action: '进入管理',
  },
  {
    title: '上传管理',
    desc: '上传视频或音频文件',
    icon: 'M12 4v12m0 0l-4-4m4 4l4-4M4 20h16',
    route: '/upload',
    action: '进入上传',
  },
  {
    title: '唱段管理',
    desc: '按作品查看唱段列表与详情',
    icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
    route: '/works',
    action: '进入唱段',
  },
]
</script>

<template>
  <div class="hub-container">
    <header class="hub-header">
      <button class="back-btn" @click="router.push('/')">
        ← 返回首页
      </button>
      <div class="hub-brand">
        <span class="brand-name">影子戏</span>
        <span class="brand-sep">·</span>
        <span class="brand-section">音乐拆解</span>
      </div>
      <div class="header-spacer"></div>
    </header>

    <main class="hub-content fade-in">
      <h2 class="hub-title">选择管理模块</h2>
      <p class="hub-subtitle">清晰管理你的戏曲素材</p>

      <div class="hub-cards">
        <div
          v-for="(section, index) in sections"
          :key="section.title"
          class="hub-card"
          :style="{ animationDelay: `${index * 0.12}s` }"
          @click="router.push(section.route)"
        >
          <div class="hub-card-glow"></div>
          <div class="hub-card-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path :d="section.icon" />
            </svg>
          </div>
          <h3 class="hub-card-title">{{ section.title }}</h3>
          <p class="hub-card-desc">{{ section.desc }}</p>
          <span class="hub-card-action">{{ section.action }} →</span>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.hub-container {
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

.hub-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  background: rgba(26, 26, 46, 0.85);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(184, 134, 11, 0.12);
}

.back-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 1px;
  padding: 6px 12px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.back-btn:hover {
  color: #b8860b;
  background: rgba(184, 134, 11, 0.08);
}

.hub-brand {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.brand-name {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #b8860b 0%, #daa520 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 3px;
}

.brand-sep {
  color: rgba(184, 134, 11, 0.3);
  font-size: 16px;
}

.brand-section {
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
  letter-spacing: 2px;
}

.header-spacer {
  width: 100px;
}

.hub-content {
  max-width: 1000px;
  margin: 0 auto;
  padding: 60px 32px;
  text-align: center;
}

.hub-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #b8860b 0%, #daa520 50%, #b8860b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 4px;
  margin-bottom: 8px;
}

.hub-subtitle {
  color: rgba(255, 255, 255, 0.35);
  font-size: 14px;
  letter-spacing: 2px;
  margin-bottom: 48px;
}

.hub-cards {
  display: flex;
  gap: 32px;
  justify-content: center;
}

.hub-card {
  width: 260px;
  padding: 40px 28px;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border-radius: 10px;
  border: 1px solid rgba(184, 134, 11, 0.12);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  animation: cardFadeIn 0.6s ease-out forwards;
  opacity: 0;
}

@keyframes cardFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hub-card-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, rgba(184, 134, 11, 0.3) 50%, transparent 100%);
  opacity: 0.4;
  transition: opacity 0.3s ease;
}

.hub-card:hover {
  transform: translateY(-6px);
  border-color: rgba(184, 134, 11, 0.35);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4);
}

.hub-card:hover .hub-card-glow {
  opacity: 1;
  background: linear-gradient(90deg, transparent 0%, #b8860b 50%, transparent 100%);
}

.hub-card:hover .hub-card-action {
  color: #b8860b;
  letter-spacing: 3px;
}

.hub-card-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 20px;
  color: rgba(184, 134, 11, 0.5);
  transition: color 0.3s ease;
}

.hub-card:hover .hub-card-icon {
  color: rgba(184, 134, 11, 0.8);
}

.hub-card-icon svg {
  width: 100%;
  height: 100%;
}

.hub-card-title {
  font-size: 20px;
  color: #e0e0e0;
  letter-spacing: 3px;
  margin-bottom: 10px;
  font-weight: 600;
}

.hub-card-desc {
  color: rgba(255, 255, 255, 0.35);
  font-size: 13px;
  letter-spacing: 1px;
  margin-bottom: 24px;
  line-height: 1.6;
}

.hub-card-action {
  font-size: 13px;
  color: rgba(184, 134, 11, 0.45);
  letter-spacing: 2px;
  transition: all 0.3s ease;
}

.fade-in {
  animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
