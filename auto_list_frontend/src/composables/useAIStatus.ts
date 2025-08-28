// src/composables/useAIStatus.ts
import { reactive, readonly } from 'vue';

// 状态类型定义
export type AIStatus = 'idle' | 'thinking' | 'processing' | 'completed' | 'error';
export type StepStatus = 'pending' | 'processing' | 'completed' | 'error';

// 处理步骤接口
export interface ProcessStep {
  title: string;
  description: string;
  status: StepStatus;
  statusText: string;
  timestamp: string;
}

export function useAIStatus() {
  // AI状态
  const state = reactive({
    status: 'idle' as AIStatus,
    steps: [
      {
        title: "邮件接收",
        description: "收取并解析邮件内容",
        status: "pending" as StepStatus,
        statusText: "未开始",
        timestamp: "--:--"
      },
      {
        title: "意图识别",
        description: "分析邮件核心诉求",
        status: "pending" as StepStatus,
        statusText: "未开始",
        timestamp: "--:--"
      },
      {
        title: "方案生成",
        description: "创建处理方案",
        status: "pending" as StepStatus,
        statusText: "未开始",
        timestamp: "--:--"
      },
      {
        title: "结果输出",
        description: "提交最终处理结果",
        status: "pending" as StepStatus,
        statusText: "未开始",
        timestamp: "--:--"
      }
    ],
    notificationVisible: false,
    notificationContent: '',
    drawerVisible: false
  });

  // 设置AI状态
  const setStatus = (status: AIStatus) => {
    state.status = status;
    
    // 状态变化时的特殊处理
    if (status === 'completed') {
      showCompleteNotification();
      
      // 更新所有步骤状态为完成
      state.steps.forEach(step => {
        if (step.status !== 'error') {
          step.status = 'completed';
          step.statusText = '已完成';
          step.timestamp = getCurrentTime();
        }
      });
    } else if (status === 'processing') {
      // 将下一个待处理步骤设置为处理中
      const pendingStep = state.steps.find(step => step.status === 'pending');
      if (pendingStep) {
        pendingStep.status = 'processing';
        pendingStep.statusText = '执行中';
        pendingStep.timestamp = getCurrentTime();
      }
    } else if (status === 'error') {
      // 设置错误步骤
      const errorStep = state.steps.find(step => step.status === 'processing') || 
                       state.steps.find(step => step.status === 'pending');
      if (errorStep) {
        errorStep.status = 'error';
        errorStep.statusText = '需要处理';
        errorStep.timestamp = getCurrentTime();
      }
    }
  };

  // 显示完成通知
  const showCompleteNotification = (count = 1) => {
    state.notificationContent = `${count}封邮件处理完成`;
    state.notificationVisible = true;
    
    // 5秒后自动关闭通知
    setTimeout(() => {
      state.notificationVisible = false;
    }, 3000);
  };

  // 切换详情面板可见性
  const toggleDrawer = () => {
    state.drawerVisible = !state.drawerVisible;
  };

  // 重置AI状态
  const resetStatus = () => {
    state.status = 'idle';
    state.steps = state.steps.map(step => ({
      ...step,
      status: "pending",
      statusText: "未开始",
      timestamp: "--:--"
    }));
  };

  // 获取当前时间
  const getCurrentTime = () => {
    return new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  };

  return {
    state: readonly(state),
    setStatus,
    showCompleteNotification,
    toggleDrawer,
    resetStatus
  };
}