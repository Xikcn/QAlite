<script setup>
import { defineProps, defineEmits } from 'vue';

const props = defineProps({
  files: {
    type: Array,
    default: () => []
  },
  currentFile: {
    type: String,
    default: null
  }
});

const emit = defineEmits(['select-file', 'delete-file']);

function handleSelectFile(filename) {
  emit('select-file', filename);
}

function handleDeleteFile(event, filename) {
  event.stopPropagation();
  if (confirm(`确定要删除文件 ${filename} 吗？`)) {
    emit('delete-file', filename);
  }
}
</script>

<template>
  <div class="ios-file-list">
    <div v-if="files.length === 0" class="ios-empty-state">
      <div class="ios-empty-icon">📂</div>
      <p class="ios-empty-text">暂无文件</p>
    </div>
    
    <ul v-else class="ios-files">
      <li 
        v-for="file in files" 
        :key="file" 
        class="ios-file-item"
        :class="{ 'active': file === currentFile }"
        @click="handleSelectFile(file)"
      >
        <div class="ios-file-icon">
          <span class="ios-icon">
            <span>📝</span>
          </span>
        </div>
        <div class="ios-file-details">
          <span class="ios-file-name">{{ file }}</span>
          <span class="ios-file-time">{{ new Date().toLocaleDateString() }}</span>
        </div>
        <button 
          class="ios-file-action" 
          @click="(event) => handleDeleteFile(event, file)"
          aria-label="删除文件"
        >
          <span class="ios-action-icon">🗑️</span>
        </button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.ios-file-list {
  width: 100%;
}

.ios-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  color: var(--text-secondary);
  text-align: center;
}

.ios-empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.6;
}

.ios-empty-text {
  font-size: 15px;
}

.ios-files {
  list-style: none;
  padding: 0;
  margin: 0;
  border-radius: 10px;
  overflow: hidden;
  background-color: var(--bg-secondary);
}

.ios-file-item {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--bg-tertiary);
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;
}

.ios-file-item:last-child {
  border-bottom: none;
}

.ios-file-item.active {
  background-color: rgba(0, 122, 255, 0.1);
}

.dark-mode .ios-file-item.active {
  background-color: rgba(10, 132, 255, 0.2);
}

.ios-file-item:active {
  background-color: var(--bg-tertiary);
}

.ios-file-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  font-size: 20px;
}

.ios-file-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.ios-file-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ios-file-time {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.ios-file-action {
  background: none;
  border: none;
  color: var(--danger-color);
  padding: 8px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 16px;
  opacity: 0.8;
  transition: opacity 0.2s, transform 0.2s;
}

.ios-file-action:active {
  opacity: 1;
  transform: scale(0.92);
}
</style> 