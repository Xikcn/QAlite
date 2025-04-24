<script setup>
import { ref, watch } from 'vue';

const emit = defineEmits(['search']);

const searchTerm = ref('');
const isSearching = ref(false);
let debounceTimer = null;

// 监听搜索输入，带防抖
watch(searchTerm, (newValue) => {
  isSearching.value = true;
  
  // 清除之前的计时器
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  
  // 设置新的防抖计时器
  debounceTimer = setTimeout(() => {
    emit('search', newValue);
    isSearching.value = false;
  }, 300);
});

// 立即搜索
function searchNow() {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  
  isSearching.value = true;
  emit('search', searchTerm.value);
  
  setTimeout(() => {
    isSearching.value = false;
  }, 200);
}

// 清空搜索
function clearSearch() {
  searchTerm.value = '';
  emit('search', '');
}
</script>

<template>
  <div class="ios-search-bar-container">
    <div class="ios-search-bar">
      <div class="ios-search-icon">
        <span>🔍</span>
      </div>
      
      <input
        v-model="searchTerm"
        type="text"
        class="ios-search-input"
        placeholder="搜索问题或答案..."
        @keyup.enter="searchNow"
      />
      
      <button 
        v-if="searchTerm" 
        class="ios-clear-button"
        @click="clearSearch"
        aria-label="清空搜索"
      >
        <span>✕</span>
      </button>
      
      <div v-if="isSearching" class="ios-search-spinner"></div>
    </div>
    
    <button 
      class="ios-search-button" 
      @click="searchNow"
      :disabled="!searchTerm.trim()"
    >
      搜索
    </button>
  </div>
</template>

<style scoped>
.ios-search-bar-container {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.ios-search-bar {
  flex: 1;
  display: flex;
  align-items: center;
  position: relative;
  background-color: var(--bg-tertiary);
  border-radius: 10px;
  padding: 4px 8px;
  transition: background-color 0.2s;
}

.ios-search-bar:focus-within {
  background-color: var(--bg-secondary);
  box-shadow: 0 0 0 1px var(--accent-color);
}

.ios-search-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  color: var(--text-secondary);
  font-size: 16px;
}

.ios-search-input {
  flex: 1;
  height: 36px;
  border: none;
  background: transparent;
  padding: 0 8px;
  font-size: 17px;
  color: var(--text-primary);
  -webkit-appearance: none;
  appearance: none;
}

.ios-search-input:focus {
  outline: none;
}

.ios-search-input::placeholder {
  color: var(--text-secondary);
  opacity: 0.7;
}

.ios-clear-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  font-size: 12px;
  margin-right: 4px;
  transition: background-color 0.2s;
}

.ios-clear-button:active {
  background-color: var(--text-secondary);
  color: var(--bg-secondary);
}

.ios-search-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-top: 2px solid var(--accent-color);
  border-radius: 50%;
  margin-right: 8px;
  animation: spin 0.8s linear infinite;
}

.dark-mode .ios-search-spinner {
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-top: 2px solid var(--accent-color);
}

.ios-search-button {
  background-color: var(--accent-color);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.2s, opacity 0.2s;
  white-space: nowrap;
}

.ios-search-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ios-search-button:not(:disabled):active {
  transform: scale(0.98);
  background-color: var(--accent-color-light);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 480px) {
  .ios-search-button {
    padding: 8px 12px;
    font-size: 14px;
  }
}
</style> 