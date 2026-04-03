<template>
  <div class="products-container">
    <!-- 页面标题栏 -->
    <div class="page-header">
      <h2>商品管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>新建商品
      </el-button>
    </div>

    <!-- 搜索筛选栏 -->
    <el-card shadow="hover" class="filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :xs="24" :sm="8" :md="6">
          <el-input
            v-model="filters.keyword"
            placeholder="搜索商品名称..."
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

    <!-- 商品列表 -->
    <el-card shadow="hover" class="table-card">
      <el-table
        v-loading="loading"
        :data="tableData"
        stripe
        style="width: 100%"
        row-key="id"
      >
        <el-table-column prop="name" label="商品名称" min-width="160" show-overflow-tooltip />
        <el-table-column prop="cost_price" label="成本价" width="120" align="right">
          <template #default="{ row }">
            ¥{{ formatMoney(row.cost_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="sale_price" label="售价" width="120" align="right">
          <template #default="{ row }">
            ¥{{ formatMoney(row.sale_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="140">
          <template #default="{ row }">
            <el-tag :type="statusTagMap[row.status] || 'info'" size="small">
              {{ statusMap[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="score" label="评分" width="80" align="center">
          <template #default="{ row }">
            {{ row.score ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-popconfirm
              title="确定删除该商品吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
            <el-button
              v-if="row.status === 'listed'"
              type="warning"
              link
              size="small"
              @click="handleToggleListing(row, 'delisted')"
            >
              下架
            </el-button>
            <el-button
              v-else-if="row.status === 'active' || row.status === 'delisted'"
              type="success"
              link
              size="small"
              @click="handleToggleListing(row, 'listed')"
            >
              上架
            </el-button>
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
          @size-change="fetchProducts"
          @current-change="fetchProducts"
        />
      </div>
    </el-card>

    <!-- 新建/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑商品' : '新建商品'"
      width="560px"
      destroy-on-close
      @closed="resetForm"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="80px"
        label-position="right"
      >
        <el-form-item label="商品名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入商品名称" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            placeholder="请输入商品描述"
            :rows="3"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="成本价" prop="cost_price">
              <el-input-number v-model="formData.cost_price" :min="0" :precision="2" :controls="false" style="width: 100%" placeholder="0.00" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="售价" prop="sale_price">
              <el-input-number v-model="formData.sale_price" :min="0" :precision="2" :controls="false" style="width: 100%" placeholder="0.00" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="状态" prop="status">
          <el-select v-model="formData.status" placeholder="请选择状态" style="width: 100%">
            <el-option v-for="(label, key) in statusMap" :key="key" :label="label" :value="key" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { getProducts, createProduct, updateProduct } from '@/api'

// ========== 状态映射 ==========
const statusMap: Record<string, string> = {
  draft: '草稿',
  active: '在售',
  inactive: '已下架',
  listed: '已上架(TikTok)',
  delisted: '已下架(TikTok)',
}

const statusTagMap: Record<string, string> = {
  draft: 'info',
  active: 'success',
  inactive: 'danger',
  listed: 'primary',
  delisted: 'warning',
}

// ========== 筛选条件 ==========
const filters = reactive({
  keyword: '',
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

// ========== 弹窗相关 ==========
const dialogVisible = ref(false)
const isEditing = ref(false)
const editingId = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()

interface ProductForm {
  name: string
  description: string
  cost_price: number | undefined
  sale_price: number | undefined
  status: string
}

const formData = reactive<ProductForm>({
  name: '',
  description: '',
  cost_price: undefined,
  sale_price: undefined,
  status: 'draft',
})

const formRules: FormRules = {
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  sale_price: [{ required: true, message: '请输入售价', trigger: 'blur' }],
}

// ========== 方法 ==========

/** 金额格式化：保留2位小数 */
function formatMoney(value: number | undefined): string {
  if (value === undefined || value === null) return '0.00'
  return Number(value).toFixed(2)
}

/** 时间格式化：YYYY-MM-DD HH:mm */
function formatTime(value: string | undefined): string {
  if (!value) return '-'
  const d = new Date(value)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

/** 加载商品列表 */
async function fetchProducts() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      page_size: pagination.pageSize,
    }
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.status) params.status = filters.status

    const res: any = await getProducts(params)
    tableData.value = res.items || res.data || []
    pagination.total = res.total || 0
  } catch (err: any) {
    ElMessage.error('加载商品列表失败')
  } finally {
    loading.value = false
  }
}

/** 搜索 */
function handleSearch() {
  pagination.page = 1
  fetchProducts()
}

/** 重置筛选 */
function handleReset() {
  filters.keyword = ''
  filters.status = ''
  pagination.page = 1
  fetchProducts()
}

/** 新建商品 */
function handleCreate() {
  isEditing.value = false
  editingId.value = ''
  dialogVisible.value = true
}

/** 编辑商品 */
function handleEdit(row: any) {
  isEditing.value = true
  editingId.value = row.id
  Object.assign(formData, {
    name: row.name || '',
    description: row.description || '',
    cost_price: row.cost_price ?? undefined,
    sale_price: row.sale_price ?? undefined,
    status: row.status || 'draft',
  })
  dialogVisible.value = true
}

/** 删除商品 */
async function handleDelete(row: any) {
  try {
    await updateProduct(row.id, { status: 'inactive' } as any)
    ElMessage.success('商品已删除')
    fetchProducts()
  } catch (err: any) {
    ElMessage.error('删除失败')
  }
}

/** 上架/下架切换 */
async function handleToggleListing(row: any, newStatus: string) {
  try {
    await updateProduct(row.id, { status: newStatus } as any)
    ElMessage.success(newStatus === 'listed' ? '已上架' : '已下架')
    fetchProducts()
  } catch (err: any) {
    ElMessage.error('操作失败')
  }
}

/** 重置表单 */
function resetForm() {
  formRef.value?.resetFields()
  Object.assign(formData, {
    name: '',
    description: '',
    cost_price: undefined,
    sale_price: undefined,
    status: 'draft',
  })
}

/** 提交表单 */
async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload: Record<string, unknown> = {
      name: formData.name,
      description: formData.description,
      cost_price: formData.cost_price,
      sale_price: formData.sale_price,
      status: formData.status,
    }
    if (isEditing.value) {
      await updateProduct(editingId.value, payload)
      ElMessage.success('编辑成功')
    } else {
      await createProduct(payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    fetchProducts()
  } catch (err: any) {
    ElMessage.error(isEditing.value ? '编辑失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

// ========== 生命周期 ==========
onMounted(() => {
  fetchProducts()
})
</script>

<style scoped>
.products-container {
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
</style>
