<template>
  <div class="dashboard-page">
    <!-- 主要内容 -->
    <main class="dashboard-main">
      <div class="main-container">
        <!-- 欢迎区域 -->
        <section class="welcome-section">
          <div class="welcome-content">
            <div class="welcome-text">
              <h1>
                欢迎回来，{{ tokenStore.selectedToken?.name || "游戏玩家" }}！
              </h1>
              <p>今天是 {{ currentDate }}，继续您的游戏管理之旅吧</p>
            </div>
            <div class="welcome-actions">
              <n-button
                type="primary"
                size="large"
                @click="router.push('/admin/game-features')"
              >
                进入游戏功能
              </n-button>
              <n-button size="large" @click="handleManageTokens">
                管理Token
              </n-button>
            </div>
          </div>
        </section>

        <!-- 公告区 -->
        <section class="notice-section">
          <h2 class="section-title">公告</h2>

          <div class="important-notice-card" @click="showDomainNotice = true">
            <div class="important-notice-badge">重要通知</div>
            <p class="important-notice-title">
              服务器以及域名即将到期，需要更换！
            </p>
            <p>
              免费版网址将会变更，请尽快添加微信号：
              <strong class="wechat-highlight">FieYangu</strong>
              ，避免失联！
            </p>
            <p class="important-notice-tip">点击查看详情 / 一键复制微信号</p>
          </div>

          <div class="notice-card">
            <p>灵云脚本免费版将持续维护与更新，功能持续升级中。</p>
            <p>
              总域名：<strong>yanling.fun</strong><br />
              联系微信：<strong>FieYangu</strong>（付费版支持试用与购买，问题反馈、功能建议请联系）
            </p>
            <p>
              您的每一次付费购买，都是支持免费版持续更新和功能全面升级的最大动力。
            </p>
          </div>
        </section>

        <n-modal
          v-model:show="showDomainNotice"
          preset="card"
          :mask-closable="false"
          :closable="true"
          class="domain-notice-modal"
          style="width: 92%; max-width: 460px"
        >
          <template #header>
            <div class="domain-modal-header">
              <span class="domain-modal-badge">重要通知</span>
              <span>域名即将到期</span>
            </div>
          </template>

          <div class="domain-modal-body">
            <p class="domain-modal-lead">
              服务器以及域名即将到期，需要更换。
            </p>
            <p>免费版网址将会变更，请务必添加微信号，避免失联！</p>
            <div class="domain-modal-wechat">
              <span class="domain-modal-label">微信号</span>
              <strong class="wechat-highlight">FieYangu</strong>
            </div>
            <p class="domain-modal-hint">
              添加时请备注「脚本」，后续新地址与更新通知将通过微信同步。
            </p>
          </div>

          <template #footer>
            <div class="domain-modal-footer">
              <n-button @click="copyWechatId">复制微信号</n-button>
              <n-button type="error" @click="acknowledgeDomainNotice">
                我知道了
              </n-button>
            </div>
          </template>
        </n-modal>

        <!-- 快速操作 -->
        <section class="quick-actions-section">
          <h2 class="section-title">快速操作</h2>
          <div class="actions-grid">
            <div
              v-for="action in quickActions"
              :key="action.id"
              class="action-card"
              @click="handleQuickAction(action)"
            >
              <div class="action-icon">
                <component :is="action.icon" />
              </div>
              <div class="action-content">
                <h3>{{ action.title }}</h3>
                <p>{{ action.description }}</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import {
  Add,
  CheckmarkCircle,
  Cloud,
  Cube,
  GameController,
} from "@vicons/ionicons5";
import lz4 from "lz4js";
import { useMessage } from "naive-ui";
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import useIndexedDB from "@/hooks/useIndexedDB";
import { useTokenStore } from "@/stores/tokenStore";

const router = useRouter();
const message = useMessage();
const tokenStore = useTokenStore();
const { getArrayBuffer } = useIndexedDB();

const DOMAIN_NOTICE_KEY = "domain_expiry_notice_acked_v1";
const WECHAT_ID = "FieYangu";
const showDomainNotice = ref(false);

const copyWechatId = async () => {
  try {
    await navigator.clipboard.writeText(WECHAT_ID);
    message.success(`已复制微信号：${WECHAT_ID}`);
  } catch {
    message.info(`请手动添加微信号：${WECHAT_ID}`);
  }
};

const acknowledgeDomainNotice = () => {
  localStorage.setItem(DOMAIN_NOTICE_KEY, String(Date.now()));
  showDomainNotice.value = false;
};

