import './assets/main.css'

import { createApp } from 'vue'
import App from './App.vue'

// 禁用Vue DevTools
const app = createApp(App)
app.config.devtools = false
app.config.productionTip = false
app.mount('#app')
