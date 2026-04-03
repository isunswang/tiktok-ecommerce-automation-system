<template>
  <div class="fulfillment-container">
    <h2 class="page-title">履约管理</h2>

    <el-tabs v-model="activeTab" @tab-change="handleTabChange">
      <!-- Tab1: 采购管理 -->
      <el-tab-pane label="采购管理" name="purchase">
        <!-- 操作栏 -->
        <div class="toolbar">
          <div class="toolbar-left">
            <el-select v-model="poFilter.status" placeholder="全部状态" clearable style="width: 140px" @change="fetchPurchaseOrders">
              <el-option v-for="(label, key) in poStatusMap" :key="key" :label="label" :value="key" />
            </el-select>
          </div>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon> 新建采购单
          </el-button>
        </div>

        <!-- 采购单表格 -->
        <el-table :data="purchaseOrders" stripe v-loading="poLoading" style="width: 100%">
          <el-table-column prop="alibaba_order_id" label="采购单号" width="180" show-overflow-tooltip />
          <el-table-column prop="supplier_id" label="供应商ID" width="180" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="poTagType(row.status)" size="small">{{ poStatusMap[row.status] || row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="total_amount" label="总金额" width="120" align="right">
            <template #default="{ row }">¥{{ formatAmount(row.total_amount) }}</template>
          </el-table-column>
          <el-table-column prop="tracking_number" label="物流单号" width="180" show-overflow-tooltip />
          <el-table-column label="关联订单" min-width="200">
            <template #default="{ row }">
              <template v-if="row.linked_order_ids?.length">
                <el-tag v-for="id in row.linked_order_ids" :key="id" size="small" class="order-tag">{{ id.slice(0, 8) }}</el-tag>
              </template>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="170">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="viewPurchaseDetail(row)">查看详情</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrap">
          <el-pagination
            v-model:current-page="poPage"
            v-model:page-size="poPageSize"
            :total="poTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="fetchPurchaseOrders"
            @current-change="fetchPurchaseOrders"
          />
        </div>
      </el-tab-pane>

      <!-- Tab2: 物流管理 -->
      <el-tab-pane label="物流管理" name="shipment">
        <el-table :data="shipments" stripe v-loading="shipmentLoading" style="width: 100%">
          <el-table-column prop="tracking_number" label="物流单号" width="180" show-overflow-tooltip />
          <el-table-column prop="carrier" label="承运商" width="140" />
          <el-table-column prop="status" label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="shipmentTagType(row.status)" size="small">{{ shipmentStatusMap[row.status] || row.status }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="origin" label="发货地" width="140" show-overflow-tooltip />
          <el-table-column prop="destination" label="目的地" width="140" show-overflow-tooltip />
          <el-table-column prop="estimated_delivery" label="预计送达" width="170">
            <template #default="{ row }">{{ formatTime(row.estimated_delivery) }}</template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="170">
            <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link size="small" @click="viewLogistics(row)">物流轨迹</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pagination-wrap">
          <el-pagination
            v-model:current-page="shipmentPage"
            v-model:page-size="shipmentPageSize"
            :total="shipmentTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="fetchShipments"
            @current-change="fetchShipments"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建采购单弹窗 -->
    <el-dialog v-model="showCreateDialog" title="新建采购单" width="520px" destroy-on-close>
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="供应商ID" prop="supplier_id">
          <el-input v-model="createForm.supplier_id" placeholder="请输入供应商ID" />
        </el-form-item>
        <el-form-item label="关联订单" prop="linked_order_ids">
          <el-input v-model="createForm.linked_order_ids" type="textarea" :rows="3" placeholder="请输入关联订单ID，多个用逗号分隔" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="createForm.remark" type="textarea" :rows="2" placeholder="备注信息（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreatePO">确定</el-button>
      </template>
    </el-dialog>

    <!-- 采购单详情弹窗 -->
    <el-dialog v-model="showDetailDialog" title="采购单详情" width="600px">
      <el-descriptions :column="2" border v-if="currentPO">
        <el-descriptions-item label="采购单号">{{ currentPO.alibaba_order_id }}</el-descriptions-item>
        <el-descriptions-item label="供应商ID">{{ currentPO.supplier_id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="poTagType(currentPO.status)" size="small">{{ poStatusMap[currentPO.status] }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="总金额">¥{{ formatAmount(currentPO.total_amount) }}</el-descriptions-item>
        <el-descriptions-item label="物流单号">{{ currentPO.tracking_number || '-' }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatTime(currentPO.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="关联订单" :span="2">
          <el-tag v-for="id in currentPO.linked_order_ids" :key="id" size="small" class="order-tag">{{ id }}</el-tag>
          <span v-if="!currentPO.linked_order_ids?.length">-</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 物流轨迹弹窗 -->
    <el-dialog v-model="showLogisticsDialog" title="物流轨迹" width="600px">
      <el-timeline v-if="currentLogistics?.length">
        <el-timeline-item
          v-for="(event, index) in currentLogistics"
          :key="index"
          :timestamp="formatTime(event.time || event.timestamp)"
          placement="top"
        >
          <el-card shadow="never">
            <div class="logistics-event">
              <div class="event-desc">{{ event.description || event.status || event.event }}</div>
              <div class="event-location" v-if="event.location">{{ event.location }}</div>
            </div>
          </el-card>
        </el-timeline-item>
      </el-timeline>
      <el-empty v-else description="暂无物流轨迹信息" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { getPurchaseOrders, createPurchaseOrder, getShipments } from '@/api'

// ========== 状态映射 ==========
const poStatusMap: Record<string, string> = {
  pending: '待处理',
  ordered: '已下单',
  shipped: '已发货',
  received: '已收货',
  cancelled: '已取消',
}

const shipmentStatusMap: Record<string, string> = {
  pending: '待发货',
  in_transit: '运输中',
  delivered: '已送达',
  returned: '已退回',
  exception: '异常',
}

function poTagType(status: string): string {
  const map: Record<string, string> = { pending: 'info', ordered: 'primary', shipped: 'warning', received: 'success', cancelled: 'danger' }
  return map[status] || 'info'
}

function shipmentTagType(status: string): string {
  const map: Record<string, string> = { pending: 'info', in_transit: 'primary', delivered: 'success', returned: 'warning', exception: 'danger' }
  return map[status] || 'info'
}

// ========== 工具函数 ==========
function formatAmount(val: number | string | undefined): string {
  if (val === undefined || val === null) return '0.00'
  return Number(val).toFixed(2)
}

function formatTime(val: string | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return val
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ========== Tab切换 ==========
const activeTab = ref('purchase')

function handleTabChange(tab: string) {
  if (tab === 'purchase') fetchPurchaseOrders()
  else fetchShipments()
}

// ========== 采购管理 ==========
const poLoading = ref(false)
const purchaseOrders = ref<any[]>([])
const poPage = ref(1)
const poPageSize = ref(10)
const poTotal = ref(0)
const poFilter = reactive({ status: '' })

async function fetchPurchaseOrders() {
  poLoading.value = true
  try {
    const params: Record<string, unknown> = { page: poPage.value, page_size: poPageSize.value }
    if (poFilter.status) params.status = poFilter.status
    const res = await getPurchaseOrders(params)
    const data = res.data || res
    purchaseOrders.value = data.items || data.results || data.list || data.data || []
    poTotal.value = data.total || data.count || 0
  } catch (e: any) {
    ElMessage.error(e?.message || '获取采购单列表失败')
  } finally {
    poLoading.value = false
  }
}

// 新建采购单
const showCreateDialog = ref(false)
const createLoading = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = reactive({ supplier_id: '', linked_order_ids: '', remark: '' })
const createRules: FormRules = {
  supplier_id: [{ required: true, message: '请输入供应商ID', trigger: 'blur' }],
}

async function handleCreatePO() {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) return
  createLoading.value = true
  try {
    const data: Record<string, unknown> = { supplier_id: createForm.supplier_id }
    if (createForm.linked_order_ids.trim()) {
      data.linked_order_ids = createForm.linked_order_ids.split(',').map((s: string) => s.trim()).filter(Boolean)
    }
    if (createForm.remark.trim()) data.remark = createForm.remark.trim()
    await createPurchaseOrder(data)
    ElMessage.success('采购单创建成功')
    showCreateDialog.value = false
    createForm.supplier_id = ''
    createForm.linked_order_ids = ''
    createForm.remark = ''
    fetchPurchaseOrders()
  } catch (e: any) {
    ElMessage.error(e?.message || '创建采购单失败')
  } finally {
    createLoading.value = false
  }
}

// 采购单详情
const showDetailDialog = ref(false)
const currentPO = ref<any>(null)
function viewPurchaseDetail(row: any) {
  currentPO.value = row
  showDetailDialog.value = true
}

// ========== 物流管理 ==========
const shipmentLoading = ref(false)
const shipments = ref<any[]>([])
const shipmentPage = ref(1)
const shipmentPageSize = ref(10)
const shipmentTotal = ref(0)

async function fetchShipments() {
  shipmentLoading.value = true
  try {
    const res = await getShipments({ page: shipmentPage.value, page_size: shipmentPageSize.value })
    const data = res.data || res
    shipments.value = data.items || data.results || data.list || data.data || []
    shipmentTotal.value = data.total || data.count || 0
  } catch (e: any) {
    ElMessage.error(e?.message || '获取发货单列表失败')
  } finally {
    shipmentLoading.value = false
  }
}

// 物流轨迹
const showLogisticsDialog = ref(false)
const currentLogistics = ref<any[]>([])
function viewLogistics(row: any) {
  currentLogistics.value = row.logistics_events || []
  showLogisticsDialog.value = true
}

// ========== 初始化 ==========
onMounted(() => {
  fetchPurchaseOrders()
  fetchShipments()
})
</script>

<style scoped>
.fulfillment-container { padding: 20px; }
.page-title { margin: 0 0 16px; font-size: 22px; color: #303133; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.toolbar-left { display: flex; gap: 12px; }
.order-tag { margin: 2px 4px 2px 0; }
.pagination-wrap { display: flex; justify-content: flex-end; margin-top: 16px; }
.logistics-event { padding: 4px 0; }
.event-desc { font-size: 14px; color: #303133; }
.event-location { font-size: 12px; color: #909399; margin-top: 4px; }
</style>
