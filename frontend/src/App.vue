<template>
  <div class="app-bg" :style="bgStyle"></div>
  <router-view />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const bgStyle = computed(() => {
  const isHome = route.path === '/'
  const isLogin = route.path === '/login'
  const img = isHome || isLogin ? '/images/stage.png' : '/images/curtain.png'
  const blur = isLogin ? 6 : 4
  const brightness = isLogin ? 0.4 : 0.5
  return {
    backgroundImage: `url('${img}')`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    filter: `blur(${blur}px) brightness(${brightness})`,
  }
})
</script>

<style>
#app {
  height: 100%;
}

.app-bg {
  position: fixed;
  top: -20px;
  left: -20px;
  right: -20px;
  bottom: -20px;
  z-index: 0;
  pointer-events: none;
  background-color: #1a1a2e;
  transition: background-image 0.6s ease, filter 0.6s ease;
}

.app-bg::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 30% 40%, rgba(58, 90, 120, 0.12) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 60%, rgba(184, 134, 11, 0.06) 0%, transparent 60%);
}
</style>
