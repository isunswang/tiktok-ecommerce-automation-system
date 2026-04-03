<template>
  <div class="cs-container">
    <h2 class="page-title">客服管理</h2>
    <el-container class="cs-layout">
      <!-- 左侧面板：会话列表 -->
      <el-aside width="350px" class="cs-aside">
        <div class="aside-header">
          <el-input v-model="searchKeyword" placeholder="搜索买家名称..." clearable :prefix-icon="Search" />
          <el-button type="primary" size="small" @click="showCreateSessionDialog = true" style="margin-top: 8px; width: 100%">
            <el-icon><Plus /></el-icon> 新建会话
          </el-button>
        </div>
        <div class="session-list" v-loading="sessionLoading">
          <div
            v-for="session in filteredSessions"
            :key="session.id"
            class="session-card"
            :class="{ active: currentSessionId === session.id }"
            @click="selectSession(session)"
          >
            <div class="session-header">
              <span class="session-name">{{ session.buyer_name || '未知买家' }}</span>
              <el-tag :type="sessionStatusType(session.status)" size="small">{{ sessionStatusMap[session.status] || session.status }}</el-tag>
            </div>
            <div class="session-preview">{{ session.last_message || '暂无消息' }}</div>
            <div class="session-footer">
              <span class="session-time">{{ formatTime(session.updated_at || session.created_at) }}</span>
              <span v-if="session.status === 'active'" class="active-dot"></span>
            </div>
          </div>
          <el-empty v-if="!sessionLoading && sessions.length === 0" description="暂无会话" />
        </div>
      </el-aside>

      <!-- 右侧面板：聊天窗口 -->
      <el-main class="cs-main">
        <!-- 未选中会话 -->
        <div v-if="!currentSession" class="no-session">
          <el-icon :size="48" color="#C0C4CC"><ChatDotRound /></el-icon>
          <p>请选择一个会话</p>
        </div>

        <!-- 已选中会话 -->
        <template v-else>
          <!-- 顶部信息栏 -->
          <div class="chat-header">
            <div class="chat-header-info">
              <span class="chat-buyer-name">{{ currentSession.buyer_name || '未知买家' }}</span>
              <el-tag :type="sessionStatusType(currentSession.status)" size="small">{{ sessionStatusMap[currentSession.status] }}</el-tag>
            </div>
            <div class="chat-header-actions">
              <el-button size="small" type="danger" plain @click="handleEndSession">结束会话</el-button>
              <el-button size="small" type="warning" plain @click="handleTransfer">转人工</el-button>
            </div>
          </div>

          <!-- 消息列表 -->
          <div class="message-list" ref="messageListRef">
            <div v-for="msg in messages" :key="msg.id || msg.timestamp" class="message-item" :class="msg.role">
              <div class="message-bubble" :class="msg.role">
                <div class="msg-role-tag">{{ roleLabel(msg.role) }}</div>
                <div class="msg-content">{{ msg.content }}</div>
                <div class="msg-time">{{ formatTime(msg.created_at || msg.timestamp) }}</div>
              </div>
            </div>
            <el-empty v-if="!messages.length" description="暂无消息" />
          </div>

          <!-- 底部输入区域 -->
          <div class="chat-input" v-if="currentSession.status === 'active'">
            <el-input
              v-model="newMessage"
              type="textarea"
              :rows="2"
              placeholder="输入消息..."
              @keydown.enter.ctrl="handleSendMessage"
            />
            <el-button type="primary" @click="handleSendMessage" :disabled="!newMessage.trim()">发送</el-button>
          </div>
          <div v-else class="chat-input disabled-input">
            <span style="color: #909399; font-size: 13px">会话已结束，无法发送消息</span>
          </div>
        </template>
      </el-main>
    </el-container>

    <!-- 新建会话弹窗 -->
    <el-dialog v-model="showCreateSessionDialog" title="新建会话" width="480px" destroy-on-close>
      <el-form ref="sessionFormRef" :model="sessionForm" :rules="sessionRules" label-width="80px">
        <el-form-item label="买家ID" prop="buyer_id">
          <el-input v-model="sessionForm.buyer_id" placeholder="请输入买家ID" />
        </el-form-item>
        <el-form-item label="买家名称" prop="buyer_name">
          <el-input v-model="sessionForm.buyer_name" placeholder="请输入买家名称" />
        </el-form-item>
        <el-form-item label="订单ID">
          <el-input v-model="sessionForm.order_id" placeholder="关联订单ID（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateSessionDialog = false">取消</el-button>
        <el-button type="primary" :loading="createSessionLoading" @click="handleCreateSession">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, ChatDotRound } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { getCsSessions, getCsSession, sendCsMessage, createCsSession, endCsSession, transferCsSession } from '@/api'

