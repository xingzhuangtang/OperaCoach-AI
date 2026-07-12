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
      router.push('/')
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
    <div class="mist-layer"></div>
    <div class="bamboo-shadow"></div>

    <div class="login-card fade-in">
      <div class="card-ornament top-left"></div>
      <div class="card-ornament top-right"></div>
      <div class="card-ornament bottom-left"></div>
      <div class="card-ornament bottom-right"></div>

      <h1 class="login-title">影子戏</h1>
      <p class="login-subtitle">以戏为影，以影传情</p>

      <div class="divider-line"></div>

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
          class="login-btn"
          :loading="loading"
          @click="handleLogin(loginFormRef)"
        >
          踏入江湖
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
          <el-input v-model="registerForm.username" placeholder="江湖名号" prefix-icon="Avatar" />
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
          class="login-btn"
          :loading="loading"
          @click="handleRegister(registerFormRef)"
        >
          初入江湖
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
  overflow: hidden;
  z-index: 1;
}

.mist-layer {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(ellipse at 30% 40%, rgba(58, 90, 120, 0.08) 0%, transparent 60%),
    radial-gradient(ellipse at 70% 60%, rgba(184, 134, 11, 0.05) 0%, transparent 60%);
  animation: mistFloat 20s ease-in-out infinite;
}

@keyframes mistFloat {
  0%, 100% { opacity: 0.6; transform: translateX(0); }
  50% { opacity: 1; transform: translateX(20px); }
}

.bamboo-shadow {
  position: fixed;
  top: 0;
  right: 0;
  width: 200px;
  height: 100%;
  pointer-events: none;
  z-index: 0;
  background: linear-gradient(to left, rgba(58, 90, 120, 0.05), transparent);
  opacity: 0.5;
}

.login-card {
  width: 440px;
  padding: 48px 40px;
  background: rgba(26, 26, 46, 0.85);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(184, 134, 11, 0.2);
  z-index: 1;
  position: relative;
}

.card-ornament {
  position: absolute;
  width: 24px;
  height: 24px;
  border: 2px solid rgba(184, 134, 11, 0.4);
}

.card-ornament.top-left {
  top: 12px;
  left: 12px;
  border-right: none;
  border-bottom: none;
}

.card-ornament.top-right {
  top: 12px;
  right: 12px;
  border-left: none;
  border-bottom: none;
}

.card-ornament.bottom-left {
  bottom: 12px;
  left: 12px;
  border-right: none;
  border-top: none;
}

.card-ornament.bottom-right {
  bottom: 12px;
  right: 12px;
  border-left: none;
  border-top: none;
}

.login-title {
  text-align: center;
  font-size: 32px;
  font-weight: 700;
  background: linear-gradient(135deg, #b8860b 0%, #daa520 50%, #b8860b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 6px;
  margin-bottom: 8px;
}

.login-subtitle {
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  letter-spacing: 2px;
  margin-bottom: 24px;
}

.divider-line {
  height: 1px;
  background: linear-gradient(90deg, transparent 0%, rgba(184, 134, 11, 0.4) 50%, transparent 100%);
  margin-bottom: 24px;
}

.login-tabs {
  margin-bottom: 24px;
}

.login-tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: rgba(184, 134, 11, 0.2);
}

.login-tabs :deep(.el-tabs__item) {
  color: rgba(255, 255, 255, 0.5);
  font-size: 15px;
  letter-spacing: 2px;
}

.login-tabs :deep(.el-tabs__item.is-active) {
  color: #b8860b;
}

.login-tabs :deep(.el-tabs__active-bar) {
  background-color: #b8860b;
}

.login-form {
  margin-top: 20px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.login-form :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(184, 134, 11, 0.2);
  border-radius: 6px;
  box-shadow: none;
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(184, 134, 11, 0.4);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.08);
  border-color: #b8860b;
  box-shadow: 0 0 0 2px rgba(184, 134, 11, 0.15) !important;
}

.login-form :deep(.el-input__inner) {
  color: #e0e0e0;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.3);
}

.login-form :deep(.el-input__prefix .el-icon) {
  color: rgba(184, 134, 11, 0.6);
}

.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  letter-spacing: 4px;
  background: linear-gradient(135deg, #3a5a78 0%, #5a7a98 100%);
  border: 1px solid rgba(184, 134, 11, 0.3);
  border-radius: 6px;
  color: #fff;
  margin-top: 8px;
  position: relative;
  overflow: hidden;
}

.login-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.login-btn:hover::before {
  left: 100%;
}

.login-btn:hover {
  background: linear-gradient(135deg, #2a4a68 0%, #3a5a78 100%);
  box-shadow: 0 6px 20px rgba(58, 90, 120, 0.4);
  transform: translateY(-2px);
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
