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
      await createWork(workForm)
      ElMessage.success('创建成功')
      dialogVisible.value = false
      Object.assign(workForm, { name: '', category: '', description: '' })
      await fetchWorks()
    } catch (e) {
      // 已处理
    }
  })
}

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
    <div class="ink-bg"></div>

    <!-- 顶部导航 -->
    <header class="header dreamy-card">
      <div class="header-left">
        <span class="logo">戏曲 AI 助教</span>
      </div>
      <div class="header-right">
        <el-button type="primary" class="dreamy-btn" @click="router.push('/upload')">
          上传管理
        </el-button>
        <el-button class="dreamy-btn" @click="handleLogout">退出</el-button>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="main-content fade-in">
      <div class="page-header">
        <h2 class="dreamy-title">我的作品</h2>
        <el-button type="primary" class="dreamy-btn" @click="dialogVisible = true">
          新建作品
        </el-button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-wrapper">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>加载中...</span>
      </div>

      <!-- 空状态 -->
      <el-empty v-else-if="works.length === 0" description="暂无作品，点击右上角新建" />

      <!-- 作品卡片网格 -->
      <div v-else class="works-grid">
        <div
          v-for="work in works"
          :key="work.id"
          class="work-card dreamy-card"
          @click="handleWorkClick(work)"
        >
          <div class="work-card-header">
            <h3>{{ work.name }}</h3>
            <el-button
              type="danger"
              size="small"
              text
              class="delete-btn"
              @click.stop="handleDeleteWork(work)"
            >
              删除作品
            </el-button>
          </div>
          <el-tag v-if="work.category" type="primary" size="small">
            {{ work.category }}
          </el-tag>
          <p v-if="work.description" class="description">{{ work.description }}</p>
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
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  font-size: 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #2b6cb0 0%, #d69e2e 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
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
  margin-bottom: 24px;
}

.works-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

.work-card {
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.work-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(43, 108, 176, 0.2);
}

.work-card h3 {
  margin-bottom: 12px;
  font-size: 18px;
  color: #1a202c;
}

.work-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.work-card-header h3 {
  margin-bottom: 0;
  flex: 1;
}

.delete-btn {
  flex-shrink: 0;
  color: #e53e3e;
}

.delete-btn:hover {
  color: #c53030;
}

.description {
  margin-top: 12px;
  color: #718096;
  font-size: 14px;
  line-height: 1.5;
}

.loading-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px;
  color: #718096;
}
</style>
