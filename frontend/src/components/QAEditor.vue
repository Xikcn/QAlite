<script setup>
import { ref, computed, watchEffect, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  qaPairs: {
    type: Array,
    default: () => []
  },
  addSingleQA: {
    type: Function,
    default: null
  },
  deleteSingleQA: {
    type: Function,
    default: null
  }
});

const emit = defineEmits(['update']);

// 本地状态
const localQaPairs = ref([]);

// 当前编辑的索引
const currentIndex = ref(0);

// 编辑器容器DOM引用
const editorContainer = ref(null);

// 动画状态
const isAnimating = ref(false);

// 输入状态 - 用于跟踪是否有未保存的修改
const hasUnsavedChanges = ref(false);

// 延迟保存的定时器
let autoSaveTimer = null;

// 布局设置
const isCombinedView = ref(false);

// 本地存储键
const CURRENT_INDEX_KEY = 'qalite-current-index';
const VIEW_MODE_KEY = 'qalite-view-mode';

// 添加复习模式相关的状态
const isRevisionMode = ref(false);
const isRandomMode = ref(false);
const isAnswerVisible = ref(false);
const revisionIndex = ref(0);
const revisionOrder = ref([]);
const userAnswers = ref([]);

// 从本地存储加载设置
function loadSettings() {
  const savedIndex = localStorage.getItem(CURRENT_INDEX_KEY);
  if (savedIndex !== null) {
    const index = parseInt(savedIndex);
    if (!isNaN(index)) {
      currentIndex.value = index;
    }
  }
  
  const savedViewMode = localStorage.getItem(VIEW_MODE_KEY);
  if (savedViewMode !== null) {
    isCombinedView.value = savedViewMode === 'combined';
  }
}

// 保存设置到本地存储
function saveSettings() {
  localStorage.setItem(CURRENT_INDEX_KEY, currentIndex.value.toString());
  localStorage.setItem(VIEW_MODE_KEY, isCombinedView.value ? 'combined' : 'separate');
}

// 复制props中的数据到本地状态
watchEffect(() => {
  if (props.qaPairs && props.qaPairs.length) {
    // 记录当前索引位置
    const currentIdx = currentIndex.value;
    // 更新本地数据
    localQaPairs.value = JSON.parse(JSON.stringify(props.qaPairs));
    // 确保索引不超过数组长度
    if (currentIdx < localQaPairs.value.length) {
      currentIndex.value = currentIdx;
    } else {
      currentIndex.value = Math.max(0, localQaPairs.value.length - 1);
    }
  } else {
    // 如果没有数据，至少提供一个空的问答对
    localQaPairs.value = [{ question: '', answer: '' }];
    currentIndex.value = 0;
  }
});

// 计算当前可编辑的问答对
const currentQA = computed(() => {
  if (currentIndex.value >= localQaPairs.value.length) {
    currentIndex.value = Math.max(0, localQaPairs.value.length - 1);
  }
  return localQaPairs.value[currentIndex.value] || { question: '', answer: '' };
});

// 添加新的问答对
async function addNewQA() {
  // 验证当前问答对至少一个不为空
  const current = currentQA.value;
  if (!current.question.trim() && !current.answer.trim()) {
    console.log("当前问答对为空，不添加新问答对");
    return; // 不允许添加新的空问答对
  }
  
  // 保存当前内容
  if (hasUnsavedChanges.value) {
    await saveChanges();
  }
  
  console.log("开始添加新的QA对");
  
  // 使用单个QA添加API（如果可用）
  if (props.addSingleQA) {
    console.log("使用单个QA API添加");
    // 直接使用API添加空QA对
    const success = await props.addSingleQA('', '');
    if (success) {
      console.log("API添加成功，更新索引");
      // API成功，导航到最后一个QA对（新添加的）
      currentIndex.value = localQaPairs.value.length;
      saveSettings();
      
      // 在下一个渲染循环中尝试聚焦新创建的问题输入框
      setTimeout(() => {
        const questionInputs = document.querySelectorAll('.question-card textarea');
        if (questionInputs.length > 0) {
          const lastInput = questionInputs[questionInputs.length - 1];
          lastInput.focus();
        }
      }, 50);
      return;
    } else {
      console.log("API添加失败，使用本地添加");
    }
  } else {
    console.log("未提供addSingleQA API");
  }
  
  // 如果API不可用或失败，回退到整体更新
  console.log("回退到本地添加");
  const newQA = { question: '', answer: '' };
  localQaPairs.value.push(newQA);
  currentIndex.value = localQaPairs.value.length - 1;
  saveSettings();
  await updateParent();
  console.log("本地添加完成，当前索引:", currentIndex.value);
  
  // 聚焦到新的输入框
  setTimeout(() => {
    const questionInputs = document.querySelectorAll('.question-card textarea');
    if (questionInputs.length > 0) {
      const lastInput = questionInputs[questionInputs.length - 1];
      lastInput.focus();
    }
  }, 50);
}

