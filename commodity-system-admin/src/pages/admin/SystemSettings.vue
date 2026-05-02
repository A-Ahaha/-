<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getSystemConfig, getSystemLogs, testSystemNotify, updateSystemConfig } from '@/api/admin'
import type { SystemConfig, SystemLogItem } from '@/types/system'

const saving = ref(false)
const loading = ref(true)
const logLoading = ref(true)

const form = reactive<SystemConfig>({
  collectFrequencyMinutes: 30,
  collectEnabled: false,
  collectItemUrl: '',
  collectSku: '',
  collectProductName: '',
  collectIsCompetitor: false,
  collectClearExisting: false,
  collectIncludeAlerts: false,
  collectMaxPages: 20,
  alertThreshold: 80,
  emailEnabled: false,
  emailTo: '',
  smtpHost: '',
  smtpPort: 465,
  smtpUser: '',
  smtpPassword: '',
  smtpUseSsl: true,
  webhookEnabled: false,
  webhookUrl: '',
})
const testingNotify = ref(false)

const logs = ref<SystemLogItem[]>([])
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

function fmt(iso: string) {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(
    d.getSeconds(),
  )}`
}

async function loadConfig() {
  loading.value = true
  try {
    const c = await getSystemConfig()
    form.collectFrequencyMinutes = c.collectFrequencyMinutes
    form.collectEnabled = c.collectEnabled
    form.collectItemUrl = c.collectItemUrl
    form.collectSku = c.collectSku
    form.collectProductName = c.collectProductName
    form.collectIsCompetitor = c.collectIsCompetitor
    form.collectClearExisting = c.collectClearExisting
    form.collectIncludeAlerts = c.collectIncludeAlerts
    form.collectMaxPages = c.collectMaxPages
    form.alertThreshold = c.alertThreshold
    form.emailEnabled = c.emailEnabled
    form.emailTo = c.emailTo
    form.smtpHost = c.smtpHost
    form.smtpPort = c.smtpPort
    form.smtpUser = c.smtpUser
    form.smtpPassword = c.smtpPassword
    form.smtpUseSsl = c.smtpUseSsl
    form.webhookEnabled = c.webhookEnabled
    form.webhookUrl = c.webhookUrl
  } catch (e) {
    const message = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

async function onTestNotify() {
  testingNotify.value = true
  try {
    const res = await testSystemNotify()
    ElMessage.success(`测试完成：email=${res.email || 'skip'}, webhook=${res.webhook || 'skip'}`)
  } catch (e) {
    const message = e instanceof Error ? e.message : '测试失败'
    ElMessage.error(message)
  } finally {
    testingNotify.value = false
  }
}

async function loadLogs() {
  logLoading.value = true
  try {
    const res = await getSystemLogs({ page: page.value, pageSize: pageSize.value })
    logs.value = res.list
    total.value = res.total
  } catch (e) {
    const message = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(message)
  } finally {
    logLoading.value = false
  }
}

async function onSave() {
  if (saving.value) return
  try {
    saving.value = true
    await updateSystemConfig({ ...form })
    ElMessage.success('保存成功，已立即生效')
    await loadLogs()
  } catch (e) {
    const message = e instanceof Error ? e.message : '保存失败'
    ElMessage.error(message)
  } finally {
    saving.value = false
  }
}

function onPageChange(p: number) {
  page.value = p
  loadLogs()
}

function onPageSizeChange(s: number) {
  pageSize.value = s
  page.value = 1
  loadLogs()
}

onMounted(async () => {
  await Promise.all([loadConfig(), loadLogs()])
})
</script>

<template>
  <div class="grid">
    <div class="app-card">
      <div class="app-toolbar">
        <div>
          <div class="app-title">系统设置</div>
          <div class="app-subtitle">采集频率、预警阈值等系统参数</div>
        </div>
        <div class="tools">
          <el-button :loading="testingNotify" type="warning" plain @click="onTestNotify">测试通知</el-button>
          <el-button :loading="loading" @click="loadConfig">刷新</el-button>
          <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
        </div>
      </div>

      <div class="app-section">
        <el-skeleton :rows="6" animated :loading="loading">
          <template #default>
            <div class="form">
              <div class="field">
                <div class="label">数据采集频率（分钟）</div>
                <el-input-number v-model="form.collectFrequencyMinutes" :min="1" :max="720" />
                <div class="hint">数值越小，采集越频繁；建议 15-60 分钟。</div>
              </div>

              <div class="field">
                <div class="label">定时采集</div>
                <div class="inline"><el-switch v-model="form.collectEnabled" /> <span>启用京东定时采集</span></div>
                <el-input v-model="form.collectItemUrl" placeholder="京东商品链接，例如 https://item.jd.com/xxxxxxxx.html" />
                <div class="inline-grid">
                  <el-input v-model="form.collectSku" placeholder="采集后写入的型号级 SKU（不要填规格）" />
                  <el-input-number v-model="form.collectMaxPages" :min="1" :max="200" />
                </div>
                <el-input v-model="form.collectProductName" placeholder="可选：商品名称，不填则运行时自动提取" />
                <div class="inline"><el-switch v-model="form.collectIsCompetitor" /> <span>按竞品写入</span></div>
                <div class="inline"><el-switch v-model="form.collectClearExisting" /> <span>采集前清空该 SKU 历史评论</span></div>
                <div class="inline"><el-switch v-model="form.collectIncludeAlerts" /> <span>采集完成后触发告警</span></div>
                <div class="hint">开启后，系统会按“采集频率”自动执行京东评论采集。保存后立即生效。</div>
              </div>

              <div class="field">
                <div class="label">预警阈值（1-100）</div>
                <el-slider v-model="form.alertThreshold" :min="1" :max="100" show-input />
                <div class="hint">阈值越低，预警更敏感；阈值越高，预警更保守。</div>
              </div>

              <div class="field">
                <div class="label">邮件通知</div>
                <div class="inline"><el-switch v-model="form.emailEnabled" /> <span>启用 SMTP 邮件</span></div>
                <el-input v-model="form.emailTo" placeholder="收件人邮箱，例如 qa@example.com" />
                <div class="inline-grid">
                  <el-input v-model="form.smtpHost" placeholder="SMTP Host" />
                  <el-input-number v-model="form.smtpPort" :min="1" :max="65535" />
                </div>
                <div class="inline-grid">
                  <el-input v-model="form.smtpUser" placeholder="SMTP 用户名" />
                  <el-input v-model="form.smtpPassword" show-password placeholder="SMTP 密码/授权码" />
                </div>
                <div class="inline"><el-switch v-model="form.smtpUseSsl" /> <span>使用 SSL</span></div>
              </div>

              <div class="field">
                <div class="label">Webhook 通知</div>
                <div class="inline"><el-switch v-model="form.webhookEnabled" /> <span>启用 Webhook</span></div>
                <el-input v-model="form.webhookUrl" placeholder="https://your-webhook-endpoint" />
              </div>
            </div>
          </template>
        </el-skeleton>
      </div>
    </div>

    <div class="app-card">
      <div class="app-toolbar">
        <div>
          <div class="app-title">系统日志</div>
          <div class="app-subtitle">支持分页查看</div>
        </div>
        <el-button :loading="logLoading" @click="loadLogs">刷新</el-button>
      </div>

      <div class="app-section">
        <el-table v-loading="logLoading" :data="logs" style="width: 100%" height="420">
          <el-table-column label="时间" min-width="190">
            <template #default="{ row }">{{ fmt(row.createdAt) }}</template>
          </el-table-column>
          <el-table-column prop="level" label="级别" width="110" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.level === 'error'" type="danger" effect="dark">error</el-tag>
              <el-tag v-else-if="row.level === 'warn'" type="warning" effect="dark">warn</el-tag>
              <el-tag v-else type="info" effect="dark">info</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="内容" min-width="260" />
        </el-table>

        <div class="pager">
          <el-pagination
            :current-page="page"
            :page-size="pageSize"
            :total="total"
            layout="total, sizes, prev, pager, next"
            :page-sizes="[10, 20, 50]"
            @update:current-page="onPageChange"
            @update:page-size="onPageSizeChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.tools {
  display: flex;
  gap: 10px;
  align-items: center;
}

.form {
  display: grid;
  gap: 18px;
}

.field {
  border: 1px solid rgba(17, 24, 39, 0.1);
  border-radius: 14px;
  padding: 14px;
  background: rgba(255, 255, 255, 0.75);
}

.label {
  font-weight: 800;
  margin-bottom: 10px;
}

.hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--app-text-dim);
}

.inline {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 13px;
}

.inline-grid {
  display: grid;
  grid-template-columns: 1fr 160px;
  gap: 10px;
  margin-bottom: 10px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
}
</style>
