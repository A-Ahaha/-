<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { assignRole, createUser, deleteUser, getUsers, updateUser } from '@/api/admin'
import type { UserInfo, UserRole } from '@/types/user'

const loading = ref(true)
const keyword = ref('')
const list = ref<UserInfo[]>([])

const dialogOpen = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const formRef = ref()
const form = reactive({
  id: '',
  username: '',
  email: '',
  role: 'user' as UserRole,
  status: 'active' as UserInfo['status'],
})

const rules = computed(() => {
  if (dialogMode.value === 'edit') {
    return {
      email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
      status: [{ required: true, message: '请选择状态', trigger: 'change' }],
    }
  }
  return {
    username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
    email: [{ type: 'email', message: '邮箱格式不正确', trigger: 'blur' }],
    role: [{ required: true, message: '请选择角色', trigger: 'change' }],
    status: [{ required: true, message: '请选择状态', trigger: 'change' }],
  }
})

async function load() {
  loading.value = true
  try {
    list.value = await getUsers({ keyword: keyword.value })
  } catch (e) {
    const message = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

function openCreate() {
  dialogMode.value = 'create'
  dialogOpen.value = true
  form.id = ''
  form.username = ''
  form.email = ''
  form.role = 'user'
  form.status = 'active'
}

function openEdit(row: UserInfo) {
  dialogMode.value = 'edit'
  dialogOpen.value = true
  form.id = row.id
  form.username = row.username
  form.email = row.email ?? ''
  form.role = row.role
  form.status = row.status
}

async function onSubmit() {
  try {
    await formRef.value?.validate?.()
    if (dialogMode.value === 'create') {
      await createUser({
        username: form.username,
        email: form.email || undefined,
        role: form.role,
        status: form.status,
      })
      ElMessage.success('创建成功')
    } else {
      await updateUser({
        id: form.id,
        email: form.email || undefined,
        status: form.status,
      })
      ElMessage.success('保存成功')
    }
    dialogOpen.value = false
    await load()
  } catch (e) {
    if (e) {
      const message = e instanceof Error ? e.message : '操作失败'
      ElMessage.error(message)
    }
  }
}

async function onDelete(row: UserInfo) {
  try {
    await ElMessageBox.confirm(`确认删除用户“${row.username}”？删除后不可恢复。`, '确认删除', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await deleteUser({ id: row.id })
    ElMessage.success('删除成功')
    await load()
  } catch {
    return
  }
}

async function onRoleChange(row: UserInfo, next: UserRole) {
  const prev = row.role
  row.role = next
  try {
    await assignRole({ id: row.id, role: next })
    ElMessage.success('角色已更新')
  } catch (e) {
    row.role = prev
    const message = e instanceof Error ? e.message : '更新失败'
    ElMessage.error(message)
  }
}

function onRoleSelect(row: UserInfo, next: string | number | boolean) {
  onRoleChange(row, String(next) as UserRole)
}

onMounted(load)
</script>

<template>
  <div class="app-card">
    <div class="app-toolbar">
      <div>
        <div class="app-title">用户管理</div>
        <div class="app-subtitle">用户列表、新增/编辑/删除、分配角色（Mock）</div>
      </div>
      <div class="tools">
        <el-input v-model="keyword" style="width: 240px" placeholder="搜索用户名/邮箱" clearable @keyup.enter="load" />
        <el-button :loading="loading" @click="load">查询</el-button>
        <el-button type="primary" @click="openCreate">新增用户</el-button>
      </div>
    </div>

    <div class="app-section">
      <el-table v-loading="loading" :data="list" style="width: 100%" height="520">
        <el-table-column prop="username" label="用户名" min-width="160" />
        <el-table-column prop="email" label="邮箱" min-width="220">
          <template #default="{ row }">{{ row.email || '—' }}</template>
        </el-table-column>
        <el-table-column label="角色" width="150">
          <template #default="{ row }">
            <el-select :model-value="row.role" style="width: 120px" @update:model-value="onRoleSelect(row, $event as string)">
              <el-option label="user" value="user" />
              <el-option label="admin" value="admin" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'active'" type="success" effect="dark">正常</el-tag>
            <el-tag v-else type="warning" effect="dark">禁用</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="onDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && list.length === 0" class="empty">
        <el-empty description="暂无数据" />
      </div>
    </div>
  </div>

  <el-dialog v-model="dialogOpen" :title="dialogMode === 'create' ? '新增用户' : '编辑用户'" width="520px">
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent>
      <el-form-item v-if="dialogMode === 'create'" label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="必填" />
      </el-form-item>
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" placeholder="可选" />
      </el-form-item>
      <el-form-item v-if="dialogMode === 'create'" label="角色" prop="role">
        <el-select v-model="form.role" style="width: 100%">
          <el-option label="user" value="user" />
          <el-option label="admin" value="admin" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="form.status" style="width: 100%">
          <el-option label="正常" value="active" />
          <el-option label="禁用" value="disabled" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogOpen = false">取消</el-button>
      <el-button type="primary" @click="onSubmit">确认</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.tools {
  display: flex;
  gap: 10px;
  align-items: center;
}
.empty {
  padding: 24px 0 4px;
}
</style>
