<script setup>
import { ref, onMounted } from 'vue';
import QAEditor from './components/QAEditor.vue';
import FileList from './components/FileList.vue';
import CreateFileForm from './components/CreateFileForm.vue';
import SearchBar from './components/SearchBar.vue';
import { nanoid } from 'nanoid';
import { motion, useScroll, useSpring } from 'motion-v';

// 状态管理
const files = ref([]);
const currentFile = ref(null);
const loading = ref(false);
const error = ref('');
const searchResults = ref([]);
const showSearch = ref(false);
const showSearchBar = ref(false);
const isDarkMode = ref(false);

const API_URL = 'http://localhost:8000/api';

// 滚动动画相关
const mainContainer = ref(null);
const { scrollYProgress } = useScroll();
// 使用spring使动画更平滑
const smoothProgress = useSpring(scrollYProgress, {
  stiffness: 100,
  damping: 30,
  restDelta: 0.001
});

// 获取所有文件列表
async function fetchFiles() {
  loading.value = true;
  try {
    const response = await fetch(`${API_URL}/files`);
    if (!response.ok) throw new Error('获取文件列表失败');
    files.value = await response.json();
  } catch (err) {
    error.value = err.message;
    console.error(err);
  } finally {
    loading.value = false;
  }
}

// 获取特定文件内容
async function fetchFile(filename) {
  loading.value = true;
  try {
    const response = await fetch(`${API_URL}/files/${filename}`);
    if (!response.ok) throw new Error(`获取文件 ${filename} 失败`);
    currentFile.value = await response.json();
  } catch (err) {
    error.value = err.message;
    console.error(err);
  } finally {
    loading.value = false;
  }
}

// 创建新文件
async function createFile(fileData) {
  loading.value = true;
  error.value = ''; // 清除之前的错误
  
  try {
    // 添加一个空的问答卡片
    const fileDataWithEmptyQA = {
      ...fileData,
      qa_pairs: [{ question: '', answer: '' }]
    };
    
    const response = await fetch(`${API_URL}/files`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(fileDataWithEmptyQA),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      const errorStatus = response.status;
      
      // 特殊处理409状态码（文件已存在）
      if (errorStatus === 409) {
        throw new Error(errorData.detail || `文件 '${fileData.filename}' 已存在，请使用其他名称`);
      } else {
        throw new Error(errorData.detail || '创建文件失败');
      }
    }
    
    const newFile = await response.json();
    files.value.push(newFile.filename);
    currentFile.value = newFile;
  } catch (err) {
    error.value = err.message;
    console.error("创建文件错误:", err.message);
  } finally {
    loading.value = false;
  }
}

