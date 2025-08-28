<script setup >
import { ref, computed, onMounted, getCurrentInstance} from 'vue';
import AIStatus from '@/components/AIStatus.vue';
import WSSDK from "@/utils/WSSDK"
const instance = getCurrentInstance();
const evbox = instance.appContext.config.globalProperties.$evbox;
const ws_proto=instance.appContext.config.globalProperties.$ws_proto
const endpoint=instance.appContext.config.globalProperties.$endpoint
const activeTab1 = ref('task-board');
let ai_=ref(null)
const set_ai=async()=>{
  if(ai_.value){
    //await new Promise(resolve => setTimeout(resolve, 10000));
    ai_.value?.setAIStatus('thinking');
  
  // 模拟网络请求
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // 设置为处理中状态
  ai_.value?.setAIStatus('processing');
  
  // 处理完成后
  await new Promise(resolve => setTimeout(resolve, 3000));
  
  // 设置为完成状态，显示通知
  ai_.value?.setAIStatus('completed', { emailCount: 104 });
  await new Promise(resolve => setTimeout(resolve, 8000));
  }
}
const websocket_inject=async()=>{
  let last_event=""
  const ws=new WSSDK({
    url:`${ws_proto}://${endpoint}/ws`,
  })
  ws.on("message",(json)=>{
    let data=JSON.parse(json)
    let currentEvent=data.event
    console.log(currentEvent)
    if(currentEvent=="queue_updated"){
      evbox.emit("ai_awake")
    }
    if(last_event=="queue_updated"&&currentEvent=="batch_status"){
      evbox.emit("ai_thinking")
    }
    if(currentEvent=="batch_complete"){
      evbox.emit("ai_processing")
      evbox.emit("fetch_result",{
        batch_id:data.data.batch_id
      })
    }
    evbox.emit(currentEvent,data.data)
    last_event=currentEvent
  })
}
const dyn_ai=async()=>{
  evbox.on("ai_thinking",async ()=>{
    if(ai_.value){
      ai_.value?.setAIStatus('thinking');
    }
  })
  evbox.on("ai_awake",async ()=>{
    if(ai_.value){
      ai_.value?.setAIStatus('awake');
    }
  })
  evbox.on("ai_complete",async(count)=>{
    if(ai_.value){
      await ai_.value?.setAIStatus('completed', { emailCount: count });
      await evbox.emit("card_play_show")
    }
  })
  evbox.on("ai_processing",async()=>{
    if(ai_.value){
      ai_.value?.setAIStatus('processing');
    }
  })
}
onMounted(()=>{
  websocket_inject()
  dyn_ai()
  //set_ai()
})
</script>

<template>
  <header>
    <t-header class="header">
      <t-head-menu v-model="menu1Value" theme="light" @change="changeHandler">
        <template #logo>
          <h3>项目管理</h3>
        </template>
        <t-menu-item value="item1"> 工作看板</t-menu-item>
        <t-menu-item value="item2"> 甘特图</t-menu-item>
        <template #operations>
          <AIStatus ref="ai_"></AIStatus>
        </template>
      </t-head-menu>
    </t-header>
  </header>
  <main>
    <RouterView />
  </main>
</template>

<style scoped>
.header {
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  padding: 0 24px;
}

.header-content {
  display: flex;
  align-items: center;
  height: 64px;
}
.title {
  margin-right: 32px;
  font-size: 18px;
  font-weight: 500;
}
</style>
