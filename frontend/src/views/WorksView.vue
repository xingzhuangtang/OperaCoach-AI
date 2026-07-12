<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { listWorks, createWork, deleteWork } from '@/api/segments'
import type { OperaWork } from '@/types'

const router = useRouter()
const works = ref<OperaWork[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const workFormRef = ref()

const workForm = reactive({
  name: '',
  category: '',
  description: '',
})

const categories = ['京剧', '昆曲', '豫剧', '越剧', '黄梅戏', '其他']

const workRules = {
  name: [{ required: true, message: '请输入作品名称', trigger: 'blur' }],
}

const fetchWorks = async () => {
  loading.value = true
  try {
    const { data } = await listWorks()
    works.value = data
  } catch (e) {
    // 已处理
  } finally {
    loading.value = false
  }
}

const handleCreateWork = async () => {
  if (!workFormRef.value) return
  await workFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    try {
      await createWork({
        name: workForm.name,
        category: workForm.category || undefined,
        description: workForm.description || undefined,
      })
      ElMessage.success('创建成功')
      dialogVisible.value = false
      Object.assign(workForm, { name: '', category: '', description: '' })
      await fetchWorks()
    } catch (e) {
      ElMessage.error('创建失败')
    }
  })
}

const handleWorkClick = (work: OperaWork) => {
  router.push(`/works/${work.id}/segments`)
}

const handleDeleteWork = async (work: OperaWork) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除作品"${work.name}"吗？关联的唱段和切片也将被删除。`,
      '删除作品',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteWork(work.id)
    ElMessage.success('删除成功')
    await fetchWorks()
  } catch (e) {
    // 用户取消或已处理
  }
}

onMounted(() => {
  fetchWorks()
})
</script>

<template>
  <div class="works-container">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-left">
        <button class="back-nav" @click="router.push('/hub')">← 返回</button>
        <span class="logo">影子戏</span>
        <span class="logo-sub">作品管理</span>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="main-content fade-in">
      <div class="page-header">
        <div class="page-title-group">
          <h2 class="dreamy-title">我的作品</h2>
          <div class="title-underline"></div>
        </div>
        <el-button type="primary" class="dreamy-btn create-btn" @click="dialogVisible = true">
          新建作品
        </el-button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-wrapper">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <!-- 空状态 -->
      <div v-else-if="works.length === 0" class="empty-state">
        <div class="empty-icon">剑</div>
        <p class="empty-text">江湖空空，尚无作品</p>
        <p class="empty-hint">点击右上角"新建作品"开始你的戏曲之旅</p>
      </div>

      <!-- 作品卡片网格 -->
      <div v-else class="works-grid">
        <div
          v-for="(work, index) in works"
          :key="work.id"
          class="work-card"
          :style="{ animationDelay: `${index * 0.1}s` }"
          @click="handleWorkClick(work)"
        >
          <div class="card-top-line"></div>
          <div class="work-card-inner">
            <div class="work-card-header">
              <h3>{{ work.name }}</h3>
              <el-button
                type="danger"
                size="small"
                text
                class="delete-btn"
                @click.stop="handleDeleteWork(work)"
              >
                删除
              </el-button>
            </div>
            <el-tag v-if="work.category" type="warning" size="small" class="category-tag">
              {{ work.category }}
            </el-tag>
            <p v-if="work.description" class="description">{{ work.description }}</p>
            <div class="card-footer">
              <span class="enter-text">进入唱段 →</span>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 新建作品弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="新建作品"
      width="500px"
      class="dreamy-dialog"
    >
      <el-form ref="workFormRef" :model="workForm" :rules="workRules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="workForm.name" placeholder="请输入作品名称" />
        </el-form-item>
        <el-form-item label="类别">
          <el-select v-model="workForm.category" placeholder="请选择类别" style="width: 100%">
            <el-option
              v-for="cat in categories"
              :key="cat"
              :label="cat"
              :value="cat"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input
            v-model="workForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入作品描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" class="dreamy-btn" @click="handleCreateWork">
          创建
        </el-button>
      </template>
    </el-dialog>

  </div>
</template>

<style scoped>
.works-container {
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
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
  letter-spacing: 2px;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 32px;
}

.page-title-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dreamy-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #b8860b 0%, #daa520 50%, #b8860b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 4px;
}

.title-underline {
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, #b8860b, transparent);
}

.create-btn {
  letter-spacing: 2px;
}

.works-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.work-card {
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

.work-card:hover {
  transform: translateY(-6px);
}

.work-card:hover .card-top-line {
  background: linear-gradient(90deg, transparent 0%, #b8860b 50%, transparent 100%);
  opacity: 1;
}

.work-card:hover .enter-text {
  color: #b8860b;
  letter-spacing: 3px;
}

.card-top-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, rgba(184, 134, 11, 0.4) 50%, transparent 100%);
  transition: all 0.3s ease;
}

.work-card-inner {
  padding: 28px;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border-radius: 8px;
  border: 1px solid rgba(184, 134, 11, 0.15);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.work-card h3 {
  font-size: 20px;
  color: #e0e0e0;
  letter-spacing: 2px;
  margin-bottom: 12px;
  font-weight: 600;
}

.work-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}

.work-card-header h3 {
  margin-bottom: 0;
  flex: 1;
}

.delete-btn {
  flex-shrink: 0;
  color: rgba(139, 0, 0, 0.6);
}

.delete-btn:hover {
  color: #8b0000;
}

.category-tag {
  align-self: flex-start;
  margin-bottom: 12px;
}

.description {
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
  line-height: 1.6;
  flex: 1;
}

.card-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(184, 134, 11, 0.1);
}

.enter-text {
  font-size: 13px;
  color: rgba(184, 134, 11, 0.6);
  letter-spacing: 2px;
  transition: all 0.3s ease;
}

.empty-state {
  text-align: center;
  padding: 80px 20px;
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

/* 弹窗样式 */
.dreamy-dialog :deep(.el-dialog) {
  background: rgba(26, 26, 46, 0.95);
  border: 1px solid rgba(184, 134, 11, 0.3);
}

.dreamy-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(184, 134, 11, 0.2);
}

.dreamy-dialog :deep(.el-dialog__title) {
  color: #b8860b;
  letter-spacing: 2px;
}

.dreamy-dialog :deep(.el-form-item__label) {
  color: rgba(255, 255, 255, 0.6);
}

.dreamy-dialog :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(184, 134, 11, 0.2);
}

.dreamy-dialog :deep(.el-input__inner) {
  color: #e0e0e0;
}

.dreamy-dialog :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(184, 134, 11, 0.2);
  color: #e0e0e0;
}

</style>