// ========== 状态映射 ==========
const sessionStatusMap: Record<string, string> = {
  active: '进行中',
  closed: '已结束',
  escalated: '待人工',
}

function sessionStatusType(status: string): string {
  const map: Record<string, string> = { active: 'cyan', closed: 'info', escalated: 'danger' }
  return map[status] || 'info'
}

function roleLabel(role: string): string {
  const map: Record<string, string> = { buyer: '买家', ai: 'AI助手', agent: '人工客服' }
  return map[role] || role
}

// ========== 工具函数 ==========
function formatTime(val: string | undefined): string {
  if (!val) return '-'
  const d = new Date(val)
  if (isNaN(d.getTime())) return val
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ========== 会话列表 ==========
const sessionLoading = ref(false)
const sessions = ref<any[]>([])
const searchKeyword = ref('')
const currentSessionId = ref('')

const filteredSessions = computed(() => {
  if (!searchKeyword.value.trim()) return sessions.value
  const kw = searchKeyword.value.trim().toLowerCase()
  return sessions.value.filter((s: any) => (s.buyer_name || '').toLowerCase().includes(kw))
})

async function fetchSessions() {
  sessionLoading.value = true
  try {
    const res = await getCsSessions()
    const data = res.data || res
    sessions.value = data.items || data.results || data.list || data.data || []
  } catch (e: any) {
    ElMessage.error(e?.message || '获取会话列表失败')
  } finally {
    sessionLoading.value = false
  }
}

// ========== 当前会话与消息 ==========
const currentSession = ref<any>(null)
const messages = ref<any[]>([])
const messageListRef = ref<HTMLElement>()

async function selectSession(session: any) {
  currentSessionId.value = session.id
  currentSession.value = session
  try {
    const res = await getCsSession(session.id)
    const data = res.data || res
    messages.value = data.messages || data.message_list || []
  } catch (e: any) {
    ElMessage.error(e?.message || '获取会话详情失败')
  }
  await nextTick()
  scrollToBottom()
}

function scrollToBottom() {
  if (messageListRef.value) {
    messageListRef.value.scrollTop = messageListRef.value.scrollHeight
  }
}

// ========== 发送消息 ==========
const newMessage = ref('')
const sendingMessage = ref(false)

async function handleSendMessage() {
  const content = newMessage.value.trim()
  if (!content || !currentSession.value) return
  sendingMessage.value = true
  try {
    await sendCsMessage({ session_id: currentSession.value.id, content, role: 'agent' })
    messages.value.push({
      id: Date.now().toString(),
      session_id: currentSession.value.id,
      role: 'agent',
      content,
      created_at: new Date().toISOString(),
    })
    newMessage.value = ''
    await nextTick()
    scrollToBottom()
  } catch (e: any) {
    ElMessage.error(e?.message || '发送消息失败')
  } finally {
    sendingMessage.value = false
  }
}

// ========== 结束会话 ==========
async function handleEndSession() {
  if (!currentSession.value) return
  try {
    await ElMessageBox.confirm('确定要结束此会话吗？', '提示', { type: 'warning' })
    await endCsSession(currentSession.value.id)
    ElMessage.success('会话已结束')
    currentSession.value.status = 'closed'
    fetchSessions()
  } catch {
    // 用户取消
  }
}

// ========== 转人工 ==========
async function handleTransfer() {
  if (!currentSession.value) return
  try {
    const { value: reason } = await ElMessageBox.prompt('请输入转人工原因', '转人工', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: '请输入原因...',
      inputValidator: (val: string) => (val && val.trim() ? true : '请输入转人工原因'),
    })
    await transferCsSession(currentSession.value.id, reason)
    ElMessage.success('已转人工处理')
    currentSession.value.status = 'escalated'
    fetchSessions()
  } catch {
    // 用户取消
  }
}

