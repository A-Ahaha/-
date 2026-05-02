<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  collectJdComments,
  createProduct,
  deleteProduct,
  getCollectJobs,
  getProducts,
  importCsvUpload,
  rebuildAbsa,
  type CollectJobItem,
  type PagedProducts,
  type ProductRecord,
} from '@/api/admin'

const loading = ref(true)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const list = ref<ProductRecord[]>([])
const rebuildBusy = ref(false)
const jobLoading = ref(false)
const collectJobs = ref<CollectJobItem[]>([])
const jobPage = ref(1)
const jobPageSize = ref(8)
const jobTotal = ref(0)

const dialogOpen = ref(false)
const formRef = ref()
const form = reactive({
  sku: '',
  name: '',
  platform: '',
  isCompetitor: false,
})

const importDialogOpen = ref(false)
const importLoading = ref(false)
const importUploadRef = ref()
const importForm = reactive({
  sku: '',
  productName: '',
  isCompetitor: false,
  clearExisting: true,
  /** 关闭时导入很快；开启则逐条 Transformer，仅大数据量且要精度时用 */
  useTransformer: false,
  file: null as File | null,
})

const collectDialogOpen = ref(false)
const collectLoading = ref(false)
const collectForm = reactive({
  itemUrl: '',
  sku: '',
  productName: '',
  isCompetitor: false,
  clearExisting: true,
  includeAlerts: false,
  maxPages: 20,
})

