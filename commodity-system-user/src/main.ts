import { createApp } from 'vue'
import App from './App.vue'
import router from '@/router'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import '@/styles/index.css'
import { useUserStore } from '@/stores/user'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, BarChart, LineChart, GridComponent, LegendComponent, TooltipComponent, TitleComponent])

const app = createApp(App)

const pinia = createPinia()
app.use(pinia)

const userStore = useUserStore()
userStore.restore()

app.use(router)
app.use(ElementPlus)
app.component('VChart', VChart)

app.mount('#app')
