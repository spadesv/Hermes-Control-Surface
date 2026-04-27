# Hermes Control Surface 配置字段参考

本文解释 Hermes Control Surface 的公开 YAML 配置模型。

编辑前先复制示例配置：

```bash
cp config/config.example.yaml config/config.yaml
```

不要把你的私有 `config/config.yaml` 提交到公开仓库。

## 核心字段

| 路径 | 用途 | 说明 |
|---|---|---|
| `site.page_title` | 浏览器标题 | 仅显示用途 |
| `site.port` | 示例服务端口 | 默认发布配置使用 `9091` |
| `frontend.badge_*` | 顶部徽标 | 空值表示尽量自动探测 |
| `frontend.brand_*` | 顶部品牌文字 | 由 `server.py` 渲染 |
| `build.*` | HCS 构建元数据 | 用于 `/build-meta.json` 和设置底部版本号 |
| `agent.*` | Hermes Agent 路径 | 读取 Agent 版本、模型、网关状态、cron jobs |
| `network.*` | WAN / Proxy / Gateway 显示 | 可选，不需要可关闭 |
| `services.*` | systemd unit allow-list | 驱动动态服务行 |
| `ups.*` | NUT UPS 集成 | HCS 只读取 NUT，不配置 NUT |
| `bluetooth.*` | 蓝牙音响状态 | 可选 |
| `mpv.*` | MPV IPC 状态 | 可选 |
| `cron_display_names` | cron 友好名称 | 仅显示映射 |
| `dashboard.*` | UI 显示策略 | `auto`、`show`、`hide` |

## services 与 dashboard.services 的区别

`services:` 定义检测对象。

```yaml
services:
  docker: docker
  nginx: nginx
```

`dashboard.services:` 控制是否显示这一行。

```yaml
dashboard:
  services:
    docker: show
    nginx: auto
```

Hermes Control Surface 不会扫描所有 systemd 服务。用户必须显式列出想监控的服务。

## 平台行

平台行由 Hermes gateway state 和 `dashboard.platforms` 动态生成。

```yaml
dashboard:
  platforms:
    telegram: auto
    discord: auto
    homeassistant: auto
```

如果未来 gateway state 出现 `slack` 或 `matrix`，HCS 不需要再写死前端行。

## 显示策略

| 值 | 含义 |
|---|---|
| `auto` | 有相关配置或数据时显示 |
| `show` | 强制显示 |
| `hide` | 强制隐藏 |

## 构建元数据

`build:` 是 Hermes Control Surface 的版本，不是 Hermes Agent 的版本。

```yaml
build:
  version: 0.1.2
  build_date: "2026-04-27"
  commit: v0.1.2
  channel: stable
```

Hermes Agent 信息单独显示在 `/api/stats.agent`。

## 热加载

合法 YAML 通常会在下一次 API 请求生效。Python、HTML、依赖变更仍需要重启服务。
