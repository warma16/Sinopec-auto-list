<template>
  <!-- 状态指示灯容器 -->
  <div :class="['ai-status-indicator', statusPosition]" @click="toggleDetailPane">
    <!-- 状态指示灯 -->
    <t-tag 
      :shape="statusShape" 
      :theme="statusTheme" 
      :class="animationClass" 
      size="large"
      :closable="false"
    >
      <t-icon :name="statusIcon" />
    </t-tag>
    <!-- 状态文本 -->
    <span class="status-text">{{ statusText }}</span>
  </div>

  <!-- 状态详情面板 -->
  <t-drawer 
    v-model:visible="detailVisible" 
    :size="drawerSize"
    :placement="drawerPlacement"
    header="AI辅助状态详情"
    :footer="false"
  >
    <div class="status-panel">
      <t-steps layout="vertical" :current="currentStepIndex">
        <t-step v-for="(step, index) in statusSteps" :key="index" :status="stepStatus(step.status)">
          <template #icon>
            <div class="status-icon" :style="{background: stepColor(step.status)}">
              <t-icon :name="stepIcon(step.status)" />
            </div>
          </template>
          <template #title>
            <strong>{{ step.title }}</strong>
          </template>
          <template #description>
            <div class="step-details">
              <p>{{ step.description }}</p>
              <p class="step-info">
                <t-tag size="small" :theme="timelineTagTheme(step.status)">
                  {{ step.statusText }}
                </t-tag>
                <span class="timestamp">{{ step.timestamp }}</span>
              </p>
            </div>
          </template>
        </t-step>
      </t-steps>
    </div>
  </t-drawer>

  <!-- 顶部通知 -->
  <t-notification 
    v-if="notificationVisible" 
    theme="success" 
    title="邮件处理完成"
    :content="notificationContent"
    :duration="3000"
    placement="top-right"
    @duration-end="notificationVisible = false"
  >
    <template #icon>
      <t-icon name="check-circle-filled" />
    </template>
    <template #closeBtn>
      <t-icon name="close" />
    </template>
  </t-notification>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { NotifyPlugin, Link } from 'tdesign-vue-next';

// 状态管理
const currentStatus = ref('idle'); // idle | awake | thinking | processing | completed | error

// 界面状态
const detailVisible = ref(false);
const notificationVisible = ref(false);
const notificationContent = ref('');

// 配置选项
const statusPosition = ref('top-right'); // top-right | bottom-center
const animationEnabled = ref(true);
const drawerSize = ref('350px');
const drawerPlacement = ref('right'); // right | bottom

// 处理步骤数据
const statusSteps = ref([
  {
    title: "邮件接收",
    description: "收取并解析邮件内容",
    status: "complete",
    statusText: "已完成",
    timestamp: "10:23:05"
  },
  {
    title: "意图识别",
    description: "分析邮件核心诉求",
    status: "processing",
    statusText: "执行中",
    timestamp: "10:23:21"
  },
  {
    title: "方案生成",
    description: "创建处理方案",
    status: "pending",
    statusText: "待处理",
    timestamp: "--:--:--"
  },
  {
    title: "结果输出",
    description: "提交最终处理结果",
    status: "pending",
    statusText: "未开始",
    timestamp: "--:--:--"
  }
]);

// 计算当前步骤索引
const currentStepIndex = computed(() => {
  return statusSteps.value.findIndex(step => step.status === 'processing') || 0;
});

// 计算状态显示文本
const statusText = computed(() => {
  const statusMap = {
    idle: "待机中",
    awake: "已唤醒", 
    thinking: "思考中",
    processing: "处理中",
    completed: "已完成",
    error: "需要关注"
  };
  return statusMap[currentStatus.value] || '未知状态';
});

// 根据状态确定Tag形状
const statusShape = computed(() => {
  if (currentStatus.value === 'idle' || currentStatus.value === 'awake') return 'round';
  if (currentStatus.value === 'processing') return 'round-rect';
  return 'circle';
});

// 根据状态确定Tag颜色
const statusTheme = computed(() => {
  const themeMap = {
    idle: 'default',
    awake: 'primary',
    thinking: 'primary',
    processing: 'success',
    completed: 'warning',
    error: 'danger'
  };
  return themeMap[currentStatus.value] || 'default';
});

// 根据状态确定图标
const statusIcon = computed(() => {
  const iconMap = {
    idle: 'power-off',
    awake: 'view',
    thinking: 'loading',
    processing: 'time',
    completed: 'check-circle',
    error: 'error-circle'
  };
  return iconMap[currentStatus.value] || 'help-circle';
});

// 根据状态确定动画效果
const animationClass = computed(() => {
  if (!animationEnabled.value) return '';
  
  if (currentStatus.value === 'thinking' ) return 'breathing';
  if(currentStatus.value === 'awake') return "breathing awake-pulse"
  if (currentStatus.value === 'completed') return 'pulse';
  return '';
});