// 删除当前问答对
async function deleteCurrentQA() {
  const index = currentIndex.value;
  
  // 如果只有一个问答对，清空它而不是删除
  if (localQaPairs.value.length <= 1) {
    localQaPairs.value = [{ question: '', answer: '' }];
    currentIndex.value = 0;
    updateParent();
    
    // 聚焦到清空后的输入框
    setTimeout(() => {
      const questionInput = document.querySelector('.question-card textarea');
      if (questionInput) {
        questionInput.focus();
      }
    }, 50);
    
    return;
  }
  
  // 使用单个QA删除API（如果可用）
  if (props.deleteSingleQA) {
    const success = await props.deleteSingleQA(index);
    if (success) {
      // API成功，调整currentIndex
      currentIndex.value = Math.min(currentIndex.value, localQaPairs.value.length - 2);
      saveSettings();
      
      // 聚焦到当前显示的问答对
      setTimeout(() => {
        const currentQuestionInput = document.querySelector('.current .question-card textarea');
        if (currentQuestionInput) {
          currentQuestionInput.focus();
        }
      }, 50);
      
      return;
    }
  }
  
  // 如果API不可用或失败，回退到整体更新
  localQaPairs.value.splice(index, 1);
  currentIndex.value = Math.min(index, localQaPairs.value.length - 1);
  saveSettings();
  updateParent();
  hasUnsavedChanges.value = false;
  
  // 聚焦到当前显示的问答对
  setTimeout(() => {
    const currentQuestionInput = document.querySelector('.current .question-card textarea');
    if (currentQuestionInput) {
      currentQuestionInput.focus();
    }
  }, 50);
}

// 更新父组件数据
function updateParent() {
  // 记录当前索引
  const currentIdx = currentIndex.value;
  
  // 过滤掉完全为空的问答对
  const filteredQaPairs = localQaPairs.value.filter(
    qa => qa.question.trim() || qa.answer.trim()
  );
  
  if (filteredQaPairs.length === 0) {
    // 确保至少有一个空问答对
    filteredQaPairs.push({ question: '', answer: '' });
  }
  
  // 检查数据是否真正发生变化
  const currentQaPairsJson = JSON.stringify(props.qaPairs);
  const newQaPairsJson = JSON.stringify(filteredQaPairs);
  
  // 只有当数据真正变化时才触发更新
  if (currentQaPairsJson !== newQaPairsJson) {
  // 发送更新到父组件
  emit('update', filteredQaPairs);
  }
  
  // 如果过滤后的数组长度发生变化，可能需要调整当前索引
  if (filteredQaPairs.length !== localQaPairs.value.length) {
    localQaPairs.value = filteredQaPairs;
    // 确保当前索引有效
    currentIndex.value = Math.min(currentIdx, filteredQaPairs.length - 1);
    saveSettings();
  }
}

// 处理输入变化
function handleInput(event) {
  // 标记为有未保存的更改
  hasUnsavedChanges.value = true;
  
  // 清除之前的定时器 - 不再需要
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer);
    autoSaveTimer = null;
  }
  
  // 不再设置自动保存定时器，只标记变更状态
  
  // 自动调整文本区域高度
  if (event && event.target) {
    autoResize(event);
  }
}

// 立即保存更改
async function saveChanges() {
  if (hasUnsavedChanges.value) {
    // 简化保存逻辑，避免不必要的DOM操作
    updateParent();
    hasUnsavedChanges.value = false;
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer);
      autoSaveTimer = null;
    }
    saveSettings();
  }
}

// 选择卡片
function selectCard(index) {
  if (!isAnimating.value && index !== currentIndex.value) {
    // 保存当前卡片的内容
    saveChanges();
    navigateTo(index);
  }
}

// 自动调整文本框大小
function autoResize(event) {
  const textarea = event.target;
  textarea.style.height = 'auto';
  textarea.style.height = textarea.scrollHeight + 'px';
}

// 切换布局模式
function toggleViewMode() {
  // 保存当前内容
  saveChanges();
  isCombinedView.value = !isCombinedView.value;
  saveSettings();
}

// 导航到指定索引
function navigateTo(index) {
  if (isAnimating.value) return;
  
  if (index >= 0 && index < localQaPairs.value.length && index !== currentIndex.value) {
    // 保存当前卡片的内容
    if (hasUnsavedChanges.value) {
      saveChanges();
    }
    
    isAnimating.value = true;
    currentIndex.value = index;
    saveSettings();
    
    // 动画完成后重置状态，减少动画时间
    setTimeout(() => {
      isAnimating.value = false;
    }, 300); // 从400ms减少到300ms
  }
}

// 导航到相对位置
async function navigateRelative(direction) {
  // 首先保存当前内容
  if (hasUnsavedChanges.value) {
    await saveChanges();
  }
  
  if (direction === 'prev' && currentIndex.value > 0) {
    navigateTo(currentIndex.value - 1);
  } else if (direction === 'next' && currentIndex.value < localQaPairs.value.length - 1) {
    navigateTo(currentIndex.value + 1);
  } else if (direction === 'next' && currentIndex.value === localQaPairs.value.length - 1) {
    // 如果在最后一个项目，并且尝试导航到下一个，添加新问答对
    console.log("点击下一个，当前是最后一张卡片");
    const current = currentQA.value;
    if (current.question.trim() || current.answer.trim()) {
      console.log("当前卡片有内容，创建新卡片");
      await addNewQA(); // 使用优化后的addNewQA函数
    }
  }
  
  // 等待视图更新后，尝试聚焦到合适的输入框
  setTimeout(() => {
    const newQuestionInput = document.querySelector('.current .question-card textarea');
    if (newQuestionInput) {
      newQuestionInput.focus();
    }
  }, 50);
}

