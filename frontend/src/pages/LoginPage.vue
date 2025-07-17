<template>
    <div class="w-full min-h-[100vh] relative bg-[var(--background-gray-main)] dark:bg-[#050505]">
        <div
            class="sticky top-0 left-0 w-full z-[10] px-[48px] max-sm:px-[12px] max-sm:bg-[var(--background-gray-login)]">
            <div class="w-full h-[60px] mx-auto flex items-center justify-between text-[var(--text-primary)]">
                <a href="/">
                    <div class="flex">
                        <Bot :size="30" />
                        <ManusLogoTextIcon />
                    </div>
                </a>
            </div>
        </div>
        <div
            class="relative z-[1] flex flex-col justify-center items-center min-h-[100vh] pt-[20px] pb-[60px] -mt-[60px] max-sm:pt-[80px] max-sm:pb-[80px] max-sm:mt-0 max-sm:min-h-[calc(100vh-60px)] max-sm:justify-start">
            <div class="w-full max-w-[720px] pt-[24px] mb-[40px] max-sm:pt-[0px]">
                <div class="flex flex-col items-center gap-[20px] relative" style="z-index:1">
                    <div class="w-[80px] h-[80px] text-[var(--icon-primary)] max-sm:w-[64px] max-sm:h-[64px]">
                        <Bot :size="80" />
                    </div>
                    <h1 class="text-[20px] font-bold text-center text-[var(--text-primary)] max-sm:text-[18px]">
                        {{ isRegistering ? '注册 Manus' : '登录 Manus' }}
                    </h1>
                </div>
            </div>
            <div class="w-full max-w-[384px] py-[24px] pt-0 px-[12px] relative" style="z-index:1">
                <div class="flex flex-col justify-center gap-[40px] text-[var(--text-primary)] max-sm:gap-[12px]">
                    <!-- 移除显示全局错误信息的区域 -->

                    <form @submit.prevent="handleSubmit" class="flex flex-col items-stretch gap-[20px]">
                        <div class="relative">
                            <div class="transition-all duration-500 ease-out opacity-100 scale-100">
                                <div class="flex flex-col gap-[12px]">
                                    <!-- 用户名字段（仅注册时显示） -->
                                    <div v-if="isRegistering" class="flex flex-col items-start">
                                        <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                                            <label for="username"
                                                class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                                                <span>用户名</span>
                                            </label>
                                        </div>
                                        <input
                                            v-model="formData.username"
                                            class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pr-1.5 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] w-full"
                                            :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.username }"
                                            id="username" 
                                            placeholder="输入用户名" 
                                            :disabled="isLoading"
                                            @input="validateField('username')"
                                            @blur="validateField('username')">
                                        <div
                                            class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                                            :class="validationErrors.username ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                                            {{ validationErrors.username }}
                                        </div>
                                    </div>

                                    <!-- 邮箱字段 -->
                                    <div class="flex flex-col items-start">
                                        <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                                            <label for="email"
                                                class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                                                <span>邮箱</span>
                                            </label>
                                        </div>
                                        <input
                                            v-model="formData.email"
                                            class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pr-1.5 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] w-full"
                                            :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.email }"
                                            id="email" 
                                            placeholder="mail@domain.com" 
                                            type="email"
                                            :disabled="isLoading"
                                            @input="validateField('email')"
                                            @blur="validateField('email')">
                                        <div
                                            class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                                            :class="validationErrors.email ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                                            {{ validationErrors.email }}
                                        </div>
                                    </div>

                                    <!-- 密码字段 -->
                                    <div class="flex flex-col items-start">
                                        <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                                            <label for="password"
                                                class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                                                <span>密码</span>
                                            </label>
                                        </div>
                                        <div class="relative w-full">
                                            <input
                                                v-model="formData.password"
                                                class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 w-full disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] pr-[40px]"
                                                :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.password }"
                                                placeholder="输入密码" 
                                                :type="showPassword ? 'text' : 'password'"
                                                :disabled="isLoading"
                                                @input="validateField('password')"
                                                @blur="validateField('password')">
                                            <div
                                                class="text-[var(--icon-tertiary)] absolute z-30 right-[6px] top-[50%] p-[6px] rounded-md transform -translate-y-1/2 cursor-pointer hover:text-[--icon-primary] active:opacity-90 transition-all"
                                                @click="showPassword = !showPassword">
                                                <Eye v-if="showPassword" :size="16" />
                                                <EyeOff v-else :size="16" />
                                            </div>
                                        </div>
                                        <div
                                            class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                                            :class="validationErrors.password ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                                            {{ validationErrors.password }}
                                        </div>
                                    </div>

                                    <!-- 确认密码字段（仅注册时显示） -->
                                    <div v-if="isRegistering" class="flex flex-col items-start">
                                        <div class="w-full flex items-center justify-between gap-[12px] mb-[8px]">
                                            <label for="confirmPassword"
                                                class="text-[13px] text-[var(--text-primary)] font-medium after:content-[&quot;*&quot;] after:text-[var(--function-error)] after:ml-[4px]">
                                                <span>确认密码</span>
                                            </label>
                                        </div>
                                        <div class="relative w-full">
                                            <input
                                                v-model="formData.confirmPassword"
                                                class="rounded-[10px] overflow-hidden text-sm leading-[22px] text-[var(--text-primary)] h-10 w-full disabled:cursor-not-allowed placeholder:text-[var(--text-disable)] bg-[var(--fill-input-chat)] pt-1 pb-1 pl-3 focus:ring-[1.5px] focus:ring-[var(--border-dark)] pr-[40px]"
                                                :class="{ 'ring-1 ring-[var(--function-error)]': validationErrors.confirmPassword }"
                                                placeholder="再次输入密码" 
                                                :type="showConfirmPassword ? 'text' : 'password'"
                                                :disabled="isLoading"
                                                @input="validateField('confirmPassword')"
                                                @blur="validateField('confirmPassword')">
                                            <div
                                                class="text-[var(--icon-tertiary)] absolute z-30 right-[6px] top-[50%] p-[6px] rounded-md transform -translate-y-1/2 cursor-pointer hover:text-[--icon-primary] active:opacity-90 transition-all"
                                                @click="showConfirmPassword = !showConfirmPassword">
                                                <Eye v-if="showConfirmPassword" :size="16" />
                                                <EyeOff v-else :size="16" />
                                            </div>
                                        </div>
                                        <div
                                            class="text-[13px] text-[var(--function-error)] leading-[18px] overflow-hidden transition-all duration-300 ease-out"
                                            :class="validationErrors.confirmPassword ? 'opacity-100 max-h-[60px] mt-[2px]' : 'opacity-0 max-h-0 mt-0'">
                                            {{ validationErrors.confirmPassword }}
                                        </div>
                                    </div>

                                    <!-- 提交按钮 -->
                                    <button
                                        type="submit"
                                        class="inline-flex items-center justify-center whitespace-nowrap font-medium transition-colors h-[40px] px-[16px] rounded-[10px] gap-[6px] text-sm min-w-16 w-full"
                                        :class="isFormValid && !isLoading 
                                            ? 'bg-[var(--Button-primary-black)] text-[var(--text-onblack)] hover:opacity-90 active:opacity-80' 
                                            : 'bg-[#898988] dark:bg-[#939393] text-[var(--text-onblack)] opacity-50 cursor-not-allowed'"
                                        :disabled="!isFormValid || isLoading">
                                        <LoaderCircle v-if="isLoading" :size="16" class="animate-spin" />
                                        <span>{{ isLoading ? '处理中...' : (isRegistering ? '注册' : '登录') }}</span>
                                    </button>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 切换登录/注册 -->
                        <div class="text-center text-[13px] leading-[18px] text-[var(--text-tertiary)] mt-[8px]">
                            <span>{{ isRegistering ? '已有账户？' : '没有账户？' }}</span>
                            <span
                                class="ms-[8px] text-[var(--text-secondary)] cursor-pointer select-none hover:opacity-80 active:opacity-70 transition-all underline"
                                @click="toggleMode">
                                {{ isRegistering ? '登录' : '注册' }}
                            </span>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Bot, Eye, EyeOff, LoaderCircle } from 'lucide-vue-next'
