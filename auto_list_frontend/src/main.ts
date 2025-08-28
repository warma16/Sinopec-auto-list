
import TDesign from 'tdesign-vue-next';
import 'tdesign-vue-next/es/style/index.css';

import { createApp } from 'vue'
import { createPinia } from 'pinia';
import EvBox from './utils/EvBox';
import { get_endpoint } from './utils/get_endpoint';

import App from './App.vue'
import router from './router'

let isDev_=import.meta.env.DEV

const app = createApp(App)

app.use(TDesign);

app.use(createPinia())
app.use(router)
app.config.globalProperties.$evbox = new EvBox();
app.config.globalProperties.$endpoint=get_endpoint(isDev_)
app.config.globalProperties.$ws_proto=`${window.location.protocol}`=="https:"?"wss":"ws"
app.config.globalProperties.$http_proto=`${window.location.protocol}`=="https:"?"https":"http"

app.mount('#app')