// 处理鼠标滚轮事件
async function handleWheel(event) {
  // 阻止默认行为，避免页面滚动
  event.preventDefault();
  
  // 如果正在动画中，不进行处理
  if (isAnimating.value) return;
  
  // 如果有未保存的更改，先保存
  if (hasUnsavedChanges.value) {
    await saveChanges();
  }

  // 根据滚动方向导航到下一个或上一个卡片
  if (event.deltaY > 0) {
    // 向下滚动，检查是否是最后一张卡片
    if (currentIndex.value === localQaPairs.value.length - 1) {
      // 最后一张卡片，创建新卡片而不是循环到第一张
      const lastQa = localQaPairs.value[currentIndex.value];
      // 只有当最后一张卡片有内容时才创建新卡片
      if (lastQa.question.trim() || lastQa.answer.trim()) {
        await addNewQA();
      }
    } else {
      // 不是最后一张卡片，正常导航到下一张
      navigateTo(currentIndex.value + 1);
      
      // 等待视图更新后，尝试聚焦到合适的输入框
      setTimeout(() => {
        const newQuestionInput = document.querySelector('.current .question-card textarea');
        if (newQuestionInput) {
          newQuestionInput.focus();
        }
      }, 50);
    }
  } else if (event.deltaY < 0) {
    // 向上滚动，检查是否是第一张卡片
    if (currentIndex.value > 0) {
      // 不是第一张卡片，可以导航到上一张
      navigateTo(currentIndex.value - 1);
      
      // 等待视图更新后，尝试聚焦到合适的输入框
      setTimeout(() => {
        const newQuestionInput = document.querySelector('.current .question-card textarea');
        if (newQuestionInput) {
          newQuestionInput.focus();
        }
      }, 50);
    }
    // 如果已经是第一张卡片，不做任何操作，防止循环
  }
}

// 处理触摸事件
let touchStartY = 0;
let touchEndY = 0;

function handleTouchStart(event) {
  touchStartY = event.touches[0].clientY;
}

function handleTouchMove(event) {
  event.preventDefault();
}

async function handleTouchEnd(event) {
  if (isAnimating.value) return;
  
  touchEndY = event.changedTouches[0].clientY;
  const diffY = touchStartY - touchEndY;
  
  // 检测是否为有效的滑动（大于30像素）
  if (Math.abs(diffY) > 30) {
    // 只在有未保存的内容时保存
    if (hasUnsavedChanges.value) {
      await saveChanges();
    }
    
    if (diffY > 0) {
      // 向上滑动，显示下一个
      // 如果是最后一个卡片且有内容，创建新卡片
      if (currentIndex.value === localQaPairs.value.length - 1) {
        const current = currentQA.value;
        if (current.question.trim() || current.answer.trim()) {
          await addNewQA();
        }
      } else if (currentIndex.value < localQaPairs.value.length - 1) {
        // 只在不是最后一个卡片时导航到下一个
        navigateTo(currentIndex.value + 1);
        
        // 等待视图更新后，尝试聚焦到合适的输入框
        setTimeout(() => {
          const newQuestionInput = document.querySelector('.current .question-card textarea');
          if (newQuestionInput) {
            newQuestionInput.focus();
          }
        }, 50);
      }
    } else if (diffY < 0) {
      // 向下滑动，显示上一个，只在不是第一个卡片时
      if (currentIndex.value > 0) {
        navigateTo(currentIndex.value - 1);
        
        // 等待视图更新后，尝试聚焦到合适的输入框
        setTimeout(() => {
          const newQuestionInput = document.querySelector('.current .question-card textarea');
          if (newQuestionInput) {
            newQuestionInput.focus();
          }
        }, 50);
      }
    }
  }
}

// 定义beforeunload处理函数
const handleBeforeUnload = () => {
  if (hasUnsavedChanges.value) {
    saveChanges();
  }
};

// 导出方法供外部组件调用
// 直接跳转到指定索引的问答卡片
function navigateToIndex(index, smooth = true) {
  // 确保索引有效
  if (index >= 0 && index < localQaPairs.value.length) {
    // 如果有未保存的更改，先保存
    if (hasUnsavedChanges.value) {
      saveChanges();
    }
    
    // 设置新索引
    currentIndex.value = index;
    saveSettings();
    
    // 高亮显示当前卡片，使用较短的延迟
    setTimeout(() => {
      const currentCard = document.querySelector('.qa-card.current');
      if (currentCard) {
        currentCard.classList.add('highlight-card');
        currentCard.scrollIntoView({ 
          behavior: smooth ? 'smooth' : 'auto', 
          block: 'center' 
        });
        
        // 高亮效果持续2秒
        setTimeout(() => {
          currentCard.classList.remove('highlight-card');
        }, 2000);
      }
    }, 50); // 将延迟从100ms减少到50ms
    
    return true;
  }
  return false;
}

// 暴露方法供父组件调用
defineExpose({
  navigateToIndex
});