import ManusLogoTextIcon from '@/components/icons/ManusLogoTextIcon.vue'
import { useAuth } from '@/api'
import { validateUserInput } from '@/utils/auth'
import { showErrorToast, showSuccessToast } from '@/utils/toast'

const router = useRouter()
const { login, register, isLoading, authError, isAuthenticated, clearError } = useAuth()

// 表单状态
const isRegistering = ref(false)
const showPassword = ref(false)
const showConfirmPassword = ref(false)

// 表单数据
const formData = ref({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 验证错误
const validationErrors = ref<Record<string, string>>({})

// 切换登录/注册模式
const toggleMode = () => {
  isRegistering.value = !isRegistering.value
  clearForm()
}

// 清空表单
const clearForm = () => {
  formData.value = {
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  }
  validationErrors.value = {}
}

// 验证单个字段
const validateField = (field: string) => {
  const errors: Record<string, string> = {}
  
  if (field === 'username' && isRegistering.value) {
    const result = validateUserInput({ username: formData.value.username })
    if (result.errors.username) {
      errors.username = result.errors.username
    }
  }
  
  if (field === 'email') {
    const result = validateUserInput({ email: formData.value.email })
    if (result.errors.email) {
      errors.email = result.errors.email
    }
  }
  
  if (field === 'password') {
    const result = validateUserInput({ password: formData.value.password })
    if (result.errors.password) {
      errors.password = result.errors.password
    }
  }
  
  if (field === 'confirmPassword' && isRegistering.value) {
    if (formData.value.password !== formData.value.confirmPassword) {
      errors.confirmPassword = '两次密码输入不一致'
    }
  }
  
  // 更新错误状态
  Object.keys(errors).forEach(key => {
    validationErrors.value[key] = errors[key]
  })
  
  // 清除已修复的错误
  if (!errors[field]) {
    delete validationErrors.value[field]
  }
}

// 验证整个表单
const validateForm = () => {
  const data: any = {
    email: formData.value.email,
    password: formData.value.password
  }
  
  if (isRegistering.value) {
    data.username = formData.value.username
  }
  
  const result = validateUserInput(data)
  validationErrors.value = { ...result.errors }
  
  // 验证确认密码
  if (isRegistering.value && formData.value.password !== formData.value.confirmPassword) {
    validationErrors.value.confirmPassword = '两次密码输入不一致'
  }
  
  return Object.keys(validationErrors.value).length === 0
}

// 检查表单是否有效
const isFormValid = computed(() => {
  const hasRequiredFields = isRegistering.value
    ? formData.value.username.trim() && formData.value.email.trim() && formData.value.password.trim() && formData.value.confirmPassword.trim()
    : formData.value.email.trim() && formData.value.password.trim()
  
  const hasNoErrors = Object.keys(validationErrors.value).length === 0
  
  return hasRequiredFields && hasNoErrors
})

// 提交表单
const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }
  
  try {
    if (isRegistering.value) {
      await register({
        username: formData.value.username,
        email: formData.value.email,
        password: formData.value.password
      })
      // 注册成功提示
      showSuccessToast('注册成功！欢迎使用 Manus')
    } else {
      await login({
        username: formData.value.email, // 后端使用 username 字段，但可以接受邮箱
        password: formData.value.password
      })
      // 登录成功提示
      showSuccessToast('登录成功！欢迎回来')
    }
    
    // 成功后跳转到主页或用户之前访问的页面
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/')
  } catch (error: any) {
    console.error('Authentication failed:', error)
    // 使用 toast 显示错误信息
    showErrorToast(authError.value || '认证失败，请重试')
  }
}

// 监听认证状态变化
watch(isAuthenticated, (authenticated) => {
  if (authenticated) {
    const redirect = router.currentRoute.value.query.redirect as string
    router.push(redirect || '/')
  }
})

// 当原密码改变时，重新校验确认密码
watch(() => formData.value.password, () => {
  if (isRegistering.value && formData.value.confirmPassword) {
    validateField('confirmPassword')
  }
})

// 页面加载时检查是否已登录
onMounted(() => {
  if (isAuthenticated.value) {
    router.push('/')
  }
})
</script>