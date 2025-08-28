<template>
    <div class="main-content">
      <!-- 左侧视图 -->
        <div class="particle-overlay" v-if="showParticleEffect">
          <canvas ref="particleCanvas" class="particle-canvas"></canvas>
        </div>
      <!-- 主要内容 -->
      <t-content class="content">
        <!-- 搜索和筛选区域 -->
        <div class="action-bar">
          <t-input class="search-input" placeholder="搜索分组或视图..." clearable>
            <template #prefix-icon>
              <t-icon name="search" />
            </template>
          </t-input>
          
          <!-- 增强的排序控件 -->
          <div class="sort-controls">
            <span class="sort-label">排序方式：</span>
            <t-button-group>
              <t-button variant="outline" :class="{active: sortBy === 'createTime'}" @click="sortBy = 'createTime'">
                <t-icon name="time" /> 创建时间
              </t-button>
              <t-button variant="outline" :class="{active: sortBy === 'priority'}" @click="sortBy = 'priority'">
                <t-icon name="ranking" /> 优先级
              </t-button>
              <t-button variant="outline" :class="{active: sortBy === 'dueDate'}" @click="sortBy = 'dueDate'">
                <t-icon name="calendar" /> 截止日期
              </t-button>
            </t-button-group>
          </div>
        </div>

        <!-- 动态分类看板 -->
        <div class="kanban-container" ref="kanbanContainer">
          <!-- 动态生成分类列 -->
          <div v-if="!categories.length" class="empty-state">
              <t-icon name="info-circle" />
              <span>暂无任务数据</span>
          </div>
          <div v-for="(category, index) in categories" :key="index" class="kanban-column">
            <div class="column-header">
              <div class="column-title">{{ category }}</div>
              <t-badge :count="categoryTasksCount(category)" :max-count="99" />
            </div>
            
            <!-- 该分类下的任务卡片 -->
            <transition-group 
            name="task-exit" 
            tag="div" 
            class="task-list-container"
            @before-leave="onTaskLeave">
              <div 
                v-for="task in categoryTasks(category)" 
                :key="task.id" 
                class="task-card"
                :class="taskCardClass(task)"
                @click="manualReply(task,category)"
                >
                <div class="task-header">
                  <div class="task-title">{{ task.name }}</div>
                  <div class="task-meta">
                    <t-tag :theme="taskTheme(task)" size="small">{{ task.riskLevel || '无风险' }}</t-tag>
                  </div>
                </div>
                
                <div class="task-details">
                  <div class="task-deadline" v-if="task.deadline">
                    <t-icon name="calendar" />
                    <span>截止：{{ task.deadline }}</span>
                  </div>
                  
                  <div class="task-info" v-if="task.reason">
                    <t-icon name="help-circle" />
                    <span>{{ task.reason }}</span>
                  </div>
                  
                  <div class="task-level">
                    <t-icon name="flag" />
                    <span>等级：{{ task.level }}</span>
                  </div>
                </div>
              </div>
            </transition-group>
          </div>
        </div>
      </t-content>
    </div>
</template>

<script setup >
import { ref, computed, onMounted, onErrorCaptured,nextTick,getCurrentInstance} from 'vue';
import { NotifyPlugin} from 'tdesign-vue-next';
import {ds_logo_size_144} from "@/utils/ds_logo_data.js"
const instance = getCurrentInstance();
const evbox = instance.appContext.config.globalProperties.$evbox;
const http_proto=instance.appContext.config.globalProperties.$http_proto
const endpoint=instance.appContext.config.globalProperties.$endpoint
console.log("脚本开始执行");
onErrorCaptured((err, instance, info) => {
  console.error('全局错误捕获:', err);
  // 这里可以添加错误报告逻辑
  return true; // 阻止错误继续传播
});
// API返回的数据示例（实际中应该通过API获取）

const apiResponse=ref({
  "data":[]
})
const tmp_apiResponse=ref({
  "data":[]
})