// 更新文件内容
async function updateFile(qaData) {
  if (!currentFile.value) return;
  
  // 检查数据是否真正变化
  const currentQAString = JSON.stringify(currentFile.value.qa_pairs || []);
  const newQAString = JSON.stringify(qaData || []);
  
  // 只有当数据真正变化时才发送更新请求
  if (currentQAString === newQAString) {
    console.log("数据未变化，跳过更新请求");
    return;
  }
  
  loading.value = true;
  try {
    const response = await fetch(`${API_URL}/files/${currentFile.value.filename}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        filename: currentFile.value.filename,
        qa_pairs: qaData,
      }),
    });
    
    if (!response.ok) throw new Error('更新文件失败');
    
    // 只更新qa_pairs，保持其他状态不变
    const updatedFile = await response.json();
    currentFile.value = {
      ...currentFile.value,
      qa_pairs: updatedFile.qa_pairs,
      content: updatedFile.content
    };
  } catch (err) {
    error.value = err.message;
    console.error(err);
  } finally {
    loading.value = false;
  }
}

// 添加单个QA对
async function addSingleQA(question, answer) {
  if (!currentFile.value) return false;
  
  console.log("App.vue 开始添加单个QA对:", question, answer);
  loading.value = true;
  try {
    const response = await fetch(`${API_URL}/files/${currentFile.value.filename}/qa`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: question,
        answer: answer
      }),
    });
    
    if (!response.ok) {
      console.error("添加问答对API请求失败:", response.status);
      throw new Error('添加问答对失败');
    }
    
    console.log("添加问答对API请求成功");
    
    // 只更新qa_pairs，保持其他状态不变
    const updatedFile = await response.json();
    console.log("新问答对数量:", updatedFile.qa_pairs.length);
    
    currentFile.value = {
      ...currentFile.value,
      qa_pairs: updatedFile.qa_pairs,
      content: updatedFile.content
    };
    
    return true;
  } catch (err) {
    console.error("添加问答对错误:", err.message);
    error.value = err.message;
    return false;
  } finally {
    loading.value = false;
  }
}

// 删除单个QA对
async function deleteSingleQA(index) {
  if (!currentFile.value) return;
  
  loading.value = true;
  try {
    const response = await fetch(`${API_URL}/files/${currentFile.value.filename}/qa/${index}`, {
      method: 'DELETE'
    });
    
    if (!response.ok) throw new Error('删除问答对失败');
    
    // 只更新qa_pairs，保持其他状态不变
    const updatedFile = await response.json();
    currentFile.value = {
      ...currentFile.value,
      qa_pairs: updatedFile.qa_pairs,
      content: updatedFile.content
    };
    
    return true;
  } catch (err) {
    error.value = err.message;
    console.error(err);
    return false;
  } finally {
    loading.value = false;
  }
}

// 删除文件
async function deleteFile(filename) {
  loading.value = true;
  try {
    const response = await fetch(`${API_URL}/files/${filename}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) throw new Error(`删除文件 ${filename} 失败`);
    
    files.value = files.value.filter(f => f !== filename);
    if (currentFile.value && currentFile.value.filename === filename) {
      currentFile.value = null;
    }
  } catch (err) {
    error.value = err.message;
    console.error(err);
  } finally {
    loading.value = false;
  }
}

// 搜索功能
async function searchQA(term) {
  if (!term) {
    searchResults.value = [];
    showSearch.value = false;
    return;
  }
  
  loading.value = true;
  try {
    // 使用全局搜索API，搜索所有文件
    const response = await fetch(`${API_URL}/search?query=${encodeURIComponent(term)}`);
    if (!response.ok) throw new Error('搜索失败');
    
    const results = await response.json();
    searchResults.value = results;
    showSearch.value = true;
    
    // 如果没有结果，显示信息
    if (results.length === 0) {
      error.value = `未找到与"${term}"相关的内容`;
      setTimeout(() => {
        error.value = '';  // 3秒后清除错误信息
      }, 3000);
    }
  } catch (err) {
    error.value = err.message;
    console.error("搜索错误:", err.message);
  } finally {
    loading.value = false;
  }
}

// 切换搜索栏显示
function toggleSearchBar() {
  showSearchBar.value = !showSearchBar.value;
  if (!showSearchBar.value) {
    showSearch.value = false; // 收起搜索栏时同时关闭搜索结果
  }
}

// 切换暗色/亮色模式
function toggleDarkMode() {
  isDarkMode.value = !isDarkMode.value;
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark-mode');
  } else {
    document.documentElement.classList.remove('dark-mode');
  }
  // 保存主题设置到本地存储
  localStorage.setItem('isDarkMode', isDarkMode.value);
}

// 初始加载
onMounted(() => {
  fetchFiles();
  
  // 从本地存储中读取主题设置
  const savedTheme = localStorage.getItem('isDarkMode');
  
  // 如果存在已保存的主题设置，使用该设置
  if (savedTheme !== null) {
    isDarkMode.value = savedTheme === 'true';
    if (isDarkMode.value) {
      document.documentElement.classList.add('dark-mode');
    } else {
      document.documentElement.classList.remove('dark-mode');
    }
  } 
  // 否则检查系统偏好
  else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    isDarkMode.value = true;
    document.documentElement.classList.add('dark-mode');
  }
});