// 挂载事件监听器
onMounted(() => {
  // 加载存储的设置
  loadSettings();
  
  // 添加页面卸载前保存
  window.addEventListener('beforeunload', handleBeforeUnload);
  
  // 添加自定义事件监听，允许外部跳转到特定索引
  window.addEventListener('qalite-navigate', (event) => {
    if (event.detail && typeof event.detail.index === 'number') {
      console.log("QAEditor收到跳转事件:", event.detail.index);
      const smooth = event.detail.smooth !== undefined ? event.detail.smooth : true;
      navigateToIndex(event.detail.index, smooth);
    }
  });
  
  if (editorContainer.value) {
    // 使用函数包装器以确保在正确的上下文中处理事件
    const wheelHandler = (e) => {
      e.preventDefault(); // 先阻止默认行为
      if (!isAnimating.value) {
        handleWheel(e);
      }
    };
    
    const touchStartHandler = (e) => {
      handleTouchStart(e);
    };
    
    const touchMoveHandler = (e) => {
      e.preventDefault(); // 先阻止默认行为
    };
    
    const touchEndHandler = (e) => {
      if (!isAnimating.value) {
        handleTouchEnd(e);
      }
    };
    
    editorContainer.value.addEventListener('wheel', wheelHandler, { passive: false });
    editorContainer.value.addEventListener('touchstart', touchStartHandler, { passive: false });
    editorContainer.value.addEventListener('touchmove', touchMoveHandler, { passive: false });
    editorContainer.value.addEventListener('touchend', touchEndHandler, { passive: false });
  }
});

// 卸载事件监听器
onUnmounted(() => {
  // 移除页面卸载前保存
  window.removeEventListener('beforeunload', handleBeforeUnload);
  
  // 移除自定义事件监听
  window.removeEventListener('qalite-navigate', navigateToIndex);
  
  if (editorContainer.value) {
    // 由于我们使用了函数包装器，这里的移除可能不会工作，但Vue会在组件卸载时自动清理DOM
    editorContainer.value.removeEventListener('wheel', handleWheel);
    editorContainer.value.removeEventListener('touchstart', handleTouchStart);
    editorContainer.value.removeEventListener('touchmove', handleTouchMove);
    editorContainer.value.removeEventListener('touchend', handleTouchEnd);
  }
  
  // 确保清除定时器
  if (autoSaveTimer) {
    clearTimeout(autoSaveTimer);
  }
});

// 跳转到最后一张卡片
function jumpToLastCard() {
  if (props.qaPairs.length) {
    currentIndex.value = props.qaPairs.length - 1;
    saveChanges();
  }
}

// 找到不完整的QA对
function findIncompleteQA() {
  const incompleteIndex = localQaPairs.value.findIndex(qa => 
    !qa.question.trim() || !qa.answer.trim()
  );
  
  if (incompleteIndex >= 0) {
    navigateTo(incompleteIndex);
    return true;
  }
  
  return false;
}

// 切换复习模式
function toggleRevisionMode() {
  isRevisionMode.value = !isRevisionMode.value;
  if (isRevisionMode.value) {
    prepareRevisionMode();
  } else {
    isAnswerVisible.value = false;
    isRandomMode.value = false;
  }
}

// 准备复习模式
function prepareRevisionMode() {
  saveChanges();
  
  // 检查所有QA对，过滤出问题和答案都存在的对
  const validQaPairs = props.qaPairs.filter(qa => 
    qa.question.trim() && qa.answer.trim()
  );
  
  // 如果没有有效的QA对，不允许进入复习模式
  if (validQaPairs.length === 0) {
    alert('复习模式需要至少一个完整的问答对（问题和答案都不能为空）');
    isRevisionMode.value = false;
    return;
  }
  
  userAnswers.value = Array(validQaPairs.length).fill('');
  
  // 生成卡片的顺序，只包含有效的问答对
  revisionOrder.value = Array.from({ length: validQaPairs.length }, (_, i) => {
    // 查找原始索引
    return props.qaPairs.findIndex(qa => 
      qa === validQaPairs[i]
    );
  });
  
  if (isRandomMode.value) {
    shuffleRevisionOrder();
  }
  
  revisionIndex.value = 0;
  isAnswerVisible.value = false;
}

// 切换随机模式
function toggleRandomMode() {
  isRandomMode.value = !isRandomMode.value;
  prepareRevisionMode();
}

// 随机化复习顺序
function shuffleRevisionOrder() {
  for (let i = revisionOrder.value.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [revisionOrder.value[i], revisionOrder.value[j]] = [revisionOrder.value[j], revisionOrder.value[i]];
  }
}

// 切换答案可见性
function toggleAnswer() {
  isAnswerVisible.value = !isAnswerVisible.value;
}

// 下一张复习卡片
function nextRevisionCard() {
  if (revisionIndex.value < revisionOrder.value.length - 1) {
    revisionIndex.value++;
    isAnswerVisible.value = false;
  }
}

// 上一张复习卡片
function prevRevisionCard() {
  if (revisionIndex.value > 0) {
    revisionIndex.value--;
    isAnswerVisible.value = false;
  }
}

// 保存用户回答
function saveUserAnswer(event) {
  if (revisionIndex.value < userAnswers.value.length) {
    userAnswers.value[revisionIndex.value] = event.target.value;
  }
}