const shuffle=(arr)=>{
  const shuffled = [...arr];
    // 从后向前遍历数组
    for (let i = shuffled.length - 1; i > 0; i--) {
        // 生成[0, i]范围内的随机索引
        const j = Math.floor(Math.random() * (i + 1));
        // ES6解构赋值交换元素
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}
const fake_apiResponse = ref({
  "data": [
      {
    "id": "SAFE-001@risktest.com",
    "level": "1",
    "deadline": "30分钟响应",
    "riskLevel": "高",
    "reason": "苯类泄漏",
    "category": "安全环保",
    "theme": "danger",
    "name": "苯储罐T-301紧急泄漏"
  },
    {
      "id": "7c8a58859f4eecb35e5a7494d1d9df00",
      "level": "2",
      "deadline": "2025-07-19",
      "riskLevel": "中",
      "reason": "超期",
      "category": "文件报批",
      "theme": "danger",
      "name": "Silleno资料文件截止日期"
    },
    {
      "id": "4df4141b0efcc1460999aff3773c8d05",
      "level": "4",
      "deadline": "",
      "riskLevel": "小",
      "reason": "",
      "category": "生产运维",
      "theme": "default",
      "name": "温度修订单"
    },
    {
      "id": "120246f520064499502b070f7ea15f79",
      "level": "2",
      "deadline": "2025-07-10",
      "riskLevel": "中",
      "reason": "滞后项",
      "category": "工程进度",
      "theme": "warning",
      "name": "滞后工作对接会议"
    },
    {
      "id": "15e1ab8fadc52f96b4fa629111307d10",
      "level": "4",
      "deadline": "2025-09-01",
      "riskLevel": "小",
      "reason": "",
      "category": "工程进度",
      "theme": "default",
      "name": "职工体检通知"
    },
    {
      "id": "5d3c9441f55b4e8621e698ad1a21108c",
      "level": "4",
      "deadline": "",
      "riskLevel": "小",
      "reason": "",
      "category": "工程进度",
      "theme": "default",
      "name": "冷箱标准澄清"
    },
    {
      "id": "81fe91a1c06031d7c30b0f847a3fcb5c",
      "level": "2",
      "deadline": "",
      "riskLevel": "中",
      "reason": "严格管理措施",
      "category": "文件报批",
      "theme": "danger",
      "name": "全面从严管理通知"
    },
    {
      "id": "22dffecbaeedef051ac16455eb3c6a94",
      "level": "4",
      "deadline": "",
      "riskLevel": "小",
      "reason": "",
      "category": "文件报批",
      "theme": "default",
      "name": "三会一课通知"
    },
    {
      "id": "df3ecc05ae25e58c4c5c7bfee349c7e7",
      "level": "4",
      "deadline": "2025-07-10",
      "riskLevel": "小",
      "reason": "培训",
      "category": "文件报批",
      "theme": "default",
      "name": "职业资格考试指南"
    },
    {
      "id": "fd774e4131a7cb1e7a579cec82e7f1b0",
      "level": "4",
      "deadline": "",
      "riskLevel": "小",
      "reason": "征求意见",
      "category": "文件报批",
      "theme": "default",
      "name": "特种设备标准修订意见"
    },
    // 测试用例1：苯储罐泄漏（1级响应）
  
  // 测试用例2：百万级环评罚款（1级升级）
  {
    "id": "PENALTY-002@risktest.com",
    "level": "1",
    "deadline": "今日17:00",
    "riskLevel": "高",
    "reason": "环评超期罚款",
    "category": "文件报批",
    "theme": "default",
    "name": "环评逾期150万元罚单"
  },
  
  // 测试用例3：政府突击检查（1级升级）
  {
    "id": "GOV-003@risktest.com",
    "level": "1",
    "deadline": "明日9:00",
    "riskLevel": "高",
    "reason": "政府突击检查",
    "category": "安全环保",
    "theme": "default",
    "name": "省应急厅重大危险源检查"
  },
  
  // 测试用例4：动火证超期+泄漏（安全环保部分）
  {
    "id": "RISK-0720-001@risktest.com",
    "level": "1",
    "deadline": "1小时内处置",
    "riskLevel": "高",
    "reason": "甲苯泄漏",
    "category": "安全环保",
    "theme": "danger",
    "name": "V-202储罐泄漏"
  },
  
  // 测试用例4：动火证超期+泄漏（文件报批部分）
  {
    "id": "RISK-0720-001@risktest.com",
    "level": "1",
    "deadline": "今日17:00",
    "riskLevel": "高",
    "reason": "动火证超期",
    "category": "文件报批",
    "theme": "danger",
    "name": "罐区动火证超期"
  },
  // ================= 安全环保 (12条) =================
  {
    "id": "SAFE-002@risktest.com",
    "level": "1",
    "deadline": "1小时内",
    "riskLevel": "高",
    "reason": "静电引发闪爆风险",
    "category": "安全环保",
    "theme": "danger",
    "name": "甲苯卸车静电防护失效"
  },
  // 其余10条安全环保数据...

  // ================= 工程进度 (8条) =================
  {
    "id": "PROJ-101@risktest.com",
    "level": "2",
    "deadline": "本周五",
    "riskLevel": "中",
    "reason": "管廊施工滞后",
    "category": "工程进度",
    "theme": "warning",
    "name": "A区管廊焊接延期"
  },
  {
    "id": "PROJ-102@risktest.com",
    "level": "3",
    "deadline": "下月15日",
    "riskLevel": "中",
    "reason": "设备到货延迟",
    "category": "工程进度",
    "theme": "warning",
    "name": "反应釜交货延期"
  },
  // 其余6条工程进度数据...

  // ================= 文件报批 (8条) =================
  {
    "id": "DOC-201@risktest.com",
    "level": "1",
    "deadline": "今日17:00",
    "riskLevel": "高",
    "reason": "10万/日罚款",
    "category": "文件报批",
    "theme": "danger",
    "name": "安全生产许可证超期"
  },
  {
    "id": "DOC-202@risktest.com",
    "level": "2",
    "deadline": "3个工作日内",
    "riskLevel": "中",
    "reason": "环评批复过期",
    "category": "文件报批",
    "theme": "warning",
    "name": "二期项目环评续批"
  },
  // 其余6条文件报批数据...

  // ================= 生产运维 (12条) =================
  {
    "id": "OPS-301@risktest.com",
    "level": "2",
    "deadline": "4小时内",
    "riskLevel": "中",
    "reason": "轴承温度超标",
    "category": "生产运维",
    "theme": "warning",
    "name": "P-203A离心泵故障"
  },
  {
    "id": "OPS-302@risktest.com",
    "level": "3",
    "deadline": "48小时内",
    "riskLevel": "中",
    "reason": "振动值异常",
    "category": "生产运维",
    "theme": "warning",
    "name": "空压机振动超标"
  },
  {
    "id": "OPS-303@risktest.com",
    "level": "2",
    "deadline": "今日内",
    "riskLevel": "中",
    "reason": "转化率下降7%",
    "category": "生产运维",
    "theme": "warning",
    "name": "酯化反应效率降低"
  },
  {
    "id": "OPS-304@risktest.com",
    "level": "3",
    "deadline": "3天内",
    "riskLevel": "低",
    "reason": "压差波动",
    "category": "生产运维",
    "theme": "info",
    "name": "T-502精馏塔异常"
  },
  {
    "id": "OPS-305@risktest.com",
    "level": "1",
    "deadline": "1小时内",
    "riskLevel": "高",
    "reason": "全厂供汽中断",
    "category": "生产运维",
    "theme": "danger",
    "name": "蒸汽管网压力不足"
  },
  {
    "id": "OPS-306@risktest.com",
    "level": "3",
    "deadline": "本周内",
    "riskLevel": "低",
    "reason": "露点超标",
    "category": "生产运维",
    "theme": "info",
    "name": "仪表氮气质量异常"
  },
  {
    "id": "OPS-307@risktest.com",
    "level": "4",
    "deadline": "8月1日前",
    "riskLevel": "低",
    "reason": "年度计划",
    "category": "生产运维",
    "theme": "info",
    "name": "全厂停车检修准备"
  },
  {
    "id": "OPS-308@risktest.com",
    "level": "2",
    "deadline": "24小时内",
    "riskLevel": "中",
    "reason": "COD超标",
    "category": "生产运维",
    "theme": "warning",
    "name": "废水处理系统异常"
  },
  {
    "id": "OPS-309@risktest.com",
    "level": "3",
    "deadline": "72小时内",
    "riskLevel": "低",
    "reason": "催化剂效率下降",
    "category": "生产运维",
    "theme": "info",
    "name": "加氢反应器再生周期"
  },
  {
    "id": "OPS-310@risktest.com",
    "level": "2",
    "deadline": "今日下班前",
    "riskLevel": "中",
    "reason": "DCS参数漂移",
    "category": "生产运维",
    "theme": "warning",
    "name": "温度传感器校准"
  },
  {
    "id": "OPS-311@risktest.com",
    "level": "1",
    "deadline": "立即处理",
    "riskLevel": "高",
    "reason": "联锁系统误触发",
    "category": "生产运维",
    "theme": "danger",
    "name": "反应釜紧急停车"
  },
  {
    "id": "OPS-312@risktest.com",
    "level": "3",
    "deadline": "5个工作日内",
    "riskLevel": "低",
    "reason": "能效优化",
    "category": "生产运维",
    "theme": "info",
    "name": "冷冻机组维护计划"
  },

  // ================= 日常事务 (10条) =================
  {
    "id": "ADM-401@risktest.com",
    "level": "4",
    "deadline": "本周五",
    "riskLevel": "低",
    "reason": "季度申领",
    "category": "日常事务",
    "theme": "info",
    "name": "劳保用品需求申报"
  },
  {
    "id": "ADM-402@risktest.com",
    "level": "4",
    "deadline": "今日16:00",
    "riskLevel": "低",
    "reason": "防暑物资发放",
    "category": "日常事务",
    "theme": "info",
    "name": "盐汽水签收"
  },
  {
    "id": "ADM-403@risktest.com",
    "level": "3",
    "deadline": "明日14:00",
    "riskLevel": "低",
    "reason": "年度复训",
    "category": "日常事务",
    "theme": "info",
    "name": "HAZOP分析培训"
  },
  {
    "id": "ADM-404@risktest.com",
    "level": "4",
    "deadline": "下周一",
    "riskLevel": "低",
    "reason": "季度会议",
    "category": "日常事务",
    "theme": "info",
    "name": "安全生产委员会"
  },
  {
    "id": "ADM-405@risktest.com",
    "level": "4",
    "deadline": "本月25日",
    "riskLevel": "低",
    "reason": "设备台账更新",
    "category": "日常事务",
    "theme": "info",
    "name": "压力容器登记"
  },
  {
    "id": "ADM-406@risktest.com",
    "level": "4",
    "deadline": "8月10日前",
    "riskLevel": "低",
    "reason": "年度申报",
    "category": "日常事务",
    "theme": "info",
    "name": "防雷检测计划"
  },
  {
    "id": "ADM-407@risktest.com",
    "level": "3",
    "deadline": "3个工作日内",
    "riskLevel": "低",
    "reason": "审计准备",
    "category": "日常事务",
    "theme": "info",
    "name": "ISO体系文件整理"
  },
  {
    "id": "ADM-408@risktest.com",
    "level": "4",
    "deadline": "本月底",
    "riskLevel": "低",
    "reason": "月度报告",
    "category": "日常事务",
    "theme": "info",
    "name": "能源消耗分析"
  },
  {
    "id": "ADM-409@risktest.com",
    "level": "4",
    "deadline": "无时限",
    "riskLevel": "低",
    "reason": "知识库更新",
    "category": "日常事务",
    "theme": "info",
    "name": "SOP文件修订"
  },
  {
    "id": "ADM-410@risktest.com",
    "level": "3",
    "deadline": "下周一下班前",
    "riskLevel": "低",
    "reason": "预算编制",
    "category": "日常事务",
    "theme": "info",
    "name": "维修费用预估"
  },
  {
    "id": "OPS-313@risktest.com",
    "level": "1",
    "deadline": "立即处置",
    "riskLevel": "高",
    "reason": "联锁系统失效",
    "category": "生产运维",
    "theme": "danger",
    "name": "反应釜安全联锁旁路报警"
  },
  {
    "id": "OPS-314@risktest.com",
    "level": "2",
    "deadline": "2小时内",
    "riskLevel": "中",
    "reason": "pH值异常波动",
    "category": "生产运维",
    "theme": "warning",
    "name": "中和池控制系统故障"
  },
  {
    "id": "OPS-315@risktest.com",
    "level": "3",
    "deadline": "24小时内",
    "riskLevel": "低",
    "reason": "密封油渗漏",
    "category": "生产运维",
    "theme": "info",
    "name": "压缩机轴封泄漏处理"
  },
  {
    "id": "OPS-316@risktest.com",
    "level": "1",
    "deadline": "30分钟内",
    "riskLevel": "高",
    "reason": "氢气检测报警",
    "category": "生产运维",
    "theme": "danger",
    "name": "加氢装置区气体聚集"
  },
  {
    "id": "OPS-317@risktest.com",
    "level": "2",
    "deadline": "今日下班前",
    "riskLevel": "中",
    "reason": "收率下降5%",
    "category": "生产运维",
    "theme": "warning",
    "name": "结晶工序效率异常"
  },
  
  // 新增日常事务 (3条)
  {
    "id": "ADM-411@risktest.com",
    "level": "4",
    "deadline": "下季度首月5日前",
    "riskLevel": "低",
    "reason": "年度申报",
    "category": "日常事务",
    "theme": "info",
    "name": "危废转移计划备案"
  },
  {
    "id": "ADM-412@risktest.com",
    "level": "3",
    "deadline": "明日12:00前",
    "riskLevel": "低",
    "reason": "审计配合",
    "category": "日常事务",
    "theme": "info",
    "name": "特种作业证抽查准备"
  },
  {
    "id": "ADM-413@risktest.com",
    "level": "4",
    "deadline": "持续进行",
    "riskLevel": "低",
    "reason": "知识管理",
    "category": "日常事务",
    "theme": "info",
    "name": "事故案例库更新"
  },
  
  // 新增工程进度 (2条)
  {
    "id": "PROJ-103@risktest.com",
    "level": "1",
    "deadline": "今日18:00前",
    "riskLevel": "高",
    "reason": "混凝土浇筑窗口",
    "category": "工程进度",
    "theme": "danger",
    "name": "消防水池浇筑超时预警"
  },
  {
    "id": "PROJ-104@risktest.com",
    "level": "2",
    "deadline": "3个工作日内",
    "riskLevel": "中",
    "reason": "超期未验收",
    "category": "工程进度",
    "theme": "warning",
    "name": "管架防腐工程验收"
  },
  {
    "id": "SAFE-013@risktest.com",
    "level": "1",
    "deadline": "立即处理",
    "riskLevel": "高",
    "reason": "硫化氢泄漏",
    "category": "安全环保",
    "theme": "danger",
    "name": "脱硫塔检测口泄漏"
  },
  {
    "id": "SAFE-014@risktest.com",
    "level": "2",
    "deadline": "今日下班前",
    "riskLevel": "中",
    "reason": "防爆区域手机使用",
    "category": "安全环保",
    "theme": "warning",
    "name": "罐区违规行为通报"
  },
  // 新增6条安全环保数据...

  // 工程进度（新增7条）
  {
    "id": "PROJ-105@risktest.com",
    "level": "1",
    "deadline": "明日8:00前",
    "riskLevel": "高",
    "reason": "吊装作业许可超期",
    "category": "工程进度",
    "theme": "danger",
    "name": "反应器吊装作业"
  },
  {
    "id": "PROJ-106@risktest.com",
    "level": "3",
    "deadline": "下周三",
    "riskLevel": "低",
    "reason": "材料到货延迟",
    "category": "工程进度",
    "theme": "info",
    "name": "钢结构安装延期"
  },
  // 新增5条工程进度数据...

  // 文件报批（新增6条）
  {
    "id": "DOC-209@risktest.com",
    "level": "2",
    "deadline": "3个工作日内",
    "riskLevel": "中",
    "reason": "环保税申报",
    "category": "文件报批",
    "theme": "warning",
    "name": "二季度环保税缴纳"
  },
  {
    "id": "DOC-210@risktest.com",
    "level": "4",
    "deadline": "年度更新",
    "riskLevel": "低",
    "reason": "备案材料补充",
    "category": "文件报批",
    "theme": "info",
    "name": "重大危险源档案"
  },
  // 新增4条文件报批数据...

  // 生产运维（新增18条）
  {
    "id": "OPS-318@risktest.com",
    "level": "1",
    "deadline": "立即停机",
    "riskLevel": "高",
    "reason": "轴承温度骤升",
    "category": "生产运维",
    "theme": "danger",
    "name": "压缩机干气密封报警"
  },
  {
    "id": "OPS-319@risktest.com",
    "level": "2",
    "deadline": "4小时内",
    "riskLevel": "中",
    "reason": "冷却水流量不足",
    "category": "生产运维",
    "theme": "warning",
    "name": "换热器效率下降"
  },
  {
    "id": "OPS-320@risktest.com",
    "level": "3",
    "deadline": "48小时内",
    "riskLevel": "低",
    "reason": "润滑油含水超标",
    "category": "生产运维",
    "theme": "info",
    "name": "汽轮机油质检测"
  },
  // 新增15条生产运维数据...

  // 日常事务（新增10条）
  {
    "id": "ADM-414@risktest.com",
    "level": "4",
    "deadline": "每月5日前",
    "riskLevel": "低",
    "reason": "月度报表",
    "category": "日常事务",
    "theme": "info",
    "name": "能源消耗统计"
  },
  {
    "id": "ADM-415@risktest.com",
    "level": "3",
    "deadline": "本周五前",
    "riskLevel": "低",
    "reason": "培训需求收集",
    "category": "日常事务",
    "theme": "info",
    "name": "Q3技能提升计划"
  },
  // 新增8条日常事务数据...

  // ===================== 特别补充高风险场景 =====================
  {
    "id": "SAFE-021@risktest.com",
    "level": "1",
    "deadline": "30分钟内",
    "riskLevel": "高",
    "reason": "雷击导致停电",
    "category": "安全环保",
    "theme": "danger",
    "name": "UPS电源切换异常"
  },
  {
    "id": "OPS-336@risktest.com",
    "level": "1",
    "deadline": "立即撤离",
    "riskLevel": "高",
    "reason": "有毒气体扩散",
    "category": "生产运维",
    "theme": "danger",
    "name": "光气室密封失效"
  },
  // ================= 生产运维（12条）=================
  {
    "id": "OPS-401@risktest.com",
    "level": "1",
    "deadline": "立即处置",
    "riskLevel": "高",
    "reason": "联锁测试失败",
    "category": "生产运维",
    "theme": "danger",
    "name": "SIS系统安全联锁测试异常"
  },
  {
    "id": "OPS-402@risktest.com",
    "level": "2",
    "deadline": "2小时内",
    "riskLevel": "中",
    "reason": "含氧量超标",
    "category": "生产运维",
    "theme": "warning",
    "name": "氮气保护系统失效"
  },
  {
    "id": "OPS-403@risktest.com",
    "level": "3",
    "deadline": "本周五前",
    "riskLevel": "低",
    "reason": "备件库存不足",
    "category": "生产运维",
    "theme": "info",
    "name": "机泵轴承备件预警"
  },
  {
    "id": "OPS-404@risktest.com",
    "level": "1",
    "deadline": "30分钟内",
    "riskLevel": "高",
    "reason": "DCS通讯中断",
    "category": "生产运维",
    "theme": "danger",
    "name": "中央控制室信号丢失"
  },
  {
    "id": "OPS-405@risktest.com",
    "level": "2",
    "deadline": "今日下班前",
    "riskLevel": "中",
    "reason": "收率波动5%",
    "category": "生产运维",
    "theme": "warning",
    "name": "聚合反应转化率异常"
  },
  {
    "id": "OPS-406@risktest.com",
    "level": "3",
    "deadline": "48小时内",
    "riskLevel": "低",
    "reason": "润滑脂变质",
    "category": "生产运维",
    "theme": "info",
    "name": "减速机润滑状态预警"
  },
  {
    "id": "OPS-407@risktest.com",
    "level": "1",
    "deadline": "立即停机",
    "riskLevel": "高",
    "reason": "振动值爆表",
    "category": "生产运维",
    "theme": "danger",
    "name": "压缩机喘振保护触发"
  },
  {
    "id": "OPS-408@risktest.com",
    "level": "2",
    "deadline": "4小时内",
    "riskLevel": "中",
    "reason": "冷却水pH异常",
    "category": "生产运维",
    "theme": "warning",
    "name": "循环水系统腐蚀风险"
  },
  {
    "id": "OPS-409@risktest.com",
    "level": "3",
    "deadline": "3个工作日内",
    "riskLevel": "低",
    "reason": "校验周期到期",
    "category": "生产运维",
    "theme": "info",
    "name": "安全阀离线校验"
  },
  {
    "id": "OPS-410@risktest.com",
    "level": "1",
    "deadline": "15分钟内",
    "riskLevel": "高",
    "reason": "有毒气体报警",
    "category": "生产运维",
    "theme": "danger",
    "name": "光气检测仪触发"
  },
  {
    "id": "OPS-411@risktest.com",
    "level": "2",
    "deadline": "今日内",
    "riskLevel": "中",
    "reason": "催化剂活性下降",
    "category": "生产运维",
    "theme": "warning",
    "name": "加氢反应效率降低"
  },
  {
    "id": "OPS-412@risktest.com",
    "level": "4",
    "deadline": "下月5日前",
    "riskLevel": "低",
    "reason": "预防性维护",
    "category": "生产运维",
    "theme": "info",
    "name": "年度大修计划编制"
  },

  // ================= 安全环保（5条）=================
  {
    "id": "SAFE-022@risktest.com",
    "level": "1",
    "deadline": "立即撤离",
    "riskLevel": "高",
    "reason": "氯气微量泄漏",
    "category": "安全环保",
    "theme": "danger",
    "name": "液氯钢瓶连接处泄漏"
  },
  {
    "id": "SAFE-023@risktest.com",
    "level": "2",
    "deadline": "今日17:00前",
    "riskLevel": "中",
    "reason": "静电接地失效",
    "category": "安全环保",
    "theme": "warning",
    "name": "甲苯装卸区防静电检测"
  },
  {
    "id": "SAFE-024@risktest.com",
    "level": "3",
    "deadline": "3天内",
    "riskLevel": "低",
    "reason": "劳保用品缺失",
    "category": "安全环保",
    "theme": "info",
    "name": "防护手套库存不足"
  },
  {
    "id": "SAFE-025@risktest.com",
    "level": "1",
    "deadline": "1小时内",
    "riskLevel": "高",
    "reason": "受限空间报警",
    "category": "安全环保",
    "theme": "danger",
    "name": "储罐内作业人员失联"
  },
  {
    "id": "SAFE-026@risktest.com",
    "level": "2",
    "deadline": "本周内",
    "riskLevel": "中",
    "reason": "消防水压不足",
    "category": "安全环保",
    "theme": "warning",
    "name": "消防泵房压力异常"
  },

  // ================= 日常事务（3条）=================
  {
    "id": "ADM-416@risktest.com",
    "level": "4",
    "deadline": "季度末前",
    "riskLevel": "低",
    "reason": "档案整理",
    "category": "日常事务",
    "theme": "info",
    "name": "设备检修记录归档"
  },
  {
    "id": "ADM-417@risktest.com",
    "level": "3",
    "deadline": "明日12:00前",
    "riskLevel": "低",
    "reason": "会议准备",
    "category": "日常事务",
    "theme": "info",
    "name": "安委会材料收集"
  },
  {
    "id": "ADM-418@risktest.com",
    "level": "4",
    "deadline": "持续更新",
    "riskLevel": "低",
    "reason": "知识管理",
    "category": "日常事务",
    "theme": "info",
    "name": "工艺变更记录维护"
  },
  // ============= 特种设备风险（5条）=============
  {
    "id": "SPEC-501@risktest.com",
    "level": "1",
    "deadline": "立即停用",
    "riskLevel": "高",
    "reason": "超压未泄放",
    "category": "安全环保",
    "theme": "danger",
    "name": "反应釜安全阀卡涩"
  },
  {
    "id": "SPEC-502@risktest.com",
    "level": "2",
    "deadline": "今日内",
    "riskLevel": "中",
    "reason": "年度检测超期",
    "category": "生产运维",
    "theme": "warning",
    "name": "起重机械未报检"
  },
  {
    "id": "SPEC-503@risktest.com",
    "level": "1",
    "deadline": "30分钟内",
    "riskLevel": "高",
    "reason": "壁厚不达标",
    "category": "安全环保",
    "theme": "danger",
    "name": "压力管道超声检测异常"
  },
  {
    "id": "SPEC-504@risktest.com",
    "level": "3",
    "deadline": "48小时内",
    "riskLevel": "低",
    "reason": "校验标签缺失",
    "category": "生产运维",
    "theme": "info",
    "name": "可燃气体探头校验"
  },
  {
    "id": "SPEC-505@risktest.com",
    "level": "2",
    "deadline": "本周五前",
    "riskLevel": "中",
    "reason": "防爆认证过期",
    "category": "安全环保",
    "theme": "warning",
    "name": "配电箱防爆改造"
  },

  // ============= 能源管理（5条）=============
  {
    "id": "ENER-601@risktest.com",
    "level": "1",
    "deadline": "立即切换",
    "riskLevel": "高",
    "reason": "主电源失电",
    "category": "生产运维",
    "theme": "danger",
    "name": "应急发电机自启失败"
  },
  {
    "id": "ENER-602@risktest.com",
    "level": "2",
    "deadline": "2小时内",
    "riskLevel": "中",
    "reason": "蒸汽压力不足",
    "category": "生产运维",
    "theme": "warning",
    "name": "锅炉给水泵故障"
  },
  {
    "id": "ENER-603@risktest.com",
    "level": "3",
    "deadline": "本周内",
    "riskLevel": "低",
    "reason": "能效不达标",
    "category": "生产运维",
    "theme": "info",
    "name": "冷冻机组COP值下降"
  },
  {
    "id": "ENER-604@risktest.com",
    "level": "1",
    "deadline": "15分钟内",
    "riskLevel": "高",
    "reason": "全厂仪表风中断",
    "category": "生产运维",
    "theme": "danger",
    "name": "空压机连锁停机"
  },
  {
    "id": "ENER-605@risktest.com",
    "level": "4",
    "deadline": "月底前",
    "riskLevel": "低",
    "reason": "月度平衡分析",
    "category": "日常事务",
    "theme": "info",
    "name": "水平衡测试报告"
  },

  // ============= 特殊作业（5条）=============
  {
    "id": "WORK-701@risktest.com",
    "level": "1",
    "deadline": "立即停止",
    "riskLevel": "高",
    "reason": "气体检测超标",
    "category": "安全环保",
    "theme": "danger",
    "name": "受限空间作业中断"
  },
  {
    "id": "WORK-702@risktest.com",
    "level": "2",
    "deadline": "今日17:00前",
    "riskLevel": "中",
    "reason": "监护人员离岗",
    "category": "安全环保",
    "theme": "warning",
    "name": "高处作业违规通报"
  },
  {
    "id": "WORK-703@risktest.com",
    "level": "3",
    "deadline": "作业前完成",
    "riskLevel": "低",
    "reason": "未进行JSA分析",
    "category": "安全环保",
    "theme": "info",
    "name": "动火作业许可补签"
  },
  {
    "id": "WORK-704@risktest.com",
    "level": "1",
    "deadline": "30分钟内",
    "riskLevel": "高",
    "reason": "盲板抽堵错误",
    "category": "生产运维",
    "theme": "danger",
    "name": "系统隔离失效"
  },
  {
    "id": "WORK-705@risktest.com",
    "level": "2",
    "deadline": "作业全程监控",
    "riskLevel": "中",
    "reason": "放射性探伤",
    "category": "工程进度",
    "theme": "warning",
    "name": "管道焊缝检测警戒"
  },

  // ============= 数字化风险（5条）=============
  {
    "id": "DIGI-801@risktest.com",
    "level": "1",
    "deadline": "立即断网",
    "riskLevel": "高",
    "reason": "病毒入侵",
    "category": "生产运维",
    "theme": "danger",
    "name": "DCS系统网络攻击"
  },
  {
    "id": "DIGI-802@risktest.com",
    "level": "2",
    "deadline": "4小时内",
    "riskLevel": "中",
    "reason": "数据不同步",
    "category": "生产运维",
    "theme": "warning",
    "name": "MES系统接口故障"
  },
  {
    "id": "DIGI-803@risktest.com",
    "level": "3",
    "deadline": "本周内",
    "riskLevel": "低",
    "reason": "密码强度不足",
    "category": "日常事务",
    "theme": "info",
    "name": "账户安全策略升级"
  },
  {
    "id": "DIGI-804@risktest.com",
    "level": "1",
    "deadline": "立即处置",
    "riskLevel": "高",
    "reason": "控制指令篡改",
    "category": "安全环保",
    "theme": "danger",
    "name": "SIS系统通讯异常"
  },
  {
    "id": "DIGI-805@risktest.com",
    "level": "4",
    "deadline": "年度更新",
    "riskLevel": "低",
    "reason": "系统版本老旧",
    "category": "日常事务",
    "theme": "info",
    "name": "PLC控制器固件升级"
  }

  ]
});

const exitingTaskHeight = ref(0);

// 标记任务为已回复
const markAsReplied = (task,category) => {
  // 实际应用中这里应该调用API
  console.log(`标记任务 ${task.id} 为已回复`);
  NotifyPlugin.success({
    title:`${task.name}相关邮件已回复,${task.name}已完成`
  })
  let new_task=task
  new_task.status="replied"
  
  // 从数据中移除该任务
  const index = apiResponse.value.data.findIndex(t => t.id === task.id);
  if (index !== -1) {
    // 记录任务高度用于补位动画
    const taskElement = document.querySelector(`.task-card[data-id="${task.id}"]`);
    if (taskElement) {
      exitingTaskHeight.value = taskElement.offsetHeight;
    }
    
    // 从数据中删除任务
    apiResponse.value.data.splice(index, 1);
    let currResponse=[]
    for(let curtask of apiResponse.value.data){
      currResponse.push(curtask)
    }
    currResponse.push(new_task)
    apiResponse.value.data=currResponse
  }
};

// 任务离开前的回调（用于计算高度）
const onTaskLeave = (el) => {
  exitingTaskHeight.value = el.offsetHeight;
};


// 任务数据处理
const tasks = computed(() => {
  return apiResponse.value.data.map(task => {
    let o_rl=task.riskLevel
    let rl=""
    if(o_rl == "小"){
      rl="低"
    }
    else if(o_rl == "大"){
      rl="高"
    }else{
      rl=o_rl
    }
    // 处理数据一致性
    return {
      ...task,
      // 确保所有风险级别值一致
      status: task.status || 'pending',
      riskLevel: rl
    };
  });
});

const transform_ds_logo = (location_ = [100, 100], ds_logo = [[3, 3]]) => {
  return ds_logo.map(point => [
    point[0] + location_[0],
    point[1] + location_[1]
  ]);
};

// 新增排序逻辑：确保 某个元素出现的时候 始终在第一位
function sortCategories(categories) {
  return [...categories].sort((x) => x === "安全环保" ? -1 : 1);
}

// 获取所有唯一的分类（按字母顺序排序）
const categories = computed(() => {
  const uniqueCategories = [...new Set(tasks.value.map(t => t.category))];
  return sortCategories(uniqueCategories); // 使用统一的排序函数
});

const gn_categories = () => {
  const uniqueCategories = [...new Set(tasks.value.map(t => t.category))];
  return sortCategories(uniqueCategories); // 使用统一的排序函数
};


// 获取指定分类的任务（按level升序排序）
const categoryTasks = (category) => {
  return tasks.value
    .filter(task => task.category === category)
    .sort((a, b) => {
      // 第一优先级：状态排序（非 replied 在前）
      if (a.status !== 'replied' && b.status === 'replied') return -1;
      if (a.status === 'replied' && b.status !== 'replied') return 1;
      
      // 第二优先级：按 level 数值升序
      return parseInt(a.level) - parseInt(b.level);
    });
};

// 获取指定分类的任务数量
const categoryTasksCount = (category) => {
  let tasks_=categoryTasks(category)
  let real_tasks=[]
  for(let task_ of tasks_){
    if(task_.status!="replied"){
      real_tasks.push(task_)
    }
  }
  return real_tasks.length
};

// 分类颜色映射
const getCategoryColor = (category) => {
  const colors = {
    '文件报批': '#4e97b9',
    '生产运维': '#8bbf40',
    '工程进度': '#de854e',
    // 可添加更多分类映射
  };
  return colors[category] || '#a5a5a5';
};

// 获取任务标签主题
const taskTheme = (task) => {
  const riskMap = {
    '高': 'danger',
    '中': 'warning',
    '低': 'success',
    '无风险': 'default'
  };
  return riskMap[task.riskLevel] || 'default';
};

// 任务卡片类名
const taskCardClass = (task) => {
  const classes = [];
  
  // 风险级别类
  if (task.riskLevel) {
    classes.push(`risk-${task.riskLevel === '低' ? 'small' : task.riskLevel}`);
  }
  
  // 优先级类
  if (parseInt(task.level) < 3) {
    classes.push('priority-high');
  } else if (parseInt(task.level) === 3) {
    classes.push('priority-medium');
  } else {
    classes.push('priority-low');
  }
    // 添加退出动画类
  if (task.isExiting) {
    classes.push('exiting');
  }
  if (task.status === 'replied') {
    classes.push('replied');
  }
  
  
  return classes.join(' ');
};
// 添加动画控制变量
const kanbanContainer = ref(null);
const animationStarted = ref(false);
// 启动卡片动画
const startCardAnimation = () => {
  nextTick(() => {
    if (!kanbanContainer.value) return;
    
    // 获取所有卡片元素
    const cards = kanbanContainer.value.querySelectorAll('.task-card');
    const containerRect = kanbanContainer.value.getBoundingClientRect();
    
    // 计算起始位置（屏幕底部中间）
    const startX = containerRect.left + containerRect.width / 2;
    const startY = window.innerHeight;
    const shuffledCards = shuffle(cards);
    // 设置卡片初始位置和样式
    shuffledCards.forEach((card, index) => {
      // 记录原始位置
      const originalPosition = card.getBoundingClientRect();
      card.dataset.originalTop = originalPosition.top;
      card.dataset.originalLeft = originalPosition.left;
      
      // 设置初始状态（底部居中，缩小）
      card.style.position = 'fixed';
      card.style.top = `${startY}px`;
      card.style.left = `${startX}px`;
      card.style.transform = 'translate(-50%, -50%) scale(0.8)';
      card.style.opacity = '0';
      card.style.zIndex = '1000';
      card.style.transition = 'none';
    });
    
    // 延迟执行动画
    setTimeout(() => {
      shuffledCards.forEach((card, index) => {
        // 计算延迟时间（每张卡片间隔100ms）
        const delay = index * 100;
        
        // 设置动画
        setTimeout(() => {
          card.style.transition = 'all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)';
          card.style.top = `${card.dataset.originalTop}px`;
          card.style.left = `${card.dataset.originalLeft}px`;
          card.style.transform = 'translate(0, 0) scale(1)';
          card.style.opacity = '1';
          
          // 动画结束后恢复原始状态
          setTimeout(() => {
            card.style.position = '';
            card.style.top = '';
            card.style.left = '';
            card.style.transform = '';
            card.style.opacity = '';
            card.style.zIndex = '';
            card.style.transition = '';
          }, 600);
        }, delay);
      });
    }, 100);
  });
};
const reply_simulation=()=>{
  let ocates=gn_categories()
  let available_categories=[]
  for (let ocate of ocates){
    if(ocate != "安全环保"){
      available_categories.push(ocate)
    }
  }
  let cates=shuffle(available_categories)
  let lucky_category=cates[0]
  let odatas=categoryTasks(lucky_category)
  let tasks=shuffle(odatas)
  let lucky_task=tasks[0]
  markAsReplied(lucky_task,lucky_category)
}
const handleReply=(task_id="")=>{
  let available_categories=gn_categories()
  let lucky_category=null;
  let lucky_task=null;
  for(let cate of available_categories){
    let tasks=categoryTasks(cate)
    for(let task of tasks){
      if(task.id==task_id){
        lucky_category=cate
        lucky_task=task
        break;
      }

    }
    if(lucky_category!=null&&lucky_task!=null){
      break;
    }
  }
  if(lucky_category!=null&&lucky_task!=null){
    markAsReplied(lucky_task,lucky_category)
  }
}

const manualReply=async(task,cate)=>{
  await fetch(`${http_proto}://${endpoint}/task_complete/${task.id}`)
  markAsReplied(task,cate)
}
const showParticleEffect = ref(false);





// 增强的动画流程控制
const runAnimationSequence = async () => {
  try {
    console.log("启动动画序列");
    
    
    
    // 5. 启动卡片动画
    //await new Promise(resolve => setTimeout(resolve, 5000));
    console.log("启动卡片动画");
    console.log(tmp_apiResponse.value.data)
    /*NotifyPlugin.info({
      title:"任务正在更新，请稍候..."
    })*/
    let oldbox=apiResponse.value.data
    let received_box=tmp_apiResponse.value.data
    let new_box=[]
    for(let old_task of oldbox){
      let tl=String(old_task.level)
      console.log(tl)
      if(tl.indexOf("级")!=-1){
        old_task.level=tl.replace("级","")
      }
      new_box.push(old_task)
    }
    for(let new_task of received_box){
      console.log(new_task.level)
      let tl=String(new_task.level)
      if(tl.indexOf("级")!=-1){
        new_task.level=tl.replace("级","")
      }
      new_box.push(new_task)
    }
    apiResponse.value.data=new_box

    startCardAnimation();
    tmp_apiResponse.value.data=[]
    //await new Promise(resolve => setTimeout(resolve, 12000));
    //reply_simulation()
    console.log("动画序列全部完成");
  } catch (error) {
    console.error("动画序列执行失败:", error);
    showParticleEffect.value = false;
  }
};
const fetchInitialTasks=async ()=>{
  let resp=await fetch(`${http_proto}://${endpoint}/list`)
  let json_resp=await resp.json()
  tmp_apiResponse.value.data=json_resp
  if(json_resp.length!=0){
    NotifyPlugin.success({
      title:"已从系统内部自动读取之前任务"
    })
    evbox.emit("card_play_show")
  }else{
    console.log("Damn!There's nothing else to do!")
  }

}
// 确保在组件挂载后执行
onMounted(() => {
  console.log("组件已挂载");
  evbox.on("card_play_show",()=>{
    runAnimationSequence()
  })
  evbox.on("fetch_result",async (data)=>{
    const batch_id=data.batch_id
    let resp=await fetch(`${http_proto}://${endpoint}/batch/${batch_id}`)
    let json_resp=await resp.json()
    let results=json_resp.all_results
    let count=json_resp.total_emails
    tmp_apiResponse.value.data=results
    await evbox.emit("ai_complete",count)
  })
  evbox.on("email_reply",async(data)=>{
    let target_tsk_id=data.task_id
    console.log(target_tsk_id)
    handleReply(target_tsk_id)
  })
  //runAnimationSequence()
  if(tmp_apiResponse.value.data.length==0 && apiResponse.value.data.length==0){
    console.log("I wanna to find history_tasks")
    fetchInitialTasks()
  }
  
});

</script>

<style scoped>
/* 已回复任务样式 */
.task-card.replied {
  background-color: #f9f9f9;
  border-color: #e0e0e0;
  opacity: 0.8;
}

.task-card.replied .task-title,
.task-card.replied .task-details,
.task-card.replied .task-details .t-icon {
  color: #999 !important;
}

.task-card.replied .task-header .t-tag {
  opacity: 0.7;
}

.task-status {
  display: flex;
  align-items: center;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e0e0e0;
  color: #00a870;
  font-size: 12px;
}

.task-status .t-icon {
  margin-right: 4px;
}
/* 保持原有布局样式 */
.project-management-container,
.header, .main-content, .aside, .content,
.action-bar, .kanban-container {
  /* 原有样式保持不变 */
}

/* 动态分类列样式 */
.kanban-column {
  min-width: 300px;
  max-width: 350px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  padding: 16px;
  margin-right: 16px;
}

.column-header {
  display: flex;
  align-items: center;
  padding-bottom: 16px;
  margin-bottom: 16px;
  border-bottom: 1px solid #eee;
  position: relative;
}

.column-header::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: -1px;
  width: 100%;
  height: 2px;
  
}