// 处理搜索结果点击
async function handleSearchResultClick(result) {
  console.log("点击搜索结果:", result);
  
  // 如果结果中的文件与当前文件不同，先加载该文件
  if (!currentFile.value || currentFile.value.filename !== result.filename) {
    console.log("加载文件:", result.filename);
    await fetchFile(result.filename);
  }
  
  // 关闭搜索结果面板
  showSearch.value = false;
  
  // 减少延迟时间，加快响应速度
  setTimeout(() => {
    console.log("开始查找匹配卡片");
    
    // 找到问题和答案在qa_pairs中的索引
    const qaIndex = currentFile.value.qa_pairs.findIndex(qa => 
      qa.question.includes(result.question) && qa.answer.includes(result.answer)
    );
    
    console.log("匹配的问答对索引:", qaIndex);
    
    if (qaIndex !== -1) {
      // 减少等待时间
      setTimeout(() => {
        // 方法1：通过Vue组件实例调用方法
        try {
          const editorElement = document.querySelector('.qa-editor');
          if (editorElement && editorElement.__vnode && editorElement.__vnode.component) {
            console.log("找到QAEditor组件");
            const editorComponent = editorElement.__vnode.component.exposed;
            if (editorComponent && typeof editorComponent.navigateToIndex === 'function') {
              console.log("调用navigateToIndex方法");
              editorComponent.navigateToIndex(qaIndex, false); // 传入false参数，表示不使用平滑滚动
              return;
            }
          }
        } catch (e) {
          console.error("通过组件实例调用失败:", e);
        }
        
        console.log("尝试使用DOM方法");
        
        // 方法2：通过事件触发
        try {
          // 尝试通过事件触发跳转
          window.dispatchEvent(new CustomEvent('qalite-navigate', { 
            detail: { index: qaIndex, smooth: false } 
          }));
          return;
        } catch (e) {
          console.error("通过事件触发失败:", e);
        }
        
        // 方法3：最后尝试直接操作DOM
        try {
          const qaCards = document.querySelectorAll('.qa-card');
          console.log("找到卡片数量:", qaCards.length);
          
          if (qaIndex < qaCards.length) {
            const targetCard = qaCards[qaIndex];
            console.log("找到目标卡片:", targetCard);
            
            if (targetCard) {
              // 高亮显示并立即滚动到视图中(不使用平滑滚动)
              targetCard.classList.add('highlight-card');
              targetCard.scrollIntoView({ behavior: 'auto', block: 'center' });
              
              // 高亮显示3秒后移除
              setTimeout(() => {
                targetCard.classList.remove('highlight-card');
              }, 3000);
            }
          } else {
            console.log("卡片索引超出范围");
          }
        } catch (e) {
          console.error("通过DOM操作失败:", e);
        }
      }, 100); // 将300ms减少到100ms
    } else {
      console.log("在当前文件中未找到精确匹配的问答对，尝试文本匹配");
      
      // 使用文本匹配作为后备方案，减少延迟
      setTimeout(() => {
        try {
          const qaCards = document.querySelectorAll('.qa-card');
          console.log("文本匹配模式找到卡片数量:", qaCards.length);
          
          let found = false;
          
          for (let i = 0; i < qaCards.length; i++) {
            const questionEl = qaCards[i].querySelector('.qa-question-content');
            const answerEl = qaCards[i].querySelector('.qa-answer-content');
            
            if (!questionEl || !answerEl) continue;
            
            const questionText = questionEl.textContent || '';
            const answerText = answerEl.textContent || '';
            
            if (questionText.includes(result.question) && 
                answerText.includes(result.answer)) {
              console.log("通过文本内容找到匹配卡片:", i);
              
              // 找到匹配的卡片，高亮显示并立即滚动到视图中
              qaCards[i].classList.add('highlight-card');
              qaCards[i].scrollIntoView({ behavior: 'auto', block: 'center' });
              
              // 高亮显示3秒后移除
              setTimeout(() => {
                qaCards[i].classList.remove('highlight-card');
              }, 3000);
              
              found = true;
              break;
            }
          }
          
          if (!found) {
            console.log("无法找到匹配的卡片");
          }
        } catch (e) {
          console.error("文本匹配失败:", e);
        }
      }, 200); // 将500ms减少到200ms
    }
  }, 100); // 将300ms减少到100ms
}
</script>

