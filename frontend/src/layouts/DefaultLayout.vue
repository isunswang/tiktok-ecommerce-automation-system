<template>
  <el-container class="layout-container">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="layout-aside">
      <div class="logo-container">
        <span v-show="!isCollapse" class="logo-text">TikTok运营</span>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="true"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
        class="aside-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        <el-menu-item index="/products">
          <el-icon><Goods /></el-icon>
          <template #title>商品管理</template>
        </el-menu-item>
        <el-menu-item index="/orders">
          <el-icon><List /></el-icon>
          <template #title>订单管理</template>
        </el-menu-item>
        <el-menu-item index="/fulfillment">
          <el-icon><Van /></el-icon>
          <template #title>履约管理</template>
        </el-menu-item>
        <el-menu-item index="/customer-service">
          <el-icon><Service /></el-icon>
          <template #title>客服管理</template>
        </el-menu-item>
        <el-menu-item index="/finance">
          <el-icon><Wallet /></el-icon>
          <template #title>财务管理</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="main-container">
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Expand v-if="isCollapse" />
            <Fold v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentRoute.meta?.title">
              {{ currentRoute.meta.title as string }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" class="user-avatar">
                {{ (userStore.userInfo?.nickname || '管')[0] }}
              </el-avatar>
              <span class="user-name">{{ userStore.userInfo?.nickname || '管理员' }}</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="layout-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  DataBoard, Goods, List, Van, Service, Wallet,
  Expand, Fold, ArrowDown, SwitchButton,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()
const isCollapse = ref(false)

const currentRoute = computed(() => route)
const activeMenu = computed(() => route.path)

async function handleCommand(command: string) {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning',
      })
      await userStore.logout()
      ElMessage.success('已退出登录')
    } catch {
      // cancelled
    }
  }
}
</script>

<style scoped>
.layout-container { height: 100vh; overflow: hidden; }
.layout-aside { background-color: #304156; transition: width 0.3s ease; overflow: hidden; }
.logo-container { height: 60px; display: flex; align-items: center; justify-content: center; padding: 0 16px; background-color: #263445; overflow: hidden; white-space: nowrap; }
.logo-text { font-size: 16px; font-weight: 700; color: #fff; }
.aside-menu { border-right: none; height: calc(100vh - 60px); overflow-y: auto; }
.aside-menu:not(.el-menu--collapse) { width: 220px; }
.main-container { display: flex; flex-direction: column; overflow: hidden; }
.layout-header { display: flex; align-items: center; justify-content: space-between; height: 60px; padding: 0 20px; background: #fff; border-bottom: 1px solid #e6e6e6; box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08); }
.header-left { display: flex; align-items: center; gap: 16px; }
.collapse-btn { font-size: 20px; cursor: pointer; color: #606266; transition: color 0.3s; }
.collapse-btn:hover { color: #409EFF; }
.header-right { display: flex; align-items: center; }
.user-info { display: flex; align-items: center; gap: 8px; cursor: pointer; color: #606266; }
.user-info:hover { color: #409EFF; }
.user-avatar { background-color: #409EFF; color: #fff; font-size: 14px; }
.user-name { font-size: 14px; }
.layout-main { background: #f0f2f5; padding: 0; overflow-y: auto; }
</style>