// ============ BIN 格式转换 ============

function extractKey(bytes) {
  return (
    (((bytes[2] >> 6) & 1) << 7) |
    (((bytes[2] >> 4) & 1) << 6) |
    (((bytes[2] >> 2) & 1) << 5) |
    ((bytes[2] & 1) << 4) |
    (((bytes[3] >> 6) & 1) << 3) |
    (((bytes[3] >> 4) & 1) << 2) |
    (((bytes[3] >> 2) & 1) << 1) |
    (bytes[3] & 1)
  );
}

function encodeKey(bytes, r) {
  bytes[2] =
    (bytes[2] & 0b10101010) |
    (((r >> 7) & 1) << 6) |
    (((r >> 6) & 1) << 4) |
    (((r >> 5) & 1) << 2) |
    ((r >> 4) & 1);
  bytes[3] =
    (bytes[3] & 0b10101010) |
    (((r >> 3) & 1) << 6) |
    (((r >> 2) & 1) << 4) |
    (((r >> 1) & 1) << 2) |
    (r & 1);
}

function xDecrypt(buf) {
  const e = new Uint8Array(buf);
  const t = extractKey(e);
  const out = new Uint8Array(e);
  for (let n = out.length; --n >= 4;) out[n] ^= t;
  return out.subarray(4);
}

function lxEncrypt(plain) {
  const compressed = lz4.compress(plain);
  const out = new Uint8Array(compressed.length);
  out.set(compressed);
  const r = 2 + ~~(Math.random() * 248);
  for (let n = Math.min(out.length, 100); --n >= 0;) out[n] ^= r;
  out[0] = 112;
  out[1] = 108;
  encodeKey(out, r);
  return out;
}

function convertBinToLx(buf) {
  const e = new Uint8Array(buf);
  if (e.length > 4 && e[0] === 112 && e[1] === 108) return e;
  if (e.length > 4 && e[0] === 112 && e[1] === 120) {
    const plain = xDecrypt(e);
    return lxEncrypt(plain);
  }
  return e;
}

const openGame = async () => {
  const token = tokenStore.selectedToken;
  if (!token) {
    message.warning("请先选择一个Token");
    return;
  }
  const binData = await getArrayBuffer(token.id);
  if (!binData) {
    message.error("未找到该Token的BIN数据");
    return;
  }
  const converted = convertBinToLx(binData);
  const hex = Array.from(converted)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  localStorage.setItem(`bin_data_${token.id}`, hex);
  localStorage.setItem("current_bin_id", token.id);
  let binList = [];
  try {
    binList = JSON.parse(localStorage.getItem("bin_file_list") || "[]");
  } catch (e) {}
  if (!binList.find((i) => i.id === token.id)) {
    binList.push({
      id: token.id,
      name: token.name || "Token",
      byteLength: binData.byteLength,
      size: `${(binData.byteLength / 1024).toFixed(1)} KB`,
      order: binList.length,
    });
    localStorage.setItem("bin_file_list", JSON.stringify(binList));
  }
  router.push("/game");
};

// 响应式数据
// const recentActivities = ref([]);

// 计算属性
const currentDate = computed(() => {
  return new Date().toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  });
});

const quickActions = ref([
  {
    id: 1,
    icon: GameController,
    title: "打开游戏",
    description: "使用当前Token直接进入游戏",
    action: "open-game",
  },
  {
    id: 2,
    icon: Cube,
    title: "游戏功能",
    description: "访问所有游戏功能模块",
    action: "game-features",
  },
  {
    id: 3,
    icon: Add,
    title: "添加Token",
    description: "快速添加新的游戏Token",
    action: "add-token",
  },
  {
    id: 4,
    icon: CheckmarkCircle,
    title: "批量任务",
    description: "批量执行任务",
    action: "batch-daily-tasks",
  },
  {
    id: 5,
    icon: Cloud,
    title: "WebSocket测试",
    description: "测试WebSocket连接和游戏命令",
    action: "websocket-test",
  },
]);

const handleManageTokens = () => {
  // 降噪
  /* 当前Token状态:
    hasTokens: tokenStore.hasTokens,
    selectedToken: tokenStore.selectedToken?.name,
    tokenCount: tokenStore.gameTokens.length
  */

  try {
    router.push("/tokens");
    // 降噪
  } catch (error) {
    console.error("❌ 导航失败:", error);
    message.error("导航到Token管理页面失败");
  }
};

