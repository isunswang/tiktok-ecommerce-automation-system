<template>
  <div class="orders-container">
    <!-- 页面标题栏 -->
    <div class="page-header">
      <h2>订单管理</h2>
    </div>

    <!-- 搜索筛选栏 -->
    <el-card shadow="hover" class="filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :xs="24" :sm="8" :md="6">
          <el-input
            v-model="filters.search"
            placeholder="搜索订单编号/买家..."
            clearable
            @keyup.enter="handleSearch"
          />
        </el-col>
        <el-col :xs="24" :sm="6" :md="4">
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 100%">
            <el-option v-for="(label, key) in statusMap" :key="key" :label="label" :value="key" />
          </el-select>
        </el-col>
        <el-col :xs="24" :sm="10" :md="6">
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 订单列表 -->
    <el-card shadow="hover" class="table-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        style="width: 100%"
        row-key="id"
      >
        <el-table-column prop="tiktok_order_id" label="订单编号" width="180" show-overflow-tooltip />
        <el-table-column prop="buyer_name" label="买家" width="120" show-overflow-tooltip />
        <el-table-column label="金额" width="120" align="right">
          <template #default="{ row }">
            {{ currencySymbol(row.currency) }}{{ formatMoney(row.total_amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="currency" label="货币" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusTagMap[row.status] || 'info'" size="small">
              {{ statusMap[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tracking_number" label="物流单号" width="160" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.tracking_number || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleViewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页器 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="fetchOrders"
          @current-change="fetchOrders"
        />
      </div>
    </el-card>

    <!-- 订单详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="订单详情"
      direction="rtl"
      size="480px"
      destroy-on-close
    >
      <div v-if="currentOrder" class="order-detail">
        <el-descriptions :column="1" border size="small">
          <el-descriptions-item label="订单编号">
            {{ currentOrder.tiktok_order_id || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagMap[currentOrder.status] || 'info'" size="small">
              {{ statusMap[currentOrder.status] || currentOrder.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="金额">
            {{ currencySymbol(currentOrder.currency) }}{{ formatMoney(currentOrder.total_amount) }}
          </el-descriptions-item>
          <el-descriptions-item label="货币">
            {{ currentOrder.currency || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="买家姓名">
            {{ currentOrder.buyer_name || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="收货地址">
            <pre class="address-pre">{{ formatAddress(currentOrder.shipping_address) }}</pre>
          </el-descriptions-item>
          <el-descriptions-item label="物流单号">
            {{ currentOrder.tracking_number || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="备注">
            {{ currentOrder.remark || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatTime(currentOrder.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatTime(currentOrder.updated_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 状态流转操作 -->
        <div class="status-update-section">
          <h4>状态流转</h4>
          <div class="status-update-row">
            <el-select
              v-model="newStatus"
              placeholder="选择目标状态"
              style="flex: 1; margin-right: 12px"
            >
              <el-option
                v-for="s in availableTransitions"
                :key="s"
                :label="statusMap[s] || s"
                :value="s"
              />
            </el-select>
            <el-button
              type="primary"
              :disabled="!newStatus"
              :loading="statusUpdating"
              @click="handleUpdateStatus"
            >
              确认
            </el-button>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="drawerVisible = false">关闭</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getOrders, getOrder, updateOrderStatus } from '@/api'

// ========== 状态映射 ==========
const statusMap: Record<string, string> = {
  pending: '待处理',
  matched: '已匹配',
  matching_failed: '匹配失败',
  confirmed: '已确认',
  purchased: '已采购',
  shipped: '已发货',
  delivered: '已送达',
  completed: '已完成',
  cancelled: '已取消',
}

const statusTagMap: Record<string, string> = {
  pending: 'danger',
  matched: 'warning',
  matching_failed: 'danger',
  confirmed: 'primary',
  purchased: 'primary',
  shipped: 'primary',
  delivered: 'success',
  completed: 'success',
  cancelled: 'info',
}

// 合法的状态流转路径
const stateTransitions: Record<string, string[]> = {
  pending: ['matched', 'matching_failed', 'cancelled'],
  matched: ['confirmed', 'cancelled'],
  matching_failed: ['matched', 'cancelled'],
  confirmed: ['purchased', 'cancelled'],
  purchased: ['shipped', 'cancelled'],
  shipped: ['delivered'],
  delivered: ['completed'],
}

// ========== 筛选条件 ==========
const filters = reactive({
  search: '',
  status: '',
})

// ========== 分页 ==========
const pagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0,
})

// ========== 表格数据 ==========
const loading = ref(false)
const tableData = ref<any[]>([])

// ========== 抽屉详情 ==========
const drawerVisible = ref(false)
const currentOrder = ref<any>(null)
const newStatus = ref('')
const statusUpdating = ref(false)

// 当前订单可流转的状态列表
const availableTransitions = computed(() => {
  if (!currentOrder.value) return []
  const current = currentOrder.value.status
  return stateTransitions[current] || []
})

// ========== 方法 ==========

/** 金额格式化 */
function formatMoney(value: number | undefined): string {
  if (value === undefined || value === null) return '0.00'
  return Number(value).toFixed(2)
}

/** 货币符号 */
function currencySymbol(currency: string | undefined): string {
  const symbols: Record<string, string> = {
    CNY: '¥',
    USD: '$',
    EUR: '€',
    GBP: '£',
    JPY: '¥',
  }
  return symbols[currency || ''] || ''
}

/** 时间格式化：YYYY-MM-DD HH:mm */
function formatTime(value: string | undefined): string {
  if (!value) return '-'
  const d = new Date(value)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** 格式化地址信息（JSON→可读字符串） */
function formatAddress(address: any): string {
  if (!address) return '-'
  // 如果是字符串，尝试解析JSON
  if (typeof address === 'string') {
    try {
      address = JSON.parse(address)
    } catch {
      return address
    }
  }
  // 如果是对象，拼接为可读字符串
  if (typeof address === 'object') {
    const parts: string[] = []
    if (address.name) parts.push(`姓名: ${address.name}`)
    if (address.phone) parts.push(`电话: ${address.phone}`)
    if (address.province) parts.push(`省: ${address.province}`)
    if (address.city) parts.push(`市: ${address.city}`)
    if (address.district) parts.push(`区: ${address.district}`)
    if (address.address) parts.push(`详细地址: ${address.address}`)
    if (address.zip) parts.push(`邮编: ${address.zip}`)
    return parts.length > 0 ? parts.join('\n') : JSON.stringify(address, null, 2)
  }
  return String(address)
}

/** 加载订单列表 */
async function fetchOrders() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.search) params.search = filters.search
    if (filters.status) params.status = filters.status

    const res: any = await getOrders(params)
    tableData.value = res.items || res.data || []
    pagination.total = res.total || 0
  } catch (err: any) {
    ElMessage.error('加载订单列表失败')
  } finally {
    loading.value = false
  }
}

/** 搜索 */
function handleSearch() {
  pagination.page = 1
  fetchOrders()
}

/** 重置筛选 */
function handleReset() {
  filters.search = ''
  filters.status = ''
  pagination.page = 1
  fetchOrders()
}

/** 查看订单详情 */
async function handleViewDetail(row: any) {
  newStatus.value = ''
  try {
    const res: any = await getOrder(row.id)
    currentOrder.value = res
    drawerVisible.value = true
  } catch (err: any) {
    ElMessage.error('获取订单详情失败')
  }
}

/** 更新订单状态 */
async function handleUpdateStatus() {
  if (!currentOrder.value || !newStatus.value) return
  statusUpdating.value = true
  try {
    await updateOrderStatus(currentOrder.value.id, { status: newStatus.value })
    ElMessage.success('状态更新成功')
    currentOrder.value.status = newStatus.value
    newStatus.value = ''
    fetchOrders()
  } catch (err: any) {
    ElMessage.error('状态更新失败')
  } finally {
    statusUpdating.value = false
  }
}

// ========== 生命周期 ==========
onMounted(() => {
  fetchOrders()
})
</script>

<style scoped>
.orders-container {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 22px;
  color: #303133;
}

.filter-card {
  margin-bottom: 16px;
}

.filter-card .el-row .el-col {
  margin-bottom: 8px;
}

.filter-card .el-col:last-child {
  margin-bottom: 0;
}

.table-card {
  margin-bottom: 16px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 16px 0 4px;
}

/* 订单详情抽屉 */
.order-detail {
  padding: 0 4px;
}

.address-pre {
  margin: 0;
  font-family: inherit;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.6;
  background: #f5f7fa;
  padding: 8px 12px;
  border-radius: 4px;
}

.status-update-section {
  margin-top: 24px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.status-update-section h4 {
  margin: 0 0 12px;
  font-size: 15px;
  color: #303133;
}

.status-update-row {
  display: flex;
  align-items: center;
}
</style>