<template>
  <div class="app-container" :class="{ 'dark-mode': isDarkMode }">
    <!-- iOS风格状态栏 -->
    <div class="status-bar">
      <div class="time">{{ new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}</div>
      <div class="status-icons">
        <span class="icon">📶</span>
        <span class="icon">📱</span>
        <span class="icon">🔋</span>
      </div>
    </div>
    
    <!-- 导航栏 -->
    <header class="ios-header">
      <div class="header-left">
        <h1 class="app-title">QAlite</h1>
      </div>
      
      <div class="header-right">
        <button v-if="currentFile" class="ios-button" @click="toggleSearchBar">
          <span class="icon">🔍</span>
        </button>
        <button class="ios-button" @click="toggleDarkMode">
          <span class="icon">{{ isDarkMode ? '☀️' : '🌙' }}</span>
        </button>
      </div>
    </header>

    <!-- 搜索栏 -->
    <div v-if="showSearchBar" class="search-container">
      <SearchBar @search="searchQA" />
    </div>

    <!-- 进度条 -->
    <motion.div class="progress-bar" :style="{ scaleX: smoothProgress }"></motion.div>

    <div class="main-container" ref="mainContainer">
      <!-- 左侧文件列表 -->
      <aside class="file-sidebar">
        <div class="files-list-container">
          <h2 class="section-title">文件列表</h2>
          <div class="files-stack-container">
            <motion.div
              v-for="(file, index) in files"
              :key="file"
              :initial="{ opacity: 0, y: 20 }"
              :whileInView="{ opacity: 1, y: 0 }"
              :inViewOptions="{ once: true }"
              :transition="{ delay: index * 0.1 }"
              class="file-card-wrapper"
              :class="{ 'active': currentFile?.filename === file }"
              :style="{ zIndex: files.length - index }"
              @click="fetchFile(file)"
            >
              <div class="stacked-file-card">
                <div class="file-card-content">
                  <div class="file-icon">📄</div>
                  <div class="file-name">{{ file }}</div>
                  <div class="file-date">{{ new Date().toLocaleDateString() }}</div>
                </div>
                <button 
                  v-if="currentFile?.filename !== file" 
                  class="delete-icon" 
                  @click.stop="deleteFile(file)"
                >
                  🗑️
                </button>
              </div>
            </motion.div>
          </div>
        </div>
        
        <div class="create-form-container">
          <h2 class="section-title">创建新文件</h2>
          <CreateFileForm @create="createFile" :error="error" />
        </div>
      </aside>

      <!-- 主内容区 -->
      <main class="ios-main">
        <div v-if="loading" class="ios-loading">
          <div class="loading-spinner"></div>
          <div class="loading-text">加载中...</div>
        </div>
        <div v-else-if="error && !currentFile" class="ios-error">
          <div class="error-icon">❌</div>
          <div class="error-text">{{ error }}</div>
          <button class="ios-button primary" @click="fetchFiles">重试</button>
        </div>
        <div v-else-if="!currentFile" class="ios-welcome">
          <motion.div
            :initial="{ opacity: 0, scale: 0.8 }"
            :whileInView="{ opacity: 1, scale: 1 }"
            :transition="{ type: 'spring', stiffness: 300, damping: 20 }"
          >
            <div class="welcome-icon">📝</div>
            <h2>欢迎使用QAlite</h2>
            <p>请从左侧选择一个文件或创建新文件开始使用。</p>
          </motion.div>
        </div>
        <div v-else class="ios-content">
          <div class="ios-file-header">
            <h2 class="file-title">{{ currentFile.filename }}</h2>
          </div>
          
          <div v-if="showSearch" class="ios-search-results">
            <div class="results-header">
              <h3>搜索结果</h3>
              <button class="ios-button close" @click="showSearch = false">×</button>
            </div>
            <div v-if="searchResults.length === 0" class="no-results">
              未找到匹配结果
            </div>
            <div v-else class="results-list">
              <motion.div
                v-for="(result, index) in searchResults"
                :key="index"
                :initial="{ opacity: 0, x: -20 }"
                :whileInView="{ opacity: 1, x: 0 }"
                :transition="{ delay: index * 0.05 }"
                class="result-item"
                @click="() => handleSearchResultClick(result)"
              >
                <div class="result-filename">{{ result.filename }}</div>
                <div class="result-question">{{ result.question }}</div>
                <div class="result-answer">{{ result.answer }}</div>
              </motion.div>
            </div>
          </div>
          
          <QAEditor 
            v-else
            :qa-pairs="currentFile.qa_pairs || []" 
            @update="updateFile" 
            :addSingleQA="addSingleQA"
            :deleteSingleQA="deleteSingleQA"
          />
        </div>
      </main>
    </div>
  </div>
</template>

<style>
:root {
  --text-primary: #000000;
  --text-secondary: #666666;
  --bg-primary: #f2f2f7;
  --bg-secondary: #ffffff;
  --bg-tertiary: #e5e5ea;
  --accent-color: #007aff;
  --accent-color-light: #409cff;
  --success-color: #34c759;
  --warning-color: #ff9500;
  --danger-color: #ff3b30;
  --border-radius: 10px;
  --header-height: 44px;
  --status-bar-height: 20px;
  --tab-bar-height: 49px;
  --sidebar-width: 80%;
}

.dark-mode {
  --text-primary: #ffffff;
  --text-secondary: #ebebf5;
  --bg-primary: #1c1c1e;
  --bg-secondary: #2c2c2e;
  --bg-tertiary: #3a3a3c;
  --accent-color: #0a84ff;
  --accent-color-light: #5ac8fa;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
  -webkit-tap-highlight-color: transparent;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

html, body {
  height: 100%;
  width: 100%;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', sans-serif;
}

body {
  color: var(--text-primary);
  background-color: var(--bg-primary);
  margin: 0;
  padding: 0;
}

/* 应用容器 */
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  position: relative;
  background-color: var(--bg-primary);
  max-width: 100%;
}

/* 状态栏 */
.status-bar {
  height: var(--status-bar-height);
  padding: 0 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 12px;
  background-color: var(--bg-secondary);
}

.time {
  flex: 1;
  text-align: center;
}

.status-icons {
  display: flex;
  gap: 5px;
}

/* iOS风格导航栏 */
.ios-header {
  height: var(--header-height);
  padding: 0 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--bg-secondary);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 10;
}