.column-title {
  font-weight: 600;
  font-size: 16px;
  margin-right: 12px;
  color: #333;
}
/* 新增任务退出动画 */
.task-exit-leave-active {
  transition: all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: absolute;
  width: calc(100% - 32px); /* 减去padding */
  left: 16px; /* 与卡片padding一致 */
}

.task-exit-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

/* 添加移动过渡效果 */
.task-exit-move {
  transition: transform 0.6s ease, opacity 0.6s ease;
}

/* 任务卡片样式增强 */
.task-card {
  background: #fff;
  border-radius: 6px;
  border: 1px solid #eaeaea;
  padding: 14px;
  margin-bottom: 12px;
  transition: all 0.2s ease;
}
/* 卡片飞入时的放大效果 */
@keyframes flyIn {
  0% {
    transform: translateY(100px) scale(0.8);
    opacity: 0;
  }
  70% {
    transform: translateY(-10px) scale(1.05);
    opacity: 1;
  }
  100% {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

.task-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #d0d0d0;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.task-title {
  font-weight: 500;
  font-size: 14px;
  color: #1d2129;
  flex: 1;
  margin-right: 10px;
}

.task-meta {
  flex-shrink: 0;
}

.task-details {
  font-size: 12px;
  color: #666;
  line-height: 1.6;
}

.task-details > div {
  display: flex;
  align-items: center;
  margin-top: 6px;
}

.task-details .t-icon {
  margin-right: 6px;
  font-size: 12px;
}

/* 风险级别指示器 */
.task-card.risk-高 {
  border-left: 4px solid #e34d59;
}

.task-card.risk-中 {
  border-left: 4px solid #ed7b2f;
}

.task-card.risk-低, .task-card.risk-小 {
  border-left: 4px solid #3491fa;
}

/* 优先级指示器 */
.task-card.priority-high::before {
  content: '⚠️ 高优先级';
  display: block;
  font-size: 11px;
  color: #e34d59;
  background: #ffece8;
  padding: 2px 6px;
  border-radius: 4px;
  margin-bottom: 6px;
  width: fit-content;
}

.task-card.priority-medium::before {
  content: '❗ 中等优先级';
  display: block;
  font-size: 11px;
  color: #ed7b2f;
  background: #fff7e8;
  padding: 2px 6px;
  border-radius: 4px;
  margin-bottom: 6px;
  width: fit-content;
}

/* 滚动条样式 */
.kanban-container {
  display: flex;
  overflow-x: auto;
  padding-bottom: 4px;
}

.kanban-container::-webkit-scrollbar {
  height: 6px;
}

.kanban-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.kanban-container::-webkit-scrollbar-thumb {
  background: #d1d1d1;
  border-radius: 3px;
}

.kanban-container::-webkit-scrollbar-thumb:hover {
  background: #a5a5a5;
}
/* 粒子效果蒙层 */
.particle-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.9); /* 白色半透明背景 */
  z-index: 2000;
  pointer-events: none;
}


.particle-canvas {
  position: absolute;
  width: 100%;
  height: 100%;
}
</style>