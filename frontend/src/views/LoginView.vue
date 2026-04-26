<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login, register } from '@/api/auth'

const router = useRouter()
const isLogin = ref(true)
const loading = ref(false)
const loginFormRef = ref()
const registerFormRef = ref()

const loginForm = reactive({
  phone: '',
  password: '',
})

const registerForm = reactive({
  phone: '',
  username: '',
  password: '',
  confirmPassword: '',
})

const loginRules = {
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const registerRules = {
  phone: [{ required: true, message: '请输入手机号', trigger: 'blur' }],
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
  ],
}

const handleLogin = async (formEl: any) => {
  if (!formEl) return
  await formEl.validate(async (valid: boolean) => {
    if (!valid) return
    loading.value = true
    try {
      const { data } = await login(loginForm.phone, loginForm.password)
      localStorage.setItem('token', data.access_token)
      ElMessage.success('登录成功')
      router.push('/works')
    } catch (e) {
      // 错误已由 axios 拦截器处理
    } finally {
      loading.value = false
    }
  })
}

const handleRegister = async (formEl: any) => {
  if (!formEl) return
  await formEl.validate(async (valid: boolean) => {
    if (!valid) return
    if (registerForm.password !== registerForm.confirmPassword) {
      ElMessage.error('两次密码不一致')
      return
    }
    loading.value = true
    try {
      await register(registerForm.phone, registerForm.username, registerForm.password)
      ElMessage.success('注册成功，请登录')
      isLogin.value = true
    } catch (e) {
      // 错误已由 axios 拦截器处理
    } finally {
      loading.value = false
    }
  })
}
</script>

<template>
  <div class="login-container">
    <div class="ink-bg"></div>
    <div class="login-card fade-in">
      <h1 class="dreamy-title">戏曲 AI 助教</h1>
      <el-tabs v-model="isLogin" class="login-tabs">
        <el-tab-pane :label="'登录'" :name="true" />
        <el-tab-pane :label="'注册'" :name="false" />
      </el-tabs>

      <el-form
        v-if="isLogin"
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-width="0"
        class="login-form"
      >
        <el-form-item prop="phone">
          <el-input v-model="loginForm.phone" placeholder="手机号" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-button
          type="primary"
          class="dreamy-btn"
          :loading="loading"
          @click="handleLogin(loginFormRef)"
          style="width: 100%"
        >
          登录
        </el-button>
      </el-form>

      <el-form
        v-else
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        label-width="0"
        class="login-form"
      >
        <el-form-item prop="phone">
          <el-input v-model="registerForm.phone" placeholder="手机号" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="username">
          <el-input v-model="registerForm.username" placeholder="用户名" prefix-icon="Avatar" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        <el-button
          type="primary"
          class="dreamy-btn"
          :loading="loading"
          @click="handleRegister(registerFormRef)"
          style="width: 100%"
        >
          注册
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.ink-bg {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  z-index: 0;
}

.ink-bg::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at 20% 50%, rgba(43, 108, 176, 0.1) 0%, transparent 50%),
              radial-gradient(circle at 80% 20%, rgba(214, 158, 46, 0.1) 0%, transparent 50%);
}

.login-card {
  width: 420px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(43, 108, 176, 0.15);
  border: 1px solid rgba(214, 158, 46, 0.2);
  z-index: 1;
}

.dreamy-title {
  text-align: center;
  margin-bottom: 30px;
  font-size: 28px;
  background: linear-gradient(135deg, #2b6cb0, #d69e2e);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-tabs {
  margin-bottom: 24px;
}

.login-form {
  margin-top: 20px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.dreamy-btn {
  background: linear-gradient(135deg, #2b6cb0, #3182ce);
  border: none;
  border-radius: 8px;
  height: 44px;
  font-size: 16px;
}

.dreamy-btn:hover {
  background: linear-gradient(135deg, #2c5282, #2b6cb0);
}

.fade-in {
  animation: fadeIn 0.6s ease-in-out;
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