const handleQuickAction = (action) => {
  switch (action.action) {
    case "open-game":
      openGame();
      break;
    case "game-features":
      router.push("/admin/game-features");
      break;
    case "add-token":
      handleManageTokens();
      break;
    case "execute-tasks":
      router.push("/admin/game-features");
      break;
    case "websocket-test":
      router.push("/websocket-test");
      break;
    case "open-settings":
      router.push("/admin/profile");
      break;
    case "batch-daily-tasks":
      router.push("/admin/batch-daily-tasks");
      break;
  }
};

/*
const getActivityIcon = (type) => {
  switch (type) {
    case "success":
      return CheckmarkCircle;
    case "warning":
      return Time;
    case "info":
    default:
      return Cube;
  }
};

const formatTime = (timestamp) => {
  const diff = Date.now() - timestamp;
  const minutes = Math.floor(diff / (1000 * 60));
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days > 0) {
    return `${days}天前`;
  } else if (hours > 0) {
    return `${hours}小时前`;
  } else if (minutes > 0) {
    return `${minutes}分钟前`;
  } else {
    return "刚刚";
  }
};
*/

// 生命周期
onMounted(async () => {
  // 确保有Token
  if (!tokenStore.hasTokens) {
    router.push("/tokens");
    return;
  }

  // 初始化Token数据
  tokenStore.initTokenStore();

  // 域名到期重要通知：进入首页自动弹窗（关闭后当天内不再强弹）
  const ackedAt = Number(localStorage.getItem(DOMAIN_NOTICE_KEY) || 0);
  const oneDayMs = 24 * 60 * 60 * 1000;
  if (!ackedAt || Date.now() - ackedAt > oneDayMs) {
    showDomainNotice.value = true;
  }
});
</script>

<style scoped lang="scss">
.dashboard-page {
  min-height: 100vh;
  background: var(--bg-secondary);
}

// 主要内容
.dashboard-main {
  padding: var(--spacing-xl);
}

.main-container {
  max-width: 1400px;
  margin: 0 auto;
}

// 欢迎区域
.welcome-section {
  background: linear-gradient(
    135deg,
    var(--primary-color) 0%,
    var(--secondary-color) 100%
  );
  border-radius: var(--border-radius-xl);
  padding: var(--spacing-2xl);
  margin-bottom: var(--spacing-xl);
  color: white;
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--spacing-lg);
}

.welcome-text {
  h1 {
    font-size: var(--font-size-3xl);
    font-weight: var(--font-weight-bold);
    margin-bottom: var(--spacing-sm);
  }

  p {
    font-size: var(--font-size-lg);
    opacity: 0.9;
    margin: 0;
  }
}

.welcome-actions {
  display: flex;
  gap: var(--spacing-md);
}

// 统计区域
.stats-section {
  margin-bottom: var(--spacing-xl);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-lg);
}

.stat-card {
  background: var(--bg-primary);
  border-radius: var(--border-radius-large);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-light);
  transition: all var(--transition-normal);

  &:hover {
    box-shadow: var(--shadow-medium);
    transform: translateY(-2px);
  }
}

.stat-icon {
  width: 48px;
  height: 48px;
  margin-bottom: var(--spacing-md);

  :deep(svg) {
    width: 100%;
    height: 100%;
  }
}

.stat-number {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-xs);
}

.stat-label {
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-xs);
}

.stat-change {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);

  &.positive {
    color: var(--success-color);
  }

  &.negative {
    color: var(--error-color);
  }
}

// 快速操作区域
.quick-actions-section {
  margin-bottom: var(--spacing-xl);
}

.notice-section {
  margin-bottom: var(--spacing-xl);
}

