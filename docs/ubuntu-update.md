# Ubuntu 一条命令更新 helper

两个项目独立部署：helper 使用 `/root/xyzw-helper`，platform 的目录和 Nginx 配置不变。
本说明只配置构建产物发布和更新，不会安装、修改或重启 Nginx。

## 一次性准备

先配置好 helper 自己的 Nginx 网站：端口 `6660`，网站目录
`/root/xyzw-helper`，域名 `helper.xyanling.fun`。需要保留 Vue 路由回退和
`vite.config.js` 中对应的登录 API 代理；Cloudflare 的 `_worker.js` 不会在 Nginx 下执行。

在 Ubuntu 的 root 终端安装更新命令：

```bash
apt-get update
apt-get install -y python3 curl ca-certificates acl
curl -fL --retry 3 https://raw.githubusercontent.com/Ethan0648/xyzw_web_helper/main/scripts/update-helper.py -o /tmp/update-helper.py
install -m 755 /tmp/update-helper.py /usr/local/bin/update-helper
mkdir -p /root/xyzw-helper
```

每条命令成功后再执行下一条。安装不需要 GitHub Token、Node 或服务器 SSH 密钥。

确认 Nginx 的工作进程用户：

```bash
nginx -T 2>&1 | grep -E '^[[:space:]]*user[[:space:]]'
```

若为 Ubuntu 常见的 `www-data`，执行以下权限设置；若为其他用户，用实际用户名替换：

```bash
setfacl -m u:www-data:--x /root
setfacl -R -m u:www-data:r-X /root/xyzw-helper
find /root/xyzw-helper -type d -exec setfacl -m d:u:www-data:r-x {} +
```

这里只给工作进程穿过 `/root` 和读取 helper 所需的权限，不修改 platform 目录权限。
更新器创建的目录和文件分别可被读取为 755 和 644。

## 每次更新

仓库的 `main` 为新服务器版本，公告包含最新免费版地址、收藏提醒和旧站数据迁移说明。
新地址为 `http://124.222.163.110:6660`。`update-helper` 只用于新服务器；
旧站关闭公告由旧站手动维护，不再单独维护旧站分支。

1. 打开仓库的 **Actions → build-dist → Run workflow**，选择 **main** 分支。
2. 等待运行成功。流程生成 `dist` Artifact，同时发布一个新的 Release，包含
   `dist.zip` 和 `dist.zip.sha256`，并标记为 Latest。
3. 在服务器的 root 终端执行：

   ```bash
   update-helper
   ```

4. 刷新网页。无需重启 Nginx。

首次成功发布前，更新器会因没有可用 Release 或缺少附件而退出，不会修改网页。
其他分支仍可生成 Artifact，但不会发布服务器使用的 Latest Release。
工作流使用仓库自带的 `GITHUB_TOKEN` 的 `contents: write` 权限发布，无需新增 Secret。

公开的固定下载地址：

- <https://github.com/Ethan0648/xyzw_web_helper/releases/latest/download/dist.zip>
- <https://github.com/Ethan0648/xyzw_web_helper/releases/latest/download/dist.zip.sha256>

更新器实际会先锁定同一个 Release 的附件地址，防止下载期间有新发布造成压缩包和校验文件不匹配。

## 更新行为与故障排查

- 下载、SHA-256 校验和解压全部在临时目录完成，失败时不改网站文件。
- 校验通过后逐个替换文件，最后替换首页；拒绝压缩包中的越界路径、符号链接以及目标路径中的符号链接。
- 仅更新 `/root/xyzw-helper`，不会删除旧文件，不操作 `/root/xyzw-platform` 或 Nginx。
- 保留旧资源是为了兼容已打开的网页，但旧文件会占空间；需要清理时另行安排维护。
- 这是文件覆盖更新，不是整个网站的原子切换。写入阶段如果磁盘满或断电，可能留下部分更新的文件；修复后重新运行即可。
- 提示 404：确认 main 的 build-dist 已成功发布 Release，且包含两个附件。
- 提示网络错误或 GitHub API 限流：稍后重新运行；服务器需要能访问 GitHub API 和 Release 下载服务。
- 网站返回 403：确认 Nginx 工作进程用户和上面的目录访问权限。
- 网站打不开但本机 `curl -I http://127.0.0.1:6660/` 成功：检查云防火墙和系统防火墙是否放行 TCP 6660。

更新命令自身不自动升级。以后修改了更新脚本时，重新执行上面的 curl 和 install 两条命令即可。