// 当前复习卡片
const currentRevisionQA = computed(() => {
  if (revisionOrder.value.length && revisionIndex.value < revisionOrder.value.length) {
    const qaIndex = revisionOrder.value[revisionIndex.value];
    if (qaIndex < props.qaPairs.length) {
      return {
        question: props.qaPairs[qaIndex].question,
        answer: props.qaPairs[qaIndex].answer,
        userAnswer: userAnswers.value[revisionIndex.value]
      };
    }
  }
  return { question: '', answer: '', userAnswer: '' };
});
</script>

<template>
  <div class="qa-editor" ref="editorContainer">
    <div class="editor-header">
      <div class="editor-title">Q&A 编辑器</div>
      <div class="editor-actions">
        <button class="view-toggle" @click="toggleViewMode">
          {{ isCombinedView ? '分开视图' : '合并视图' }}
          <span class="toggle-icon">{{ isCombinedView ? '🌸' : '🌷' }}</span>
        </button>
        <button class="view-toggle" @click="toggleRevisionMode">
          {{ isRevisionMode ? '编辑模式' : '复习模式' }}
          <span class="toggle-icon">{{ isRevisionMode ? '✏️' : '📚' }}</span>
        </button>
        <button v-if="!isRevisionMode" class="view-toggle" @click="findIncompleteQA">
          查找未完成 <span class="toggle-icon">🔍</span>
        </button>
      </div>
    </div>

    <!-- 复习模式 -->
    <div v-if="isRevisionMode" class="revision-mode">
      <div class="revision-controls">
        <button class="revision-button" @click="toggleRandomMode">
          {{ isRandomMode ? '顺序模式' : '随机模式' }}
          <span class="button-icon">{{ isRandomMode ? '🔢' : '🎲' }}</span>
        </button>
        <div class="revision-progress">
          {{ revisionIndex + 1 }} / {{ revisionOrder.length }}
        </div>
      </div>
      
      <!-- 复习卡片 -->
      <div class="revision-card">
        <div class="revision-question">
          <h3>问题</h3>
          <div class="revision-content">{{ currentRevisionQA.question }}</div>
        </div>
        
        <div class="revision-answer" :class="{ 'hidden': !isAnswerVisible }">
          <h3>标准答案</h3>
          <div class="revision-content" @click="toggleAnswer">
            {{ isAnswerVisible ? currentRevisionQA.answer : '点击查看答案' }}
          </div>
        </div>
        
        <div class="revision-user-answer">
          <h3>你的回答</h3>
          <textarea 
            v-model="currentRevisionQA.userAnswer" 
            placeholder="在这里输入你的答案..."
            @input="handleInput"
          ></textarea>
        </div>
      </div>
      
      <!-- 复习导航 -->
      <div class="revision-navigation">
        <button 
          class="nav-button prev-button" 
          @click="prevRevisionCard" 
          :disabled="revisionIndex <= 0"
        >
          <span class="button-text">上一个</span>
          <span class="button-emoji">⬅️</span>
        </button>
        <button class="nav-button toggle-answer" @click="toggleAnswer">
          <span class="button-text">{{ isAnswerVisible ? '隐藏答案' : '显示答案' }}</span>
          <span class="button-emoji">{{ isAnswerVisible ? '👁️' : '👓' }}</span>
        </button>
        <button 
          class="nav-button next-button" 
          @click="nextRevisionCard" 
          :disabled="revisionIndex >= revisionOrder.length - 1"
        >
          <span class="button-text">下一个</span>
          <span class="button-emoji">➡️</span>
        </button>
      </div>
    </div>

    <!-- 编辑模式 -->
    <div v-else class="cards-container" :class="{ 'combined-view': isCombinedView }">
      <div class="cards-row" v-if="!isCombinedView">
        <!-- 问题与回答卡片并排显示 -->
        <div class="card-pair" v-for="(qa, index) in localQaPairs" :key="`pair-${index}`"
             :class="{ 'current': index === currentIndex, 'next': index === currentIndex + 1, 'prev': index === currentIndex - 1 }"
             v-show="index >= currentIndex - 1 && index <= currentIndex + 1"
             @click="selectCard(index)">
          
          <!-- 问题卡片 -->
          <div class="card question-card">
            <div class="card-header">
              <span class="card-label">问题 <span class="card-emoji">❓</span></span>
              <span v-if="hasUnsavedChanges" class="unsaved-indicator">未保存</span>
            </div>
            <div class="card-content">
              <textarea v-model="qa.question" placeholder="输入你的问题..." 
                @input="handleInput" 
                :disabled="index !== currentIndex"></textarea>
            </div>
            <div class="card-decoration top-left"></div>
            <div class="card-decoration top-right"></div>
            <div class="card-decoration bottom-left"></div>
            <div class="card-decoration bottom-right"></div>
          </div>
          
          <!-- 回答卡片 -->
          <div class="card answer-card">
            <div class="card-header">
              <span class="card-label">回答 <span class="card-emoji">💡</span></span>
            </div>
            <div class="card-content">
              <textarea v-model="qa.answer" placeholder="输入你的回答..." 
                @input="handleInput" 
                :disabled="index !== currentIndex"></textarea>
            </div>
            <div class="card-decoration top-left"></div>
            <div class="card-decoration top-right"></div>
            <div class="card-decoration bottom-left"></div>
            <div class="card-decoration bottom-right"></div>
          </div>
        </div>
      </div>

      <!-- 合并视图模式 -->
      <div v-if="isCombinedView" class="combined-card-stack">
        <div class="card-scroll-container">
          <transition-group name="card" tag="div" class="card-scroll">
            <div v-for="(qa, index) in localQaPairs" :key="`qa-${index}`" 
                class="card combined-card" 
                :class="{ 'current': index === currentIndex, 'next': index === currentIndex + 1, 'prev': index === currentIndex - 1 }"
                v-show="index >= currentIndex - 1 && index <= currentIndex + 1"
                @click="selectCard(index)">
              <div class="card-content">
                <div class="qa-section question-section">
                  <div class="section-header">问题 <span class="card-emoji">❓</span></div>
                  <textarea v-model="qa.question" placeholder="输入你的问题..." 
                    @input="handleInput" 
                    :disabled="index !== currentIndex"></textarea>
                </div>
                <div class="qa-section answer-section">
                  <div class="section-header">回答 <span class="card-emoji">💡</span></div>
                  <textarea v-model="qa.answer" placeholder="输入你的回答..." 
                    @input="handleInput" 
                    :disabled="index !== currentIndex"></textarea>
                </div>
              </div>
              <div class="card-decoration top-left"></div>
              <div class="card-decoration top-right"></div>
              <div class="card-decoration bottom-left"></div>
              <div class="card-decoration bottom-right"></div>
            </div>
          </transition-group>
        </div>
      </div>
    </div>

    <div class="navigation-controls" v-if="!isRevisionMode">
      <button class="nav-button prev-button" @click="navigateRelative('prev')" :disabled="currentIndex <= 0">
        <span class="button-text">上一个</span>
        <span class="button-emoji">🌸</span>
      </button>
      <button class="nav-button add-button" @click="addNewQA">
        <span class="button-text">新建</span>
        <span class="button-emoji">✨</span>
      </button>
      <button class="nav-button save-button" @click="saveChanges" :disabled="!hasUnsavedChanges" 
        :class="{'highlight-save': hasUnsavedChanges}">
        <span class="button-text">保存</span>
        <span class="button-emoji">{{ hasUnsavedChanges ? '📝' : '💾' }}</span>
      </button>
      <button class="nav-button delete-button" @click="deleteCurrentQA" :disabled="localQaPairs.length <= 1">
        <span class="button-text">删除</span>
        <span class="button-emoji">🗑️</span>
      </button>
      <button class="nav-button next-button" @click="navigateRelative('next')" :disabled="currentIndex >= localQaPairs.length - 1">
        <span class="button-text">下一个</span>
        <span class="button-emoji">🌸</span>
      </button>
      <button class="nav-button last-button" @click="jumpToLastCard" :disabled="currentIndex >= localQaPairs.length - 1">
        <span class="button-text">底部</span>
        <span class="button-emoji">⏬</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.qa-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
  overflow: hidden;
  position: relative;
  user-select: none;
  z-index: 1; /* 确保z-index层级正确 */
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding: 0.5rem 0;
}

