<template>
  <div class="dashboard-container" v-loading="loading">
    <div class="dashboard-header">
      <h2>工作台</h2>
      <p class="dashboard-subtitle">欢迎回来，{{ userStore.userInfo?.nickname || '管理员' }}！</p>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6" v-for="item in statCards" :key="item.title">
        <el-card shadow="hover" class="stat-card" :body-style="{ padding: '20px' }">
          <div class="stat-card-content">
            <div class="stat-info">
              <div class="stat-title">{{ item.title }}</div>
              <div class="stat-value">{{ item.value }}</div>
              <div class="stat-trend" :class="item.trend > 0 ? 'up' : 'down'">
                {{ Math.abs(item.trend) }}%
                <span class="stat-trend-label">较昨日</span>
              </div>
            </div>
            <div class="stat-icon" :style="{ backgroundColor: item.bgColor }">
              <el-icon :size="28" :style="{ color: item.iconColor }">
                <component :is="item.icon" />
              </el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :xs="24" :lg="16">
        <el-card shadow="hover">
          <template #header><span>销售趋势</span></template>
          <div ref="salesChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="8">
        <el-card shadow="hover">
          <template #header><span>订单状态分布</span></template>
          <div ref="orderChartRef" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" class="recent-orders">
      <template #header>
        <div class="card-header">
          <span>最近订单</span>
          <el-button type="primary" link @click="router.push('/orders')">查看全部</el-button>
        </div>
      </template>
      <el-table :data="recentOrders" stripe style="width: 100%">
        <el-table-column prop="tiktok_order_id" label="订单编号" width="180" />
        <el-table-column prop="buyer_name" label="买家" />
        <el-table-column prop="total_amount" label="金额" width="120">
          <template #default="{ row }">${{ Number(row.total_amount).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">
              {{ statusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { ShoppingCart, Money, Clock, Goods } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { useUserStore } from '@/stores/user'
import {
  getDashboardStats,
  getDashboardRecentOrders,
  getDashboardSalesTrend,
  getDashboardOrderDistribution,
} from '@/api/index'

const router = useRouter()
const userStore = useUserStore()
const salesChartRef = ref<HTMLElement>()
const orderChartRef = ref<HTMLElement>()
let salesChart: echarts.ECharts | null = null
let orderChart: echarts.ECharts | null = null
const loading = ref(false)

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待处理', type: 'warning' },
  matched: { label: '已匹配', type: '' },
  matching_failed: { label: '匹配失败', type: 'danger' },
  confirmed: { label: '已确认', type: 'primary' },
  purchased: { label: '已采购', type: 'primary' },
  shipped: { label: '已发货', type: 'primary' },
  delivered: { label: '已送达', type: 'success' },
  completed: { label: '已完成', type: 'success' },
  cancelled: { label: '已取消', type: 'danger' },
}

const statCards = ref([
  { title: '今日订单', value: '-', trend: 0, icon: markRaw(ShoppingCart), iconColor: '#409EFF', bgColor: '#ECF5FF' },
  { title: '今日销售额', value: '-', trend: 0, icon: markRaw(Money), iconColor: '#67C23A', bgColor: '#F0F9EB' },
  { title: '待处理订单', value: '-', trend: 0, icon: markRaw(Clock), iconColor: '#E6A23C', bgColor: '#FDF6EC' },
  { title: '商品总数', value: '-', trend: 0, icon: markRaw(Goods), iconColor: '#F56C6C', bgColor: '#FEF0F0' },
])

const recentOrders = ref<any[]>([])

function formatTime(isoStr: string) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function formatMoney(val: string | number) {
  const num = typeof val === 'string' ? parseFloat(val) : val
  return num.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
}

function initSalesChart(dates: string[], sales: number[]) {
  if (!salesChartRef.value) return
  if (!salesChart) salesChart = echarts.init(salesChartRef.value)
  salesChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: dates },
    yAxis: { type: 'value', name: '销售额($)' },
    series: [{
      name: '销售额', type: 'line', smooth: true, areaStyle: { opacity: 0.3 },
      data: sales, itemStyle: { color: '#409EFF' },
    }],
  }, true)
}

function initOrderChart(data: { name: string; value: number }[]) {
  if (!orderChartRef.value) return
  if (!orderChart) orderChart = echarts.init(orderChartRef.value)
  const colorMap: Record<string, string> = {
    '待处理': '#E6A23C', '已匹配': '#909399', '匹配失败': '#F56C6C',
    '已确认': '#409EFF', '已采购': '#409EFF', '已发货': '#409EFF',
    '已送达': '#67C23A', '已完成': '#67C23A', '已取消': '#F56C6C',
  }
  orderChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: '0', left: 'center' },
    series: [{
      name: '订单状态', type: 'pie', radius: ['40%', '70%'], avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false, position: 'center' },
      emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
      labelLine: { show: false },
      data: data.map(d => ({ ...d, itemStyle: { color: colorMap[d.name] || '#909399' } })),
    }],
  }, true)
}

function handleResize() {
  salesChart?.resize()
  orderChart?.resize()
}

async function loadDashboardData() {
  loading.value = true
  try {
    const [statsRes, ordersRes, trendRes, distRes] = await Promise.allSettled([
      getDashboardStats(),
      getDashboardRecentOrders(),
      getDashboardSalesTrend(),
      getDashboardOrderDistribution(),
    ])

    // 统计卡片
    if (statsRes.status === 'fulfilled' && statsRes.value) {
      const s = statsRes.value
      statCards.value[0].value = String(s.today_orders)
      statCards.value[0].trend = s.order_trend || 0
      statCards.value[1].value = formatMoney(s.today_sales)
      statCards.value[1].trend = s.sales_trend || 0
      statCards.value[2].value = String(s.pending_orders)
      statCards.value[2].trend = s.pending_trend || 0
      statCards.value[3].value = String(s.total_products)
      statCards.value[3].trend = s.product_trend || 0
    }

    // 最近订单
    if (ordersRes.status === 'fulfilled' && Array.isArray(ordersRes.value)) {
      recentOrders.value = ordersRes.value
    }

    // 销售趋势图
    if (trendRes.status === 'fulfilled' && trendRes.value) {
      initSalesChart(trendRes.value.dates || [], trendRes.value.sales || [])
    }

    // 订单状态饼图
    if (distRes.status === 'fulfilled' && distRes.value?.data) {
      initOrderChart(distRes.value.data)
    }
  } catch (e: any) {
    ElMessage.error('加载仪表盘数据失败')
    console.error('Dashboard load error:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDashboardData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  salesChart?.dispose()
  orderChart?.dispose()
})
</script>

<style scoped>
.dashboard-container { padding: 20px; }
.dashboard-header { margin-bottom: 24px; }
.dashboard-header h2 { margin: 0 0 4px; font-size: 22px; color: #303133; }
.dashboard-subtitle { margin: 0; font-size: 14px; color: #909399; }
.stats-row { margin-bottom: 20px; }
.stat-card-content { display: flex; justify-content: space-between; align-items: center; }
.stat-title { font-size: 14px; color: #909399; margin-bottom: 8px; }
.stat-value { font-size: 24px; font-weight: 700; color: #303133; margin-bottom: 8px; }
.stat-trend { font-size: 12px; display: flex; align-items: center; gap: 2px; }
.stat-trend.up { color: #67C23A; }
.stat-trend.down { color: #F56C6C; }
.stat-trend-label { color: #909399; margin-left: 4px; }
.stat-icon { width: 56px; height: 56px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.chart-row { margin-bottom: 20px; }
.chart-container { height: 320px; width: 100%; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.recent-orders { margin-bottom: 20px; }
</style>
