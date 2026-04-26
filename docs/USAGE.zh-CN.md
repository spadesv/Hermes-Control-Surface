# 使用说明

Hermes Control Surface 刻意保持小而清楚。

它最初是围绕一台真实本地机器做出来的，后来才整理成可以分享的项目。  
所以它的配置方式也很直接：先定义你真的在跑什么，再决定页面上显示什么。

## 1. 理解它的工作方式

可以把它理解成三层：

```text
config/config.yaml
  -> 后端状态 API
  -> 前端显示和布局
```

后端负责读取状态。  
前端负责展示状态。  
Capabilities 决定哪些内容应该显示。

## 2. 启动或重启

长期使用建议交给 systemd：

```bash
sudo systemctl restart hermes-control-surface.service
```

如果只是临时在项目目录里测试：

```bash
python3 -m uvicorn server:app --host 0.0.0.0 --port 9091
```

打开：

```text
http://你的主机地址:9091/
```

## 3. 本地配置

创建本地配置：

```bash
cp config/config.example.yaml config/config.yaml
```

编辑配置：

```bash
nano config/config.yaml
```

不要把真实的 `config/config.yaml` 提交到公开仓库。

这个项目不需要 `.env` 文件。

## 4. 热加载

`config.yaml` 会自动热加载。

保存配置后，下一次 API 请求就会使用新配置。

如果 YAML 写错，面板会继续使用上一次可用配置。

代码、HTML、依赖变更仍然需要重启服务：

```bash
sudo systemctl restart hermes-control-surface.service
```

## 5. 语言

语言优先级：

```text
?lang 参数
> 已保存的语言 cookie
> 浏览器 Accept-Language
> 默认语言
```

常用地址：

```text
/?lang=en
/?lang=zh-CN
/?lang=system
```

`system` 会清除手动选择，重新跟随浏览器语言。

## 6. 响应式布局

面板已经同时考虑桌面和手机使用。

桌面端：

```text
更宽的布局
更完整的首屏信息
一次显示更多状态
```

手机端：

```text
紧凑头部
卡片纵向排列
小屏下切换为单列内容
底部抽屉式设置面板
```

手机端不是另一个独立页面。  
它是同一个控制面板针对小屏幕做的适配。

## 7. 显示能力

Capabilities 决定页面上显示什么。

```yaml
dashboard:
  sections:
    network: auto
    audio: hide

  cards:
    ups: auto

  platforms:
    telegram: show
    discord: hide

  services:
    docker: show
    crowdsec: hide
```

支持三个值：

```text
auto  默认行为
show  强制显示
hide  强制隐藏
```

这只是显示控制。  
它不会修改你的系统服务。

## 8. 服务

面板不会扫描所有 systemd 服务。

你只需要定义自己关心的服务：

```yaml
services:
  hermes: hermes-gateway
  docker: docker
  crowdsec: crowdsec
```

然后控制是否显示：

```yaml
dashboard:
  services:
    hermes: show
    docker: show
    crowdsec: hide
```

这样服务列表会更可控，也不会出现意外扫描。

## 9. 可选集成

有些内容取决于你自己的机器环境。

例如：

```text
UPS       需要可用的 NUT 配置
音频      取决于本机 PipeWire / 蓝牙 / mpv 配置
网络      取决于你配置的命令或网卡
服务      取决于你列出的 systemd unit
```

如果某个功能和你的环境无关，可以用 capabilities 隐藏。

## 10. 快速检查

基础检查：

```bash
curl -fsS http://127.0.0.1:9091/ >/dev/null
curl -fsS http://127.0.0.1:9091/api/stats >/dev/null
```

语言检查：

```bash
curl -sD - -o /dev/null \
  -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' \
  http://127.0.0.1:9091/ | grep -i content-language
```

服务状态：

```bash
systemctl status hermes-control-surface.service --no-pager --full
```

实时日志：

```bash
journalctl -u hermes-control-surface.service -f
```

## 11. 常见问题

### 页面打不开

先看服务状态：

```bash
systemctl status hermes-control-surface.service --no-pager --full
```

再看端口：

```bash
ss -lntp | grep ':9091'
```

确认本机能访问：

```bash
curl -fsS http://127.0.0.1:9091/ >/dev/null
```

### 配置改了但页面没变化

保存 `config/config.yaml` 后刷新页面。

如果 YAML 写错，面板会继续使用上一次可用配置。可以看日志：

```bash
journalctl -u hermes-control-surface.service -n 80 --no-pager
```

### 某个卡片或服务行不见了

检查对应的 capability：

```yaml
auto
show
hide
```

如果设置成 `hide`，前端会隐藏它。

### 服务显示离线

先确认真实 systemd 服务名：

```bash
systemctl status your-service-name
```

然后确认 `config.yaml` 里写的是同一个名字。

## 12. 如果你要 fork 或重新发布

如果你只是本地使用，可以跳过这一节。

如果你准备 fork、打包，或者发布自己的修改版本，请先确认没有带上私有文件和生成文件。

不要公开：

```text
config/config.yaml
*.bak.*
__pycache__
*.pyc
运行时数据
缓存文件
带有隐私信息的本地截图
```

通常可以公开：

```text
config/config.example.yaml
README.md
README.zh-CN.md
docs/
server.py
app/
static/
scripts/
requirements.txt
```

真实的 `config/config.yaml` 只属于你的本地机器。  
公开仓库里应该只放 `config/config.example.yaml`。