.editor-title {
  font-size: 1.5rem;
  font-weight: bold;
  color: #6d28d9;
}

.view-toggle {
  background: #f3e8ff;
  border: none;
  border-radius: 20px;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6d28d9;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.view-toggle:hover {
  background: #e9d5ff;
  transform: translateY(-2px);
}

.toggle-icon {
  font-size: 1.1rem;
}

.cards-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  width: 100%;
  display: flex;
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
}

.cards-row {
  width: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center; /* 确保卡片在容器中垂直居中 */
  height: 100%;
  position: relative; /* 确保定位正确 */
}

/* 卡片对样式 - 用于并排显示 */
.card-pair {
  display: flex;
  gap: 1.5rem;
  width: 100%;
  position: absolute;
  transition: all 0.4s ease;
  opacity: 0;
  transform: translateY(20px);
  left: 0; /* 确保水平位置正确 */
}

.card-pair.current {
  position: relative;
  opacity: 1;
  transform: translateY(0);
  z-index: 3;
  margin: 0 auto; /* 水平居中 */
  max-width: 100%;
}

.card-pair.prev {
  opacity: 0.5;
  transform: translateY(-100%);
  z-index: 2;
}

.card-pair.next {
  opacity: 0.5;
  transform: translateY(100%);
  z-index: 1;
}

/* 基础卡片样式 */
.card {
  background: white;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
  padding: 1rem;
  position: relative;
  overflow: hidden;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 250px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
}

.question-card {
  background: #f5f3ff;
  border: 2px solid #ddd6fe;
}

.answer-card {
  background: #ecfdf5;
  border: 2px solid #a7f3d0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.8rem;
}

.card-label {
  font-weight: bold;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #333;
}

.card-emoji {
  font-size: 1.2rem;
}

.card-content {
  flex: 1;
  position: relative;
}

/* 卡片装饰元素 */
.card-decoration {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  position: absolute;
}

.top-left {
  top: 10px;
  left: 10px;
  background: rgba(209, 213, 219, 0.3);
}

.top-right {
  top: 10px;
  right: 10px;
  background: rgba(209, 213, 219, 0.3);
}