// 步骤颜色方法
const stepColor = (status) => {
  const colorMap = {
    complete: 'var(--td-brand-color)',
    processing: 'var(--td-success-color)',
    pending: 'var(--td-gray-color-5)',
    error: 'var(--td-error-color)'
  };
  return colorMap[status] || '#A4A4A4';
};

// 步骤图标方法
const stepIcon = (status) => {
  const iconMap = {
    complete: 'check',
    processing: 'loading',
    pending: 'time',
    error: 'error-circle'
  };
  return iconMap[status] || 'help';
};

// 步骤状态图标
const stepStatus = (status) => {
  const statusMap = {
    complete: 'finish',
    processing: 'process',
    pending: 'wait',
    error: 'error'
  };
  return statusMap[status] || 'default';
};

// 时间线标签主题
const timelineTagTheme = (status) => {
  const themeMap = {
    complete: 'primary',
    processing: 'success',
    pending: 'default',
    error: 'danger'
  };
  return themeMap[status] || 'default';
};

// 切换详情面板
const toggleDetailPane = () => {
  detailVisible.value = !detailVisible.value;
};

// 显示完成通知
const showCompleteNotification = (count = 1) => {
  NotifyPlugin.success({
    title:`${count}封邮件处理完成`
  })
  
  // 5秒后重置状态
  setTimeout(() => {
    notificationVisible.value = false;
    if (currentStatus.value === 'completed') {
      currentStatus.value = 'idle';
    }
  }, 3000);
};

// 模拟状态变化函数 - 可在外部调用
const setAIStatus = (status, options = {}) => {
  currentStatus.value = status;
  
  if (status === 'completed') {
    showCompleteNotification(options.emailCount || 1);
    
    // 更新所有步骤状态为完成
    statusSteps.value.forEach(step => {
      if (step.status !== 'error') {
        step.status = 'complete';
        step.statusText = '已完成';
        step.timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
      }
    });
  } else if (status === 'processing') {
    // 将下一个待处理步骤设置为处理中
    const pendingStep = statusSteps.value.find(step => step.status === 'pending');
    if (pendingStep) {
      pendingStep.status = 'processing';
      pendingStep.statusText = '执行中';
      pendingStep.timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
  } else if (status === 'error') {
    // 设置错误步骤
    const errorStep = statusSteps.value.find(step => step.status === 'processing') || 
                     statusSteps.value.find(step => step.status === 'pending');
    if (errorStep) {
      errorStep.status = 'error';
      errorStep.statusText = '需要处理';
      errorStep.timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
  }
};

// 重置AI状态
const resetAIStatus = () => {
  currentStatus.value = 'idle';
  statusSteps.value = statusSteps.value.map(step => ({
    ...step,
    status: step.title === "邮件接收" ? "complete" : "pending",
    statusText: step.title === "邮件接收" ? "已完成" : "未开始",
    timestamp: step.title === "邮件接收" ? new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : "--:--"
  }));
};

// 监听状态变化
watch(currentStatus, (newVal) => {
  if (newVal === 'error') {
    // 错误通知逻辑
  }
});

// 暴露方法给父组件
defineExpose({
  setAIStatus,
  resetAIStatus,
  showCompleteNotification
});
</script>

<style scoped>
/* 状态指示灯基础样式 */
.ai-status-indicator {
  z-index: 1000;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  user-select: none;
  backdrop-filter: blur(4px);
}

/* 位置控制 */
.ai-status-indicator.top-right {
  top: 20px;
  right: 20px;
}

.ai-status-indicator.bottom-center {
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
}

/* 状态文本样式 */
.status-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--td-text-color-primary);
}

/* 状态图标样式 */
.status-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
}

/* 动画效果 */
.breathing {
  animation: breathing 3s ease-in-out infinite;
}

.pulse {
  animation: pulse 2s infinite;
}

@keyframes breathing {
  0%, 100% { opacity: 0.8; transform: scale(0.95); }
  50% { opacity: 1; transform: scale(1.05); }
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(25, 103, 210, 0.5); }
  70% { box-shadow: 0 0 0 10px rgba(25, 103, 210, 0); }
  100% { box-shadow: 0 0 0 0 rgba(25, 103, 210, 0); }
}

/* 状态面板样式 */
.status-panel {
  padding: 16px;
}

.status-panel :deep(.t-steps) {
  padding: 0;
}

.status-panel :deep(.t-steps .t-step) {
  padding-bottom: 16px;
}

.step-details {
  padding-left: 8px;
}

.step-info {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.timestamp {
  font-size: 12px;
  color: var(--td-text-color-placeholder);
}
.awake-pulse {
  animation: awakePulse 2.5s infinite;
}

@keyframes awakePulse {
  0% { 
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(0, 123, 255, 0.7);
  }
  50% { 
    transform: scale(1.05);
    box-shadow: 0 0 0 10px rgba(0, 123, 255, 0);
  }
  100% { 
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(0, 123, 255, 0);
  }
}
</style>