// ========== 新建会话 ==========
const showCreateSessionDialog = ref(false)
const createSessionLoading = ref(false)
const sessionFormRef = ref<FormInstance>()
const sessionForm = reactive({ buyer_id: '', buyer_name: '', order_id: '' })
const sessionRules: FormRules = {
  buyer_id: [{ required: true, message: '请输入买家ID', trigger: 'blur' }],
  buyer_name: [{ required: true, message: '请输入买家名称', trigger: 'blur' }],
}

async function handleCreateSession() {
  const valid = await sessionFormRef.value?.validate().catch(() => false)
  if (!valid) return
  createSessionLoading.value = true
  try {
    const data: Record<string, unknown> = { buyer_id: sessionForm.buyer_id, buyer_name: sessionForm.buyer_name }
    if (sessionForm.order_id.trim()) data.order_id = sessionForm.order_id.trim()
    const res = await createCsSession(data)
    const session = res.data || res
    ElMessage.success('会话创建成功')
    showCreateSessionDialog.value = false
    sessionForm.buyer_id = ''
    sessionForm.buyer_name = ''
    sessionForm.order_id = ''
    fetchSessions()
    // 自动选中新创建的会话
    if (session?.id) {
      selectSession(session)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '创建会话失败')
  } finally {
    createSessionLoading.value = false
  }
}

// ========== 初始化 ==========
onMounted(() => {
  fetchSessions()
})
</script>

<style scoped>
.cs-container { padding: 20px; height: calc(100vh - 100px); display: flex; flex-direction: column; }
.page-title { margin: 0 0 16px; font-size: 22px; color: #303133; }
.cs-layout { flex: 1; border: 1px solid #E4E7ED; border-radius: 8px; overflow: hidden; }

/* 左侧面板 */
.cs-aside { border-right: 1px solid #E4E7ED; display: flex; flex-direction: column; background: #FAFAFA; }
.aside-header { padding: 12px; }
.session-list { flex: 1; overflow-y: auto; padding: 0 8px 12px; }
.session-card { padding: 12px; margin-bottom: 8px; background: #FFF; border-radius: 8px; cursor: pointer; transition: all 0.2s; border: 2px solid transparent; }
.session-card:hover { background: #F5F7FA; }
.session-card.active { border-color: #409EFF; background: #ECF5FF; }
.session-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.session-name { font-size: 14px; font-weight: 600; color: #303133; }
.session-preview { font-size: 12px; color: #909399; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.session-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }
.session-time { font-size: 11px; color: #C0C4CC; }
.active-dot { width: 8px; height: 8px; border-radius: 50%; background: #67C23A; display: inline-block; }

/* 右侧聊天面板 */
.cs-main { display: flex; flex-direction: column; padding: 0; background: #F5F7FA; }
.no-session { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; color: #C0C4CC; }

.chat-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #FFF; border-bottom: 1px solid #E4E7ED; }
.chat-header-info { display: flex; align-items: center; gap: 8px; }
.chat-buyer-name { font-size: 15px; font-weight: 600; color: #303133; }
.chat-header-actions { display: flex; gap: 8px; }

.message-list { flex: 1; overflow-y: auto; padding: 16px; }
.message-item { display: flex; margin-bottom: 12px; }
.message-item.buyer { justify-content: flex-start; }
.message-item.ai, .message-item.agent { justify-content: flex-end; }
.message-bubble { max-width: 70%; padding: 10px 14px; border-radius: 12px; }
.message-bubble.buyer { background: #F0F0F0; color: #303133; border-top-left-radius: 4px; }
.message-bubble.ai { background: #409EFF; color: #FFF; border-top-right-radius: 4px; }
.message-bubble.agent { background: #67C23A; color: #FFF; border-top-right-radius: 4px; }
.msg-role-tag { font-size: 11px; opacity: 0.8; margin-bottom: 4px; }
.msg-content { font-size: 14px; line-height: 1.5; word-break: break-word; }
.msg-time { font-size: 11px; opacity: 0.7; margin-top: 4px; text-align: right; }

.chat-input { display: flex; align-items: flex-end; gap: 8px; padding: 12px 16px; background: #FFF; border-top: 1px solid #E4E7ED; }
.chat-input .el-input { flex: 1; }
.disabled-input { display: flex; align-items: center; justify-content: center; padding: 12px 16px; background: #FFF; border-top: 1px solid #E4E7ED; min-height: 56px; }
</style>
