<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Plus } from '@element-plus/icons-vue'
import { listSegmentsByWork, createSegment, deleteSegment, getWorkDetail } from '@/api/segments'
import type { OperaWork, OperaSegment } from '@/types'

const route = useRoute()
const router = useRouter()

const work = ref<OperaWork | null>(null)
const segments = ref<OperaSegment[]>([])
const loading = ref(false)
const creating = ref(false)

const workId = parseInt(route.params.workId as string)

const fetchSegments = async () => {
  loading.value = true
  try {
    const [workRes, segmentsRes] = await Promise.all([
      getWorkDetail(workId),
      listSegmentsByWork(workId),
    ])
    work.value = workRes.data
    segments.value = segmentsRes.data
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const handleCreateSegment = async () => {
  try {
    const { value: name } = await ElMessageBox.prompt('请输入唱段名称', '创建唱段', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    if (!name) return
    creating.value = true
    await createSegment({ work_id: workId, name })
    ElMessage.success('创建成功')
    await fetchSegments()
  } catch (e) {
    // 用户取消
  } finally {
    creating.value = false
  }
}

const handleDeleteSegment = async (segment: OperaSegment) => {
  try {
    await ElMessageBox.confirm(`确定要删除唱段"${segment.name}"吗？`, '删除唱段', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteSegment(segment.id)
    ElMessage.success('删除成功')
    await fetchSegments()
  } catch (e) {
    // 用户取消
  }
}

const handleSegmentClick = (segment: OperaSegment) => {
  router.push(`/segment/${segment.id}`)
}

const formatDuration = (seconds: number | null) => {
  if (!seconds) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

onMounted(() => {
  fetchSegments()
})
</script>

<template>
  <div class="segments-list-container">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-left">
        <button class="back-nav" @click="router.push('/hub')">← 返回</button>
        <span class="logo">影子戏</span>
        <span class="logo-sub">唱段列表</span>
      </div>
    </header>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrapper">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <!-- 主内容 -->
    <main v-else-if="work" class="main-content fade-in">
      <!-- 作品信息 -->
      <div class="info-card dreamy-card">
        <div class="info-header">
          <el-button text @click="router.push('/works')" class="back-btn">&#x2190; 返回</el-button>
          <h2 class="dreamy-title">{{ work.name }}</h2>
        </div>
        <p v-if="work.category" class="meta">类别：{{ work.category }}</p>
        <p v-if="work.description" class="meta">简介：{{ work.description }}</p>
        <p class="meta">唱段数量：{{ segments.length }}</p>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <el-button
          type="primary"
          class="dreamy-btn"
          :icon="Plus"
          :loading="creating"
          @click="handleCreateSegment"
        >
          创建新唱段
        </el-button>
      </div>

      <!-- 唱段列表 -->
      <div class="segments-grid">
        <div v-if="segments.length === 0" class="empty-state">
          <div class="empty-icon">曲</div>
          <p class="empty-text">尚无唱段</p>
          <p class="empty-hint">点击上方"创建新唱段"开始</p>
        </div>

        <div
          v-for="(segment, index) in segments"
          :key="segment.id"
          class="segment-card"
          :style="{ animationDelay: `${index * 0.1}s` }"
          @click="handleSegmentClick(segment)"
        >
          <div class="card-top-line"></div>
          <div class="segment-inner">
            <div class="segment-info">
              <h3 class="segment-name">{{ segment.name }}</h3>
              <div class="segment-meta">
                <span v-if="segment.audio_url" class="tag tag-audio">&#x1f3b5; 有音频</span>
                <span v-if="segment.video_url" class="tag tag-video">&#x1f3ac; 有视频</span>
                <span v-if="segment.is_separated" class="tag tag-separated">&#x1f3a4; 已分离</span>
                <span v-if="segment.slices?.length" class="tag tag-slices">{{ segment.slices.length }} 个切片</span>
              </div>
            </div>
            <div class="segment-actions">
              <el-button
                type="danger"
                text
                size="small"
                @click.stop="handleDeleteSegment(segment)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.segments-list-container {
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(26, 26, 46, 0.9);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(184, 134, 11, 0.15);
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.back-nav {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 1px;
  padding: 4px 10px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.back-nav:hover {
  color: #b8860b;
  background: rgba(184, 134, 11, 0.08);
}

.logo {
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, #b8860b 0%, #daa520 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 3px;
}

.logo-sub {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.3);
  letter-spacing: 2px;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px;
}

.info-card {
  padding: 24px;
  margin-bottom: 24px;
}

.info-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.back-btn:hover {
  color: #b8860b;
}

.dreamy-title {
  margin: 0;
  font-size: 24px;
}

.meta {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.4);
}

.actions {
  margin-bottom: 24px;
}

.segments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.segment-card {
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  animation: cardFadeIn 0.6s ease-out forwards;
  opacity: 0;
  position: relative;
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

.segment-card:hover {
  transform: translateY(-4px);
}

.segment-card:hover .card-top-line {
  background: linear-gradient(90deg, transparent 0%, #b8860b 50%, transparent 100%);
  opacity: 1;
}

.card-top-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, rgba(184, 134, 11, 0.3) 50%, transparent 100%);
  transition: all 0.3s ease;
}

.segment-inner {
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border-radius: 8px;
  border: 1px solid rgba(184, 134, 11, 0.15);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.segment-info {
  flex: 1;
}

.segment-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #e0e0e0;
  letter-spacing: 2px;
}

.segment-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid;
}

.tag-audio {
  background: rgba(184, 134, 11, 0.1);
  border-color: rgba(184, 134, 11, 0.3);
  color: #b8860b;
}

.tag-video {
  background: rgba(58, 90, 120, 0.1);
  border-color: rgba(58, 90, 120, 0.3);
  color: #7a9ab8;
}

.tag-separated {
  background: rgba(74, 124, 89, 0.1);
  border-color: rgba(74, 124, 89, 0.3);
  color: #4a7c59;
}

.tag-slices {
  background: rgba(184, 134, 11, 0.05);
  border-color: rgba(184, 134, 11, 0.2);
  color: rgba(184, 134, 11, 0.7);
}

.segment-actions {
  margin-left: 16px;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 64px;
  color: rgba(184, 134, 11, 0.2);
  margin-bottom: 20px;
  font-weight: 700;
  letter-spacing: 4px;
}

.empty-text {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 8px;
  letter-spacing: 2px;
}

.empty-hint {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.25);
}

.loading-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px;
  color: rgba(255, 255, 255, 0.4);
}
</style>