async function load() {
  loading.value = true
  try {
    const res: PagedProducts = await getProducts({ page: page.value, pageSize: pageSize.value })
    list.value = res.list
    total.value = res.total
  } catch (e) {
    const message = e instanceof Error ? e.message : '加载失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

async function loadJobs() {
  jobLoading.value = true
  try {
    const res = await getCollectJobs({ page: jobPage.value, pageSize: jobPageSize.value })
    collectJobs.value = res.list
    jobTotal.value = res.total
  } catch (e) {
    const message = e instanceof Error ? e.message : '加载采集任务失败'
    ElMessage.error(message)
  } finally {
    jobLoading.value = false
  }
}

function openCreate() {
  dialogOpen.value = true
  form.sku = ''
  form.name = ''
  form.platform = ''
  form.isCompetitor = false
}

async function onSubmit() {
  try {
    await formRef.value?.validate?.()
    await createProduct({
      sku: form.sku,
      name: form.name,
      platform: form.platform || undefined,
      isCompetitor: form.isCompetitor,
    })
    ElMessage.success('创建成功')
    dialogOpen.value = false
    await load()
  } catch (e) {
    if (e) {
      const message = e instanceof Error ? e.message : '创建失败'
      ElMessage.error(message)
    }
  }
}

function openImport() {
  importDialogOpen.value = true
  importUploadRef.value?.clearFiles?.()
  importForm.sku = ''
  importForm.productName = ''
  importForm.isCompetitor = false
  importForm.clearExisting = true
  importForm.useTransformer = false
  importForm.file = null
}

function closeImportDialog() {
  importDialogOpen.value = false
  importUploadRef.value?.clearFiles?.()
  importForm.file = null
}

function openCollect() {
  collectDialogOpen.value = true
  collectForm.itemUrl = ''
  collectForm.sku = ''
  collectForm.productName = ''
  collectForm.isCompetitor = false
  collectForm.clearExisting = true
  collectForm.includeAlerts = false
  collectForm.maxPages = 20
}

function onFileChange(file: any) {
  importForm.file = file?.raw || null
}

function onFileExceed(files: any[]) {
  const picked = files?.[0]
  if (!picked) return
  importUploadRef.value?.clearFiles?.()
  importUploadRef.value?.handleStart?.(picked)
  importForm.file = picked.raw || picked
}

async function onSubmitImport() {
  if (!importForm.sku.trim()) {
    ElMessage.warning('请填写 SKU')
    return
  }
  if (!importForm.file) {
    ElMessage.warning('请上传 CSV 文件')
    return
  }
  importLoading.value = true
  try {
    const res = await importCsvUpload({
      sku: importForm.sku.trim(),
      productName: importForm.productName.trim() || importForm.sku.trim(),
      isCompetitor: importForm.isCompetitor,
      clearExisting: importForm.clearExisting,
      useTransformer: importForm.useTransformer,
      file: importForm.file,
    })
    ElMessage.success(`导入成功，写入 ${res.count} 条评论`)
    closeImportDialog()
    await load()
  } catch {
    // 失败提示由 request 拦截器 / request() 统一弹出，避免与超时等错误重复两条
  } finally {
    importLoading.value = false
  }
}

async function onSubmitCollect() {
  if (!collectForm.itemUrl.trim()) {
    ElMessage.warning('请填写商品链接')
    return
  }
  if (!collectForm.sku.trim()) {
    ElMessage.warning('请填写 SKU')
    return
  }
  collectLoading.value = true
  try {
    const res = await collectJdComments({
      itemUrl: collectForm.itemUrl.trim(),
      sku: collectForm.sku.trim(),
      productName: collectForm.productName.trim() || undefined,
      isCompetitor: collectForm.isCompetitor,
      clearExisting: collectForm.clearExisting,
      includeAlerts: collectForm.includeAlerts,
      maxPages: collectForm.maxPages,
    })
    ElMessage.success(`京东采集完成，导入 ${res.count} 条评论`)
    collectDialogOpen.value = false
    await Promise.all([load(), loadJobs()])
  } catch {
    // 错误提示由 request 层统一处理
  } finally {
    collectLoading.value = false
  }
}

function onPageChange(p: number) {
  page.value = p
  load()
}

function onJobPageChange(p: number) {
  jobPage.value = p
  loadJobs()
}

function fmtTime(iso?: string) {
  return iso?.replace('T', ' ').slice(0, 19) || '—'
}

async function onRebuild(row: ProductRecord, includeAlerts: boolean) {
  if (!row?.id) return
  try {
    if (includeAlerts) {
      await ElMessageBox.confirm(
        `将对商品 ${row.name} 执行“重建 ABSA 并触发告警”。这可能会发送邮件/Webhook，请确认后继续。`,
        '确认触发告警',
        {
          confirmButtonText: '确认',
          cancelButtonText: '取消',
          type: 'warning',
        },
      )
    }

    rebuildBusy.value = true
    const res = await rebuildAbsa({ productId: row.id, includeAlerts })
    ElMessage.success(`重建完成：productId=${res.productId}`)
    await load()
  } catch (e) {
    // ElMessageBox 取消会抛错，这里不额外提示，避免干扰用户
    if (e instanceof Error) {
      ElMessage.error(e.message)
    }
  } finally {
    rebuildBusy.value = false
  }
}

async function onDelete(row: ProductRecord) {
  if (!row?.id) return
  try {
    await ElMessageBox.confirm(`确认删除商品「${row.name}」(SKU: ${row.sku})？\n此操作会同时删除该商品的评论、问题聚合与告警数据，且不可恢复。`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteProduct({ productId: row.id })
    ElMessage.success('删除成功')
    // 若删除的是本页最后一条，尝试回退一页
    if (list.value.length <= 1 && page.value > 1) page.value -= 1
    await load()
  } catch (e) {
    // 取消不提示；错误由 request 层统一提示
    if (e instanceof Error && /cancel/i.test(e.message)) return
  }
}

onMounted(async () => {
  await Promise.all([load(), loadJobs()])
})
</script>

<template>
  <div class="app-card">
    <div class="app-toolbar">
      <div>
        <div class="app-title">商品管理</div>
        <div class="app-subtitle">SKU 建议使用“型号级唯一编码”；CSV 中“产品”字段用于规格/变体分析</div>
      </div>
      <div class="tools">
        <el-button type="primary" @click="openCreate">新增商品</el-button>
        <el-button type="warning" plain @click="openCollect">京东采集</el-button>
        <el-button type="success" plain @click="openImport">导入 CSV</el-button>
      </div>
    </div>

    <div class="app-section">
      <el-table v-loading="loading" :data="list" style="width: 100%" height="520">
        <el-table-column prop="sku" label="SKU" min-width="160" />
        <el-table-column prop="name" label="商品名称" min-width="220" />
        <el-table-column prop="platform" label="平台" width="120">
          <template #default="{ row }">
            {{ row.platform || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="类别" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.isCompetitor" type="warning" effect="light">竞品</el-tag>
            <el-tag v-else type="success" effect="light">主商品</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="200">
          <template #default="{ row }">
            {{ row.createdAt?.replace('T', ' ').slice(0, 19) || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="340" fixed="right">
          <template #default="{ row }">
            <div class="row-actions">
              <el-button size="small" type="primary" plain :loading="rebuildBusy" @click="onRebuild(row, false)">
                重建 ABSA
              </el-button>
              <el-button
                size="small"
                type="danger"
                plain
                :loading="rebuildBusy"
                @click="onRebuild(row, true)"
              >
                重建 + 告警
              </el-button>
              <el-button size="small" type="danger" plain @click="onDelete(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && total > pageSize" class="pager">
        <el-pagination
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="onPageChange"
        />
      </div>

      <div v-if="!loading && list.length === 0" class="empty">
        <el-empty description="暂无商品，请先新增一个需要监控的 SKU" />
      </div>
    </div>
  </div>

  <div class="app-card" style="margin-top: 14px">
    <div class="app-toolbar">
      <div>
        <div class="app-title">采集任务记录</div>
        <div class="app-subtitle">查看京东评论采集执行结果、导入数量与失败原因</div>
      </div>
      <el-button :loading="jobLoading" @click="loadJobs">刷新</el-button>
    </div>

    <div class="app-section">
      <el-table v-loading="jobLoading" :data="collectJobs" style="width: 100%" height="360">
        <el-table-column prop="platform" label="平台" width="90" />
        <el-table-column prop="sku" label="SKU" min-width="150" />
        <el-table-column prop="productName" label="商品名称" min-width="180" />
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.status === 'success'" type="success" effect="dark">success</el-tag>
            <el-tag v-else-if="row.status === 'failed'" type="danger" effect="dark">failed</el-tag>
            <el-tag v-else-if="row.status === 'running'" type="warning" effect="dark">running</el-tag>
            <el-tag v-else effect="plain">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="totalCollected" label="采集数" width="100" align="right" />
        <el-table-column prop="totalImported" label="导入数" width="100" align="right" />
        <el-table-column prop="errorMessage" label="错误信息" min-width="220" />
        <el-table-column label="开始时间" width="180">
          <template #default="{ row }">{{ fmtTime(row.startedAt) }}</template>
        </el-table-column>
        <el-table-column label="结束时间" width="180">
          <template #default="{ row }">{{ fmtTime(row.finishedAt) }}</template>
        </el-table-column>
      </el-table>

      <div v-if="!jobLoading && jobTotal > jobPageSize" class="pager">
        <el-pagination
          :current-page="jobPage"
          :page-size="jobPageSize"
          :total="jobTotal"
          layout="prev, pager, next"
          @current-change="onJobPageChange"
        />
      </div>
    </div>
  </div>

  <el-dialog v-model="dialogOpen" title="新增商品" width="520px">
    <el-form ref="formRef" :model="form" label-position="top" @submit.prevent>
      <el-form-item label="SKU" prop="sku" :rules="[{ required: true, message: '请输入 SKU', trigger: 'blur' }]">
        <el-input v-model="form.sku" placeholder="型号级 SKU（如 MATEPAD-11.5S）；不要填颜色容量规格" />
      </el-form-item>
      <el-form-item label="商品名称" prop="name" :rules="[{ required: true, message: '请输入商品名称', trigger: 'blur' }]">
        <el-input v-model="form.name" placeholder="用于在看板中展示的商品名称" />
      </el-form-item>
      <el-form-item label="平台" prop="platform">
        <el-input v-model="form.platform" placeholder="可选，例如：jd / tmall / self" />
      </el-form-item>
      <el-form-item label="是否竞品">
        <el-switch v-model="form.isCompetitor" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogOpen = false">取消</el-button>
      <el-button type="primary" @click="onSubmit">确认</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="importDialogOpen" title="CSV 导入评论" width="560px">
    <el-form :model="importForm" label-position="top">
      <el-form-item label="SKU">
        <el-input v-model="importForm.sku" placeholder="必填，型号级 SKU（如 MATEPAD-115S-MAIN）" />
      </el-form-item>
      <el-form-item label="商品名称">
        <el-input v-model="importForm.productName" placeholder="可选，展示名称；CSV 的“产品”字段将自动用于规格/变体" />
      </el-form-item>
      <el-form-item label="是否竞品">
        <el-switch v-model="importForm.isCompetitor" />
      </el-form-item>
      <el-form-item label="导入前清空该SKU历史评论">
        <el-switch v-model="importForm.clearExisting" />
      </el-form-item>
      <el-form-item label="导入时用 Transformer 深度分析（慢）">
        <el-switch v-model="importForm.useTransformer" />
        <div class="hint">默认关闭：只把 CSV 写入数据库并用规则+启发式算情感与议题，通常秒级完成。需要模型级精度可开启，或导入后在列表里点「重建 ABSA」。</div>
      </el-form-item>
      <el-form-item label="CSV 文件">
        <el-upload ref="importUploadRef" :auto-upload="false" :limit="1" accept=".csv" :on-change="onFileChange" :on-exceed="onFileExceed">
          <el-button>选择文件</el-button>
        </el-upload>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="closeImportDialog">取消</el-button>
      <el-button type="primary" :loading="importLoading" @click="onSubmitImport">开始导入</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="collectDialogOpen" title="京东评论采集" width="620px">
    <el-form :model="collectForm" label-position="top">
      <el-form-item label="商品链接">
        <el-input v-model="collectForm.itemUrl" placeholder="https://item.jd.com/xxxxxxxx.html" />
      </el-form-item>
      <el-form-item label="SKU">
        <el-input v-model="collectForm.sku" placeholder="必填，型号级 SKU（如 MATEPAD-115S-MAIN）" />
      </el-form-item>
      <el-form-item label="商品名称">
        <el-input v-model="collectForm.productName" placeholder="可选，不填则尝试从页面自动提取" />
      </el-form-item>
      <el-form-item label="最大页数">
        <el-input-number v-model="collectForm.maxPages" :min="1" :max="200" />
      </el-form-item>
      <el-form-item label="是否竞品">
        <el-switch v-model="collectForm.isCompetitor" />
      </el-form-item>
      <el-form-item label="采集前清空该 SKU 历史评论">
        <el-switch v-model="collectForm.clearExisting" />
      </el-form-item>
      <el-form-item label="采集完成后是否触发告警">
        <el-switch v-model="collectForm.includeAlerts" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="collectDialogOpen = false">取消</el-button>
      <el-button type="primary" :loading="collectLoading" @click="onSubmitCollect">开始采集</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.tools {
  display: flex;
  gap: 10px;
  align-items: center;
}

.row-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.pager {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.empty {
  padding: 24px 0 4px;
}

.hint {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.45;
  color: var(--el-text-color-secondary);
}
</style>

