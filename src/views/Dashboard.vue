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
            <div class="important-notice-badge">最新免费版</div>
            <p class="important-notice-title">
              本站为最新免费版地址，请收藏，以免走丢
            </p>
            <p>
              最新免费版地址：
              <a :href="NEW_SITE_URL" class="notice-link" @click.stop>{{
                NEW_SITE_URL
              }}</a>
            </p>
            <p>
              如果进入本站后看不到原来的账号或配置，请使用原来的浏览器打开旧网站，
              在“备份 /
              恢复”中手动导出备份，再到本站导入恢复。不同网址的数据不会自动同步。
            </p>
            <p>
              旧网站将于
              <strong>2026年12月3日</strong> 关闭，请在关闭前完成备份迁移。
            </p>
            <p>灵云脚本免费版将持续维护与更新，功能持续升级中。</p>
            <p>
              总域名：<strong>yanling.fun</strong><br />
              联系微信：<strong>FieYangu</strong>（付费版支持试用与购买，问题反馈、功能建议请联系）
            </p>
            <p>
              您的每一次付费购买，都是支持免费版持续更新和功能全面升级的最大动力。
            </p>
            <p class="important-notice-tip">点击查看详情与联系方式</p>
          </div>
        </section>

        <n-modal
          v-model:show="showDomainNotice"
          preset="card"
          :mask-closable="false"
          :closable="true"
          class="domain-notice-modal"
          style="width: 92%; max-width: 480px"
        >
          <template #header>
            <div class="domain-modal-header">
              <span class="domain-modal-badge">最新免费版</span>
              <span>收藏本站与数据迁移</span>
            </div>
          </template>

          <div class="domain-modal-body">
            <p class="domain-modal-lead">
              本站为最新免费版地址，请收藏，以免走丢。
            </p>
            <p>
              <a :href="NEW_SITE_URL" class="notice-link">{{ NEW_SITE_URL }}</a>
            </p>
            <p>
              新旧网址的数据不会自动同步。如果本站看不到原来的数据，请使用原来的浏览器
              打开旧网站，在“备份 / 恢复”中导出备份文件，再到本站的“备份 /
              恢复”中导入。
            </p>
            <p>
              旧网站将于 <strong>2026年12月3日</strong> 关闭，请提前备份迁移。
            </p>
            <p>
              灵云脚本免费版持续维护更新。脚本问题反馈、功能建议，以及付费版试用与购买，
              请联系微信 <strong>{{ WECHAT_ID }}</strong
              >。感谢大家的支持。
            </p>
            <div class="domain-modal-wechat">
              <div class="domain-modal-wechat-info">
                <span class="domain-modal-label">微信号</span>
                <strong>{{ WECHAT_ID }}</strong>
              </div>
              <n-button
                size="small"
                :loading="copyingWechat"
                @click.stop="copyWechatId"
              >
                复制微信号
              </n-button>
            </div>
          </div>

          <template #footer>
            <div class="domain-modal-footer">
              <n-button type="primary" @click="acknowledgeDomainNotice">
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
import { copyToClipboard } from "@/utils/clubBattleUtils";

const router = useRouter();
const message = useMessage();
const tokenStore = useTokenStore();
const { getArrayBuffer } = useIndexedDB();

const DOMAIN_NOTICE_KEY = "new_server_notice_acked_20261125";
const NEW_SITE_URL = "http://124.222.163.110:6660";
const WECHAT_ID = "FieYangu";
const showDomainNotice = ref(false);
const copyingWechat = ref(false);

const copyWechatId = async () => {
  if (copyingWechat.value) return;
  copyingWechat.value = true;
  try {
    await copyToClipboard(WECHAT_ID);
    message.success(`已复制微信号：${WECHAT_ID}`);
  } catch (error) {
    console.error("复制微信号失败:", error);
    message.error(`复制失败，请手动添加：${WECHAT_ID}`);
  } finally {
    copyingWechat.value = false;
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

  // 迁移公告：进入首页自动弹窗，确认后 24 小时内不再强弹。
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
  background: var(--bg-primary);
  border: 1px solid var(--border-color, rgba(0, 0, 0, 0.08));
  border-left: 4px solid var(--warning-color, #f0a020);
  box-shadow: var(--shadow-light);
  cursor: pointer;

  .important-notice-badge {
    position: absolute;
    top: -12px;
    left: 16px;
    padding: 2px 12px;
    border-radius: 999px;
    background: var(--warning-color, #f0a020);
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.04em;
  }

  .important-notice-title {
    color: var(--text-primary);
    font-size: 16px;
    font-weight: 700;
    margin: 0 0 8px;
  }

  p {
    margin: 0;
    color: var(--text-secondary);
    font-size: var(--font-size-sm);
    line-height: var(--line-height-relaxed);
  }

  p + p {
    margin-top: var(--spacing-sm);
  }

  strong {
    color: var(--text-primary);
    font-weight: var(--font-weight-semibold);
  }

  .important-notice-tip {
    margin-top: 10px;
    color: var(--text-tertiary, var(--text-secondary));
    font-size: 12px;
  }
}

.notice-link {
  color: var(--primary-color);
  text-decoration: underline;
  overflow-wrap: anywhere;
}

.domain-modal-header {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  color: var(--text-primary);
}

.domain-modal-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--warning-color, #f0a020);
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
  }

  p {
    margin: 0;
    color: var(--text-secondary);
  }

  strong {
    color: var(--text-primary);
  }
}

.domain-modal-wechat {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--bg-secondary, rgba(0, 0, 0, 0.03));
  border: 1px dashed var(--border-color, rgba(0, 0, 0, 0.12));
}

.domain-modal-wechat-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.domain-modal-label {
  color: var(--text-secondary);
  font-size: 13px;
}

.domain-modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
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
