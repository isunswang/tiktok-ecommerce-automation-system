<template>
  <div class="finance-container">
    <h2 class="page-title">财务管理</h2>

    <!-- 财务概览卡片 -->
    <el-row :gutter="20" class="summary-row" v-loading="summaryLoading">
      <el-col :xs="12" :sm="6" v-for="card in summaryCards" :key="card.title">
        <el-card shadow="hover" class="summary-card" :body-style="{ padding: '20px' }">
          <div class="summary-card-content">
            <div class="summary-info">
              <div class="summary-title">{{ card.title }}</div>
              <div class="summary-value">{{ card.value }}</div>
              <div class="summary-trend" :class="card.trend >= 0 ? 'up' : 'down'">
                {{ card.trend >= 0 ? '+' : '' }}{{ card.trend }}%
                <span class="trend-label">较上期</span>
              </div>
            </div>
            <div class="summary-icon" :style="{ backgroundColor: card.bgColor }">
              <el-icon :size="28" :style="{ color: card.iconColor }">
                <component :is="card.icon" />
              </el-icon>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 交易记录 -->
    <el-card shadow="hover">
      <template #header>
        <span>交易记录</span>
      </template>

      <!-- 筛选栏 -->
      <div class="filter-bar">
        <el-select v-model="txFilter.type" placeholder="全部类型" clearable style="width: 120px">
          <el-option v-for="(label, key) in txTypeMap" :key="key" :label="label" :value="key" />
        </el-select>
        <el-select v-model="txFilter.period" placeholder="时间周期" style="width: 120px" @change="fetchTransactions">
          <el-option label="按日" value="daily" />
          <el-option label="按周" value="weekly" />
          <el-option label="按月" value="monthly" />
        </el-select>
        <el-button type="primary" @click="fetchTransactions">搜索</el-button>
      </div>

      <!-- 交易表格 -->
      <el-table :data="transactions" stripe v-loading="txLoading" style="width: 100%">
        <el-table-column prop="id" label="交易ID" width="180" show-overflow-tooltip />
        <el-table-column prop="order_id" label="订单ID" width="180" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="txTagType(row.type)" size="small">{{ txTypeMap[row.type] || row.type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="120" align="right">
          <template #default="{ row }">
            <span :class="amountClass(row.type)">{{ formatAmount(row.amount, row.type) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="currency" label="货币" width="70" align="center" />
        <el-table-column prop="exchange_rate" label="汇率" width="90" align="right">
          <template #default="{ row }">{{ row.exchange_rate ?? '-' }}</template>
        </el-table-column>
        <el-table-column prop="cny_amount" label="人民币金额" width="120" align="right">
          <template #default="{ row }">
            <span :class="amountClass(row.type)">{{ formatCNY(row.cny_amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column prop="site" label="站点" width="80" align="center" />
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="txPage"
          v-model:page-size="txPageSize"
          :total="txTotal"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="fetchTransactions"
          @current-change="fetchTransactions"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, markRaw } from 'vue'
import { ElMessage } from 'element-plus'
import { TrendCharts, Coin, Wallet, DataLine } from '@element-plus/icons-vue'
import { getFinanceSummary, getTransactions } from '@/api'

// ========== 类型映射 ==========
const txTypeMap: Record<string, string> = {
  income: '收入',
  cost: '成本',
  refund: '退款',
  fee: '手续费',
  withdrawal: '提现',
}

function txTagType(type: string): string {
  const map: Record<string, string> = { income: 'success', cost: 'danger', refund: 'warning', fee: 'info', withdrawal: 'primary' }
  return map[type] || 'info'
}

// ========== 工具函数 ==========
function formatAmount(val: number | undefined, type: string): string {
  if (val === undefined || val === null) return '-'
  const prefix = type === 'refund' || type === 'cost' ? '-' : ''
  return `${prefix}$${Number(val).toFixed(2)}`
}

function formatCNY(val: number | undefined): string {
  if (val === undefined || val === null) return '-'
  return `¥${Number(val).toFixed(2)}`
}

function amountClass(type: string): string {
  if (type === 'income') return 'amount-income'
  if (type === 'cost') return 'amount-cost'
  if (type === 'refund') return 'amount-refund'
  return ''
}

function formatTime(val: string | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return val
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ========== 财务概览 ==========
const summaryLoading = ref(false)
const summaryData = ref<any>({})

const summaryCards = ref([
  { title: '总收入', value: '¥0.00', trend: 0, icon: markRaw(TrendCharts), iconColor: '#67C23A', bgColor: '#F0F9EB' },
  { title: '总成本', value: '¥0.00', trend: 0, icon: markRaw(Coin), iconColor: '#F56C6C', bgColor: '#FEF0F0' },
  { title: '净利润', value: '¥0.00', trend: 0, icon: markRaw(Wallet), iconColor: '#409EFF', bgColor: '#ECF5FF' },
  { title: '利润率', value: '0%', trend: 0, icon: markRaw(DataLine), iconColor: '#E6A23C', bgColor: '#FDF6EC' },
])

async function fetchSummary() {
  summaryLoading.value = true
  try {
    const res = await getFinanceSummary({ period: 'monthly' })
    const data = res.data || res
    summaryData.value = data

    summaryCards.value[0].value = `¥${Number(data.total_revenue || 0).toFixed(2)}`
    summaryCards.value[0].trend = Number(data.revenue_growth || 0)

    summaryCards.value[1].value = `¥${Number(data.total_cost || 0).toFixed(2)}`
    summaryCards.value[1].trend = Number(data.cost_growth || 0)

    summaryCards.value[2].value = `¥${Number(data.net_profit || 0).toFixed(2)}`
    summaryCards.value[2].trend = Number(data.profit_growth || 0)

    summaryCards.value[3].value = `${Number(data.profit_rate || 0).toFixed(1)}%`
    summaryCards.value[3].trend = Number(data.profit_rate_growth || 0)
  } catch (e: any) {
    ElMessage.error(e?.message || '获取财务概览失败')
  } finally {
    summaryLoading.value = false
  }
}

// ========== 交易记录 ==========
const txLoading = ref(false)
const transactions = ref<any[]>([])
const txPage = ref(1)
const txPageSize = ref(10)
const txTotal = ref(0)
const txFilter = reactive({ type: '', period: 'monthly' })

async function fetchTransactions() {
  txLoading.value = true
  try {
    const params: Record<string, unknown> = { page: txPage.value, page_size: txPageSize.value }
    if (txFilter.type) params.type = txFilter.type
    const res = await getTransactions(params)
    const data = res.data || res
    transactions.value = data.items || data.results || data.list || data.data || []
    txTotal.value = data.total || data.count || 0
  } catch (e: any) {
    ElMessage.error(e?.message || '获取交易记录失败')
  } finally {
    txLoading.value = false
  }
}

// ========== 初始化 ==========
onMounted(() => {
  fetchSummary()
  fetchTransactions()
})
</script>

<style scoped>
.finance-container { padding: 20px; }
.page-title { margin: 0 0 16px; font-size: 22px; color: #303133; }
.summary-row { margin-bottom: 20px; }
.summary-card-content { display: flex; justify-content: space-between; align-items: center; }
.summary-info { flex: 1; }
.summary-title { font-size: 14px; color: #909399; margin-bottom: 8px; }
.summary-value { font-size: 24px; font-weight: 700; color: #303133; margin-bottom: 8px; }
.summary-trend { font-size: 12px; display: flex; align-items: center; gap: 2px; }
.summary-trend.up { color: #67C23A; }
.summary-trend.down { color: #F56C6C; }
.trend-label { color: #909399; margin-left: 4px; }
.summary-icon { width: 56px; height: 56px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.filter-bar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
.amount-income { color: #67C23A; font-weight: 600; }
.amount-cost { color: #F56C6C; font-weight: 600; }
.amount-refund { color: #E6A23C; font-weight: 600; }
</style>