.important-notice-card {
  position: relative;
  margin-bottom: var(--spacing-md);
  padding: calc(var(--spacing-lg) + 4px) var(--spacing-lg) var(--spacing-lg);
  border-radius: var(--border-radius-large);
  background: linear-gradient(135deg, #fff1f0 0%, #ffe7e5 55%, #fff7e6 100%);
  border: 2px solid #ff4d4f;
  box-shadow: 0 8px 24px rgba(255, 77, 79, 0.18);
  cursor: pointer;
  animation: important-pulse 2.4s ease-in-out infinite;

  .important-notice-badge {
    position: absolute;
    top: -12px;
    left: 16px;
    padding: 2px 12px;
    border-radius: 999px;
    background: #ff4d4f;
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.04em;
  }

  .important-notice-title {
    color: #cf1322;
    font-size: 16px;
    font-weight: 700;
    margin: 0 0 8px;
  }

  p {
    margin: 0;
    color: #5c0011;
    font-size: var(--font-size-sm);
    line-height: var(--line-height-relaxed);
  }

  .important-notice-tip {
    margin-top: 10px;
    color: #ad2102;
    font-size: 12px;
    font-weight: 600;
  }
}

.wechat-highlight {
  color: #cf1322 !important;
  font-size: 1.15em;
  letter-spacing: 0.02em;
}

.notice-card {
  background: var(--bg-primary);
  border-radius: var(--border-radius-large);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-light);
  border-left: 4px solid var(--primary-color);

  p {
    color: var(--text-secondary);
    font-size: var(--font-size-sm);
    line-height: var(--line-height-relaxed);
    margin: 0;
  }

  p + p {
    margin-top: var(--spacing-sm);
  }

  strong {
    color: var(--text-primary);
    font-weight: var(--font-weight-semibold);
  }
}

.domain-modal-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  color: #cf1322;
}

.domain-modal-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  background: #ff4d4f;
  color: #fff;
  font-size: 12px;
}

.domain-modal-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  color: var(--text-primary);
  line-height: 1.7;

  .domain-modal-lead {
    margin: 0;
    font-size: 16px;
    font-weight: 700;
    color: #cf1322;
  }

  p {
    margin: 0;
  }
}

.domain-modal-wechat {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  background: #fff1f0;
  border: 1px dashed #ff7875;
}

.domain-modal-label {
  color: var(--text-secondary);
  font-size: 13px;
}

.domain-modal-hint {
  color: var(--text-secondary);
  font-size: 13px;
}

.domain-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

@keyframes important-pulse {
  0%,
  100% {
    box-shadow: 0 8px 24px rgba(255, 77, 79, 0.18);
  }
  50% {
    box-shadow: 0 10px 28px rgba(255, 77, 79, 0.32);
  }
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-lg);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-lg);
}

.action-card {
  background: var(--bg-primary);
  border-radius: var(--border-radius-large);
  padding: var(--spacing-lg);
  box-shadow: var(--shadow-light);
  cursor: pointer;
  transition: all var(--transition-normal);

  &:hover {
    box-shadow: var(--shadow-medium);
    transform: translateY(-2px);
  }
}

.action-icon {
  width: 40px;
  height: 40px;
  color: var(--primary-color);
  margin-bottom: var(--spacing-md);

  :deep(svg) {
    width: 100%;
    height: 100%;
  }
}

.action-content {
  h3 {
    font-size: var(--font-size-md);
    font-weight: var(--font-weight-semibold);
    color: var(--text-primary);
    margin-bottom: var(--spacing-xs);
  }

  p {
    color: var(--text-secondary);
    font-size: var(--font-size-sm);
    margin: 0;
  }
}

// 最近活动区域
.recent-activity-section {
  background: var(--bg-primary);
  border-radius: var(--border-radius-large);
  padding: var(--spacing-xl);
  box-shadow: var(--shadow-light);
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-lg);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.activity-item {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--border-radius-medium);
  transition: background var(--transition-fast);

  &:hover {
    background: var(--bg-tertiary);
  }
}

.activity-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &.success {
    background: rgba(24, 160, 88, 0.1);
    color: var(--success-color);
  }

  &.warning {
    background: rgba(240, 160, 32, 0.1);
    color: var(--warning-color);
  }

  &.info {
    background: rgba(32, 128, 240, 0.1);
    color: var(--info-color);
  }

  :deep(svg) {
    width: 16px;
    height: 16px;
  }
}

.activity-content {
  flex: 1;
}

.activity-text {
  color: var(--text-primary);
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-xs);
}

.activity-time {
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
}

.empty-activity {
  text-align: center;
  padding: var(--spacing-xl) 0;
}

// 响应式设计
@media (max-width: 1024px) {
  .welcome-content {
    flex-direction: column;
    text-align: center;
  }

  .stats-grid {
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  }
}

@media (max-width: 768px) {
  .dashboard-main {
    padding: var(--spacing-md);
  }

  .nav-menu {
    display: none;
  }

  .welcome-section {
    padding: var(--spacing-xl);
  }

  .welcome-text h1 {
    font-size: var(--font-size-2xl);
  }

  .welcome-actions {
    flex-direction: column;
    width: 100%;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