.dark-mode .ios-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.app-title {
  font-size: 17px;
  font-weight: 600;
}

/* 进度条 */
.progress-bar {
  position: fixed;
  top: calc(var(--status-bar-height) + var(--header-height));
  left: 0;
  right: 0;
  height: 4px;
  background: var(--accent-color);
  transform-origin: 0%;
  z-index: 100;
}

/* iOS风格按钮 */
.ios-button {
  background: none;
  border: none;
  color: var(--accent-color);
  font-size: 17px;
  padding: 8px;
  cursor: pointer;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: opacity 0.2s;
}

.ios-button:active {
  opacity: 0.6;
}

.ios-button.primary {
  background-color: var(--accent-color);
  color: white;
  padding: 8px 16px;
  font-weight: 600;
}

.ios-button.close {
  font-size: 24px;
  padding: 4px 8px;
}

/* 搜索容器 */
.search-container {
  background-color: var(--bg-secondary);
  padding: 8px 16px;
  z-index: 90;
}

/* 主容器和文件列表 */
.main-container {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
  height: calc(100vh - var(--status-bar-height) - var(--header-height));
}

.file-sidebar {
  width: 250px;
  background-color: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
  height: 100%;
  position: relative;
}

.dark-mode .file-sidebar {
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.files-list-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  padding-bottom: 8px;
}

.create-form-container {
  padding: 16px;
  background-color: var(--bg-secondary);
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  position: sticky;
  bottom: 0;
}

.dark-mode .create-form-container {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

/* 堆叠卡片样式 */
.files-stack-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
  padding: 20px 0;
}

.file-card-wrapper {
  position: relative;
  transition: transform 0.3s ease;
  cursor: pointer;
}

.file-card-wrapper:hover {
  transform: translateY(-5px);
}

.file-card-wrapper.active {
  transform: scale(1.05);
}

.file-card-wrapper.active .stacked-file-card {
  background-color: rgba(0, 122, 255, 0.1);
  border: 2px solid var(--accent-color);
  box-shadow: 0 6px 16px rgba(0, 122, 255, 0.2);
}

.dark-mode .file-card-wrapper.active .stacked-file-card {
  background-color: rgba(10, 132, 255, 0.15);
  box-shadow: 0 6px 16px rgba(10, 132, 255, 0.3);
}

.file-card-wrapper.active .file-name {
  color: var(--accent-color);
  font-weight: 700;
}

