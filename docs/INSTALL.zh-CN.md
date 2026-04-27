# 安装说明

Hermes Control Surface 面向最小化安装的 Debian / Ubuntu 服务器。

它默认以一个轻量 FastAPI 服务运行在 `9091` 端口。

它不需要 nginx。  
它不需要 `.env` 文件。  
默认安装路径是：

```text
/opt/hermes-control-surface
```

## 我应该用哪种安装方式？

如果你只是想先跑起来，推荐使用安装脚本：

```bash
sudo bash scripts/install.sh
```

如果你想清楚知道每一步做了什么，可以按手动安装走。

两种方式最终都会创建同一个服务：

```text
hermes-control-surface.service
```

## 基础依赖

必需系统依赖：

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git curl ca-certificates
```

Python 依赖来自：

```text
requirements.txt
```

UPS、音频等可选功能可能需要额外系统包，后面会单独说明。

## 方式 A：安装脚本

在项目源码目录里执行：

```bash
sudo bash scripts/install.sh
```

脚本会做这些事：

```text
安装 Debian / Ubuntu 基础依赖
复制项目到 /opt/hermes-control-surface
创建 Python 虚拟环境
安装 Python 依赖
如果没有 config/config.yaml，就从示例配置创建
写入 systemd 服务
启动 9091 面板
```

它不会覆盖已有的：

```text
config/config.yaml
```

完成后打开：

```text
http://你的服务器地址:9091/
```

## 方式 B：手动安装

如果你想逐步确认，可以按下面手动执行。

### 1. 放到 /opt

如果你下载的是 release 压缩包：

```bash
sudo mkdir -p /opt
sudo tar -C /opt -xzf hermes-control-surface-v0.1.2.tar.gz
cd /opt/hermes-control-surface
```

如果你是 clone 仓库：

```bash
sudo mkdir -p /opt
sudo cp -a hermes-control-surface /opt/hermes-control-surface
cd /opt/hermes-control-surface
```

如果你已经在 `/opt/hermes-control-surface` 里，可以直接继续。

### 2. 创建 Python 虚拟环境

```bash
sudo python3 -m venv .venv
sudo .venv/bin/python -m pip install --upgrade pip
sudo .venv/bin/python -m pip install -r requirements.txt
```

### 3. 创建本地配置

```bash
sudo cp config/config.example.yaml config/config.yaml
```

然后编辑：

```bash
sudo nano config/config.yaml
```

真实的 `config/config.yaml` 只属于你的本地机器。  
不要把它提交到公开仓库。

### 4. 创建 systemd 服务

```bash
sudo tee /etc/systemd/system/hermes-control-surface.service >/dev/null <<'SERVICE_EOF'
[Unit]
Description=Hermes Control Surface
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/hermes-control-surface
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/hermes-control-surface/.venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 9091
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE_EOF
```

### 5. 启动服务

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now hermes-control-surface.service
```

### 6. 检查

```bash
curl -fsS http://127.0.0.1:9091/ >/dev/null
curl -fsS http://127.0.0.1:9091/api/stats >/dev/null
```

如果需要更完整的只读诊断报告：

```bash
bash scripts/doctor.sh
```

然后打开：

```text
http://你的服务器地址:9091/
```

## 可选功能

有些卡片取决于你的机器上是否真的有对应服务。

不需要就不用安装。

### UPS

如果你要显示 NUT / UPS 状态：

```bash
sudo apt install -y nut-client
```

NUT 服务本身仍然需要你根据自己的 UPS 环境单独配置。

### 音频

如果你要显示或控制本机音频，可能会用到：

```bash
sudo apt install -y bluez pipewire wireplumber mpv socat
```

按你自己的环境安装，不需要全部强制安装。

## 配置热加载

`config.yaml` 会自动热加载。

保存配置后，下一次 API 请求会使用新配置。

如果 YAML 写错，面板会继续使用上一次可用配置。

代码、HTML、依赖变更仍然需要重启服务：

```bash
sudo systemctl restart hermes-control-surface.service
```

## 日志和状态

查看服务状态：

```bash
systemctl status hermes-control-surface.service --no-pager --full
```

查看实时日志：

```bash
journalctl -u hermes-control-surface.service -f
```

检查 API：

```bash
curl -fsS http://127.0.0.1:9091/api/stats
```

## 防火墙提醒

面板默认监听 `9091` 端口。

如果本机能打开，但其他设备打不开，优先检查防火墙、路由器或服务器安全规则。

## 卸载

这会移除服务和安装目录：

```bash
sudo systemctl disable --now hermes-control-surface.service
sudo rm -f /etc/systemd/system/hermes-control-surface.service
sudo systemctl daemon-reload
sudo rm -rf /opt/hermes-control-surface
```

如果你想保留本地配置，卸载前先备份：

```text
/opt/hermes-control-surface/config/config.yaml
```