.bottom-left {
  bottom: 10px;
  left: 10px;
  background: rgba(209, 213, 219, 0.3);
}

.bottom-right {
  bottom: 10px;
  right: 10px;
  background: rgba(209, 213, 219, 0.3);
}

.question-card .top-left { background: rgba(167, 139, 250, 0.3); }
.question-card .top-right { background: rgba(167, 139, 250, 0.2); }
.question-card .bottom-left { background: rgba(167, 139, 250, 0.2); }
.question-card .bottom-right { background: rgba(167, 139, 250, 0.3); }

.answer-card .top-left { background: rgba(52, 211, 153, 0.3); }
.answer-card .top-right { background: rgba(52, 211, 153, 0.2); }
.answer-card .bottom-left { background: rgba(52, 211, 153, 0.2); }
.answer-card .bottom-right { background: rgba(52, 211, 153, 0.3); }

/* 文本区域样式 */
textarea {
  width: 100%;
  height: 100%;
  min-height: 150px;
  border: none;
  background: transparent;
  resize: none;
  outline: none;
  font-size: 1rem;
  line-height: 1.5;
  color: #333;
  padding: 0.5rem;
  border-radius: 8px;
}

.question-card textarea {
  background: rgba(237, 233, 254, 0.5);
}

.answer-card textarea {
  background: rgba(209, 250, 229, 0.5);
}

textarea:focus {
  box-shadow: inset 0 0 0 2px rgba(109, 40, 217, 0.2);
}

textarea:disabled {
  cursor: default;
  opacity: 0.8;
}

/* 导航控制 */
.navigation-controls {
  display: flex;
  justify-content: center;
  gap: 1rem;
  padding: 1rem 0;
}

.nav-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 20px;
  background: #f3e8ff;
  color: #6d28d9;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.nav-button:hover:not(:disabled) {
  background: #e9d5ff;
  transform: translateY(-2px);
}

.nav-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button-emoji {
  font-size: 1.1rem;
}

.prev-button, .next-button {
  background: #ede9fe;
  color: #6d28d9;
}

.add-button {
  background: #d1fae5;
  color: #047857;
}

.delete-button {
  background: #fee2e2;
  color: #b91c1c;
}

.nav-button.save-button {
  background: #e0f2fe;
  color: #0369a1;
}

.nav-button.save-button.highlight-save {
  background: #93c5fd;
  animation: pulse 1.5s infinite;
  font-weight: bold;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(147, 197, 253, 0.7);
  }
  70% {
    box-shadow: 0 0 0 5px rgba(147, 197, 253, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(147, 197, 253, 0);
  }
}

.save-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 合并视图样式 */
.combined-view .cards-row {
  display: none !important; /* 强制隐藏分开视图 */
  pointer-events: none !important; /* 禁用分开视图的鼠标事件 */
}

.combined-card-stack {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
}

.card-scroll-container {
  position: relative;
  height: 100%;
  overflow: hidden;
  width: 100%; /* 确保宽度正确 */
}

.card-scroll {
  height: 100%;
  position: relative;
  width: 100%; /* 确保宽度正确 */
}

.combined-card {
  position: absolute;
  width: 100%;
  height: auto; /* 改为自适应高度 */
  max-height: 100%;
  transition: all 0.4s ease;
  opacity: 0;
  transform: translateY(20px);
  margin: 0 auto; /* 水平居中 */
  left: 0; /* 确保水平位置正确 */
  right: 0; /* 确保水平位置正确 */
}

.combined-card.current {
  opacity: 1;
  transform: translateY(0);
  z-index: 3;
}

.combined-card.prev {
  opacity: 0.5;
  transform: translateY(-70%); /* 调整堆叠效果 */
  z-index: 2;
}

.combined-card.next {
  opacity: 0.5;
  transform: translateY(70%); /* 调整堆叠效果 */
  z-index: 1;
}

.qa-section {
  padding: 0.8rem;
  margin-bottom: 1rem;
  border-radius: 10px;
}

.question-section {
  background: rgba(237, 233, 254, 0.5);
  border: 1px solid #ddd6fe;
}

.answer-section {
  background: rgba(209, 250, 229, 0.5);
  border: 1px solid #a7f3d0;
}

.section-header {
  font-weight: bold;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* 卡片切换动画 */
.card-enter-active,
.card-leave-active {
  transition: all 0.3s ease; /* 从0.4s改为0.3s */
}

.card-enter-from {
  opacity: 0;
  transform: translateY(30px); /* 从50px改为30px，减少移动距离 */
}

.card-leave-to {
  opacity: 0;
  transform: translateY(-30px); /* 从50px改为30px，减少移动距离 */
}

/* 响应式设计 */
@media (max-width: 768px) {
  .card-pair {
    flex-direction: column;
    gap: 1rem;
  }
  
  .cards-container {
    padding: 0 0.5rem;
  }
  
  .nav-button {
    padding: 0.5rem 0.8rem;
    font-size: 0.8rem;
  }
}

.combined-view {
  pointer-events: auto !important; /* 确保事件传递正确 */
  z-index: 10 !important; /* 确保合并视图在最上层 */
}

/* 黑暗模式下卡片样式调整 */
:global(.dark-mode) .card {
  background: #2c2c2e;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
}

:global(.dark-mode) .card:hover {
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}

:global(.dark-mode) .card-label {
  color: #fff;
}

:global(.dark-mode) .question-card {
  background: #34275f;
  border: 2px solid #5d50a6;
}

:global(.dark-mode) .answer-card {
  background: #1e4437;
  border: 2px solid #2a8e6a;
}

:global(.dark-mode) textarea {
  color: #fff;
}

:global(.dark-mode) .question-card textarea {
  background: rgba(93, 80, 166, 0.2);
}

:global(.dark-mode) .answer-card textarea {
  background: rgba(42, 142, 106, 0.2);
}

:global(.dark-mode) textarea:focus {
  box-shadow: inset 0 0 0 2px rgba(165, 122, 245, 0.4);
}

/* 复习模式样式 */
.revision-mode {
  display: flex;
  flex-direction: column;
  height: 100%;
  flex: 1;
  padding: 0 1rem;
}

.revision-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding: 0.5rem 0;
}

