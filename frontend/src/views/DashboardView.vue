<template>
  <div class="dashboard-container">
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
          <el-button type="primary" link>查看全部</el-button>
        </div>
      </template>
      <el-table :data="recentOrders" stripe style="width: 100%">
        <el-table-column prop="orderId" label="订单编号" width="160" />
        <el-table-column prop="product" label="商品" />
        <el-table-column prop="amount" label="金额" width="100">
          <template #default="{ row }">¥{{ row.amount }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type || 'info'" size="small">
              {{ statusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="time" label="时间" width="170" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, markRaw } from 'vue'
import { ShoppingCart, Money, Clock, Goods } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const salesChartRef = ref<HTMLElement>()
const orderChartRef = ref<HTMLElement>()
let salesChart: echarts.ECharts | null = null
let orderChart: echarts.ECharts | null = null

const statusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待处理', type: 'warning' },
  shipped: { label: '已发货', type: 'primary' },
  delivered: { label: '已送达', type: 'success' },
  cancelled: { label: '已取消', type: 'danger' },
}

const statCards = ref([
  { title: '今日订单', value: '128', trend: 12.5, icon: markRaw(ShoppingCart), iconColor: '#409EFF', bgColor: '#ECF5FF' },
  { title: '今日销售额', value: '¥32,680', trend: 8.2, icon: markRaw(Money), iconColor: '#67C23A', bgColor: '#F0F9EB' },
  { title: '待处理订单', value: '23', trend: -3.1, icon: markRaw(Clock), iconColor: '#E6A23C', bgColor: '#FDF6EC' },
  { title: '商品总数', value: '1,056', trend: 2.4, icon: markRaw(Goods), iconColor: '#F56C6C', bgColor: '#FEF0F0' },
])

const recentOrders = ref([
  { orderId: 'TK20250101001', product: '无线蓝牙耳机', amount: '299.00', status: 'pending', time: '2025-01-01 14:30' },
  { orderId: 'TK20250101002', product: '手机壳 (星空款)', amount: '39.90', status: 'shipped', time: '2025-01-01 13:22' },
  { orderId: 'TK20250101003', product: '便携充电宝 20000mAh', amount: '189.00', status: 'delivered', time: '2025-01-01 11:45' },
  { orderId: 'TK20250101004', product: 'LED台灯', amount: '79.00', status: 'cancelled', time: '2025-01-01 10:18' },
  { orderId: 'TK20250101005', product: '运动水杯', amount: '49.90', status: 'pending', time: '2025-01-01 09:05' },
])

function initSalesChart() {
  if (!salesChartRef.value) return
  salesChart = echarts.init(salesChartRef.value)
  salesChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'] },
    yAxis: { type: 'value', name: '销售额(元)' },
    series: [{
      name: '销售额', type: 'line', smooth: true, areaStyle: { opacity: 0.3 },
      data: [28200, 31500, 26800, 35600, 32100, 42300, 32680], itemStyle: { color: '#409EFF' },
    }],
  })
}

function initOrderChart() {
  if (!orderChartRef.value) return
  orderChart = echarts.init(orderChartRef.value)
  orderChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: '0', left: 'center' },
    series: [{
      name: '订单状态', type: 'pie', radius: ['40%', '70%'], avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
      label: { show: false, position: 'center' },
      emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
      labelLine: { show: false },
      data: [
        { value: 23, name: '待处理', itemStyle: { color: '#E6A23C' } },
        { value: 56, name: '已发货', itemStyle: { color: '#409EFF' } },
        { value: 38, name: '已送达', itemStyle: { color: '#67C23A' } },
        { value: 11, name: '已取消', itemStyle: { color: '#F56C6C' } },
      ],
    }],
  })
}

function handleResize() {
  salesChart?.resize()
  orderChart?.resize()
}

onMounted(() => {
  initSalesChart()
  initOrderChart()
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