.file-card-wrapper.active::before {
  content: '';
  position: absolute;
  left: -4px;
  top: 0;
  height: 100%;
  width: 4px;
  background-color: var(--accent-color);
  border-radius: 2px;
}

.stacked-file-card {
  background-color: var(--bg-secondary);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  padding: 16px;
  position: relative;
  overflow: hidden;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border: 1px solid rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.dark-mode .stacked-file-card {
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.stacked-file-card::before {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 2px;
  right: 2px;
  height: 10px;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 0 0 10px 10px;
  z-index: -1;
}

.stacked-file-card::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 4px;
  right: 4px;
  height: 10px;
  background-color: rgba(0, 0, 0, 0.03);
  border-radius: 0 0 10px 10px;
  z-index: -2;
}

.file-card-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.file-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.file-date {
  font-size: 12px;
  color: var(--text-secondary);
}

.delete-icon {
  background: none;
  border: none;
  font-size: 18px;
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
  color: var(--danger-color);
}

.stacked-file-card:hover .delete-icon {
  opacity: 1;
}

.section-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 16px;
}

/* 主内容区 */
.ios-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: calc(100% - 250px);
}

.ios-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow-y: auto;
  width: 100%;
}

.ios-file-header {
  padding: 16px;
  text-align: center;
  background-color: var(--bg-secondary);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.dark-mode .ios-file-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.file-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--accent-color);
}

/* 加载、错误和欢迎页面 */
.ios-loading, .ios-error, .ios-welcome {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  text-align: center;
  padding: 32px;
  gap: 16px;
}

.loading-spinner {
  width: 30px;
  height: 30px;
  border: 3px solid var(--accent-color-light);
  border-top: 3px solid var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: var(--text-secondary);
  font-weight: 500;
}

.error-icon, .welcome-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.error-text {
  color: var(--danger-color);
  margin-bottom: 16px;
  font-weight: 500;
}

/* 搜索结果 */
.ios-search-results {
  background-color: var(--bg-secondary);
  border-radius: var(--border-radius);
  margin: 16px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.dark-mode .ios-search-results {
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--bg-tertiary);
}

.no-results {
  padding: 20px;
  text-align: center;
  color: var(--text-secondary);
}

.results-list {
  max-height: 60vh;
  overflow-y: auto;
}

.result-item {
  padding: 16px;
  border-bottom: 1px solid var(--bg-tertiary);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.result-item:hover {
  background-color: rgba(0, 122, 255, 0.05);
  transform: translateX(5px);
}

.result-item:active {
  background-color: rgba(0, 122, 255, 0.1);
  transform: translateX(3px);
}

.result-item::after {
  content: '↗';
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--accent-color);
  font-size: 14px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.result-item:hover::after {
  opacity: 1;
}

.result-filename {
  font-size: 0.8rem;
  color: var(--accent-color);
  margin-bottom: 4px;
  font-weight: 500;
}

.result-question {
  font-weight: 600;
  margin-bottom: 8px;
}

.result-answer {
  color: var(--text-secondary);
  white-space: pre-wrap;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .file-sidebar {
    width: 200px;
  }
  
  .ios-main {
    width: calc(100% - 200px);
  }
}

/* 搜索结果高亮卡片样式 */
.highlight-card {
  animation: highlight-pulse 2s ease;
  border: 2px solid var(--accent-color) !important;
  box-shadow: 0 0 15px rgba(0, 122, 255, 0.4) !important;
  transform: scale(1.02);
  z-index: 10;
  position: relative;
}

.dark-mode .highlight-card {
  box-shadow: 0 0 15px rgba(10, 132, 255, 0.5) !important;
}

@keyframes highlight-pulse {
  0% {
    box-shadow: 0 0 5px rgba(0, 122, 255, 0.2);
  }
  50% {
    box-shadow: 0 0 20px rgba(0, 122, 255, 0.6);
  }
  100% {
    box-shadow: 0 0 5px rgba(0, 122, 255, 0.2);
  }
}

@media (max-width: 576px) {
  .main-container {
    flex-direction: column;
  }
  
  .file-sidebar {
    width: 100%;
    height: auto;
    max-height: 30vh;
    border-right: none;
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  }
  
  .dark-mode .file-sidebar {
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .ios-main {
    width: 100%;
    height: 70vh;
  }
}

@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
  }
}
</style>