.revision-button {
  background: #f3e8ff;
  border: none;
  border-radius: 20px;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #6d28d9;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.revision-button:hover {
  background: #e9d5ff;
  transform: translateY(-2px);
}

.revision-progress {
  font-size: 0.9rem;
  font-weight: 600;
  color: #6d28d9;
  padding: 0.3rem 0.8rem;
  background: #f3e8ff;
  border-radius: 20px;
}

.revision-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background: white;
  border-radius: 15px;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
  padding: 1.5rem;
  margin-bottom: 1rem;
  position: relative;
  overflow: hidden;
}

.revision-question, .revision-answer, .revision-user-answer {
  border-radius: 10px;
  padding: 1rem;
  position: relative;
}

.revision-question {
  background: #e48ccb;
  border: 2px solid #ddd6fe;
}

.revision-answer {
  background: #21915c;
  border: 2px solid #338f64;
  transition: all 0.3s ease;
  cursor: pointer;
}

.revision-answer.hidden {
  background: #5379c3;
  border: 2px dashed #d1d5db;
}

.revision-user-answer {
  background: #ea7a76;
  border: 2px solid #bfdbfe;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.revision-content {
  margin-top: 0.5rem;
  white-space: pre-wrap;
  min-height: 60px;
}

.revision-user-answer textarea {
  flex: 1;
  min-height: 100px;
  padding: 0.8rem;
  border: none;
  border-radius: 8px;
  background: rgba(191, 219, 254, 0.2);
  resize: none;
  font-size: 1rem;
  line-height: 1.5;
}

.revision-user-answer textarea:focus {
  outline: none;
  box-shadow: inset 0 0 0 2px rgba(59, 130, 246, 0.3);
}

.revision-navigation {
  display: flex;
  justify-content: center;
  gap: 1rem;
  padding: 1rem 0;
}

.toggle-answer {
  background: #e0f2fe;
  color: #0369a1;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding: 0.5rem 0;
}

.editor-actions {
  display: flex;
  gap: 0.8rem;
}

.last-button {
  background: #f3e8ff;
  color: #6d28d9;
}

:global(.dark-mode) .revision-card {
  background: #1c1c1e;
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.4);
}

:global(.dark-mode) .revision-question {
  background: #2a1f48;
  border: 2px solid #7e6db9;
}

:global(.dark-mode) .revision-answer {
  background: #193a2d;
  border: 2px solid #41c990;
}

:global(.dark-mode) .revision-answer.hidden {
  background: #2c2c30;
  border: 2px dashed #8a8a93;
}

:global(.dark-mode) .revision-user-answer {
  background: #12294d;
  border: 2px solid #5c9df5;
}

:global(.dark-mode) .revision-content {
  color: #ffffff;
  font-weight: 500;
}

:global(.dark-mode) h3 {
  color: #ffffff;
  font-weight: 600;
}

:global(.dark-mode) .revision-progress {
  color: #ffffff;
  background: #42367f;
  font-weight: 600;
}

:global(.dark-mode) .revision-button {
  background: #42367f;
  color: #ffffff;
  font-weight: 500;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
}

:global(.dark-mode) .revision-button:hover {
  background: #5a4ba7;
  transform: translateY(-2px);
  box-shadow: 0 5px 12px rgba(0, 0, 0, 0.5);
}

:global(.dark-mode) .revision-user-answer textarea {
  background: rgba(92, 157, 245, 0.15);
  color: #ffffff;
  font-weight: 500;
}

:global(.dark-mode) .revision-user-answer textarea::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

:global(.dark-mode) .nav-button {
  background: #42367f;
  color: #ffffff;
  font-weight: 500;
}

:global(.dark-mode) .nav-button:hover:not(:disabled) {
  background: #5a4ba7;
}

:global(.dark-mode) .toggle-answer {
  background: #0f395c;
  color: #ffffff;
  font-weight: 500;
}

:global(.dark-mode) .toggle-answer:hover:not(:disabled) {
  background: #1e5c90;
}

.unsaved-indicator {
  font-size: 0.8rem;
  color: #ef4444;
  font-weight: 600;
  background-color: rgba(239, 68, 68, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  animation: fadeInOut 2s infinite;
}

@keyframes fadeInOut {
  0%, 100% {
    opacity: 0.7;
  }
  50% {
    opacity: 1;
  }
}
</style> 
