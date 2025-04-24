<script setup>
import { ref, defineProps, defineEmits, watchEffect } from 'vue';

const props = defineProps({
  error: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['create']);

const filename = ref('');
const isSubmitting = ref(false);
const errorMessage = ref('');

// 监听外部错误
watchEffect(() => {
  if (props.error && props.error.includes('已存在')) {
    errorMessage.value = props.error;
  }
});

function submitForm() {
  // 验证文件名
  if (!filename.value.trim()) {
    errorMessage.value = '请输入文件名';
    return;
  }
  
  // 清除错误信息
  errorMessage.value = '';
  
  // 设置提交状态
  isSubmitting.value = true;
  
  // 构造文件对象并发射事件
  const fileData = {
    filename: filename.value.trim().endsWith('.md') 
      ? filename.value.trim() 
      : `${filename.value.trim()}.md`
  };
  
  // 发射创建事件
  emit('create', fileData);
  
  // 重置表单
  setTimeout(() => {
    if (!errorMessage.value) {
      filename.value = '';
    }
    isSubmitting.value = false;
  }, 300);
}
</script>

<template>
  <div class="ios-create-form">
    <div class="ios-form-group">
      <input
        v-model="filename"
        type="text"
        class="ios-text-field"
        placeholder="输入文件名... (.md 将自动添加)"
        :disabled="isSubmitting"
        @keyup.enter="submitForm"
        @focus="errorMessage = ''"
      >
      <span v-if="errorMessage" class="ios-error-message">{{ errorMessage }}</span>
    </div>
    
    <button 
      @click="submitForm" 
      class="ios-button" 
      :disabled="isSubmitting || !filename.trim()"
    >
      <span v-if="isSubmitting" class="ios-spinner"></span>
      <span v-else>创建文件</span>
    </button>
  </div>
</template>

<style scoped>
.ios-create-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

.ios-form-group {
  display: flex;
  flex-direction: column;
  position: relative;
}

.ios-text-field {
  padding: 12px 16px;
  font-size: 16px;
  border-radius: 8px;
  border: 1px solid var(--bg-tertiary);
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  transition: border-color 0.2s, box-shadow 0.2s;
  -webkit-appearance: none;
  appearance: none;
}

.ios-text-field:focus {
  outline: none;
  border-color: var(--accent-color);
  box-shadow: 0 0 0 1px var(--accent-color);
}

.ios-text-field::placeholder {
  color: var(--text-secondary);
  opacity: 0.7;
}

.ios-error-message {
  color: var(--danger-color);
  font-size: 12px;
  margin-top: 8px;
  padding-left: 4px;
}

.ios-button {
  background-color: var(--accent-color);
  color: white;
  border: none;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.2s;
}

.ios-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ios-button:not(:disabled):active {
  transform: scale(0.98);
  background-color: var(--accent-color-light);
}

.ios-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 