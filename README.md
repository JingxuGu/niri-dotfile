# Ubuntu 22.04 + GNOME 桌面配置

`ubuntu-22.04-gnome` 分支面向 Ubuntu 22.04 LTS（Jammy）与 GNOME 42，基于原仓库适配的配置模板。原来的 Ubuntu 26.04 + Niri + DankMaterialShell 配置保存在 [main 分支](https://github.com/JingxuGu/ubuntu-dotfile/tree/main)。

## 配置内容

| 组件 | 配置 |
| --- | --- |
| GNOME / Mutter | Yaru 深色主题、24 小时制、星期和电量百分比、动态工作区、边缘平铺 |
| Ubuntu Dock | 底部、不占满宽度、40 像素图标、智能隐藏；缺少 Dock schema 时跳过 |
| Kitty | 保留原配色、JetBrainsMono Nerd Font Mono 12、0.65 不透明度、8 点 padding、Zsh 登录 Shell |
| Zsh / Bash / Starship | 保留原补全与历史配置、目录/Git/Python/Conda/耗时提示；Starship 未安装时使用普通提示符 |
| Fastfetch | 保留 ASCII Ubuntu 标志和原排版，可选安装 |
| Fcitx5 / Rime | 小鹤双拼、默认简体、Candlelight macOS Dark 候选主题 |
| 截图 | GNOME 42 自带截图/录屏界面，适用于 Wayland 和 Xorg |

`home/` 按用户主目录布局保存文件；`gnome/settings.json` 保存可读的 GSettings 模板。恢复清单在 `snapshot.json` 中，其类型为模板，不是本机配置快照。

本分支移除了 Niri、DMS、Fuzzel、Satty/grim/slurp、壁纸渲染器及其代理包装脚本。切换 Git 分支只改变仓库文件；恢复工具不会清理已经安装到主目录的旧配置。

## 安装依赖

以下命令由你在目标 Ubuntu 22.04 系统执行。恢复工具不会安装软件或修改当前机器的桌面。

```bash
sudo add-apt-repository universe
sudo apt update
sudo apt install git python3 python3-gi kitty zsh bash-completion \
  fcitx5 fcitx5-rime fcitx5-config-qt im-config \
  fcitx5-frontend-gtk2 fcitx5-frontend-gtk3 fcitx5-frontend-gtk4 \
  fcitx5-frontend-qt5 rime-data-luna-pinyin rime-data-stroke librime-bin \
  fonts-noto fonts-noto-cjk
```

使用标准 Ubuntu Desktop 的 GNOME 会话。Ubuntu Dock 使用系统自带扩展。默认配置不下载第三方 GNOME 扩展，也不覆盖已有的扩展启用清单；下方的毛玻璃配置单独安装和应用。

字体从 [Nerd Fonts 官方发布页](https://github.com/ryanoasis/nerd-fonts/releases)下载 JetBrainsMono 包，解压到 `~/.local/share/fonts/` 后执行 `fc-cache -f`。也可以把 `home/.config/kitty/kitty.conf` 中的字体改为本机已有等宽字体。

Starship 和 Fastfetch 是可选组件，Ubuntu 22.04 官方仓库不提供它们。按 [Starship 官方安装文档](https://starship.rs/guide/#installation)及 [Fastfetch 官方仓库](https://github.com/fastfetch-cli/fastfetch)的发布说明安装支持 Ubuntu 22.04 的版本。缺少这些程序时 Shell 仍可启动。

## 预览与恢复

```bash
git clone --branch ubuntu-22.04-gnome --single-branch \
  https://github.com/JingxuGu/ubuntu-dotfile.git
cd ubuntu-dotfile

# 默认仅预览文件
/usr/bin/python3 restore.py

# 同时预览 GNOME 设置，仍不写入
/usr/bin/python3 restore.py --gnome

# 备份并恢复文件，同时应用 GNOME 设置
/usr/bin/python3 restore.py --apply --gnome
```

在目标用户的 GNOME 桌面终端运行，不使用 sudo。`--gnome` 修改当前会话用户的设置，需要系统的 `python3-gi`，推荐明确使用 `/usr/bin/python3`。不传 `--gnome` 时只处理配置文件，不依赖 GI。

恢复前会校验清单与文件路径。已有文件（包括符号链接）备份到 `~/.local/state/ubuntu-dotfile-backups/<时间>/`；Fastfetch 等文件中的原用户路径会替换为目标主目录。重复应用相同配置不会重复覆盖。支持 `--home /path/to/home` 预览或恢复到其他目录，但不能同时使用 `--gnome`。

GNOME 设置先检查 schema、键、值类型、范围及可写状态，再应用。已有自定义快捷键会保留，只追加本分支的 Kitty 快捷键；相同按键的已有自定义绑定需自行解决冲突。桌面主题和下表中列出的系统快捷键会按模板替换。

只操作桌面设置也可以执行：

```bash
/usr/bin/python3 gnome.py
/usr/bin/python3 gnome.py --apply
```

GNOME 修改前的值保存在备份目录的 `gnome-settings.json`，仅记录这次修改的键。撤销时将示例路径换成实际备份路径：

```bash
/usr/bin/python3 gnome.py --undo \
  ~/.local/state/ubuntu-dotfile-backups/<时间>/gnome-settings.json
# 确认预览后添加 --apply 执行撤销
```

撤销会恢复备份中的值（包括当时的自定义快捷键列表），未修改过的键恢复为系统默认；撤销前也会产生新备份。文件可以从同一备份目录手动恢复。

## 输入法与会话兼容性

`~/.xinputrc` 选择 Fcitx5，由 Ubuntu 的 im-config 加载输入法环境；自动启动项在 GNOME 登录时启动 Fcitx5。恢复后注销并重新登录。在 Fcitx5 配置中确认“键盘 - 英语”和 Rime，右键输入法菜单执行“重新部署”，或运行：

```bash
mkdir -p ~/.local/share/fcitx5/rime/build
rime_deployer --build ~/.local/share/fcitx5/rime \
  /usr/share/rime-data ~/.local/share/fcitx5/rime/build
```

GNOME 的 Super + Space 输入源切换已释放给概览；Fcitx5 使用 Ctrl + Space 切换中英文。GNOME“区域与语言”里保留所需键盘布局，中文输入由 Fcitx5/Rime 管理。

Kitty 默认使用 X11，在 GNOME Wayland 会话中通过 XWayland 运行，以兼容 Jammy 的 Kitty 0.21 与 Fcitx5 输入。需要原生 Wayland 时可改为 `linux_display_server wayland`，但需自行确认输入法支持。GNOME Shell 原生界面的候选窗，以及部分 Wayland 应用的输入法可能需要额外适配；参见 [Fcitx 官方 Wayland 文档](https://fcitx-im.org/wiki/Using_Fcitx_5_on_Wayland)。遇到候选窗或输入问题可在登录界面选择“Ubuntu on Xorg”。

GNOME 默认不提供 Niri 的窗口背景模糊效果。壁纸沿用目标系统当前设置。

## 顶栏与 Overview 毛玻璃

使用 [Blur my Shell](https://extensions.gnome.org/extension/3193/blur-my-shell/)；GNOME 42 对应官方版本 47（version tag 42627），不是面向更新 GNOME 的最新版本。可在已安装的 Extension Manager 中搜索并安装，或下载兼容包：

```bash
curl -fL 'https://extensions.gnome.org/download-extension/blur-my-shell@aunetx.shell-extension.zip?version_tag=42627' \
  -o /tmp/blur-my-shell-v47.zip
gnome-extensions install /tmp/blur-my-shell-v47.zip

# 仅预览这个效果配置
/usr/bin/python3 gnome.py --config gnome/blur-my-shell.json
# 备份并应用，只处理这个效果配置
/usr/bin/python3 gnome.py --config gnome/blur-my-shell.json --apply
```

该配置将顶栏背景设为透明，在壁纸上应用静态模糊（半径 30、亮度 0.8）；Overview 背景使用半径 40、亮度 0.65。Overview 中顶栏复用已有模糊背景，避免重复叠加。应用菜单/文件夹和应用窗口、Dock、截图界面、锁屏的额外模糊关闭，后续可在扩展首选项调整。

工具会读取扩展私有 schemas，保留其他扩展列表并追加 Blur my Shell。备份及撤销方式与上文 `gnome.py --undo` 相同；不会重新应用基础主题、Dock 或快捷键模板。

第一次通过命令行安装后，当前 GNOME Shell 可能尚未发现扩展。Wayland 会话需要注销后重新登录；配置会在新会话中自动生效。可在 Extension Manager 查看开关和首选项，或运行 `gnome-extensions info blur-my-shell@aunetx` 确认状态为 ENABLED。

## 快捷键

| 按键 | 功能 |
| --- | --- |
| Super + T | Kitty |
| Super / Super + Space / Super + S | GNOME 概览与搜索 |
| Super + Q / Alt + F4 | 关闭窗口 |
| Super + Up / Down | 最大化 / 取消最大化 |
| F1 / Print | GNOME 原生截图界面，可选区域、窗口、全屏或录屏 |
| Shift + Print / Ctrl + Print | 直接全屏截图 |
| Alt + Print | 直接当前窗口截图 |
| Ctrl + Space | Fcitx5 中英文切换 |

GNOME 42 的截图界面见 [官方发布说明](https://release.gnome.org/42/)。截图会保存到图片目录下的 Screenshots，并复制到剪贴板；需要绘图标注时另用图片编辑器。

## 验证

```bash
/usr/bin/python3 -m unittest discover -s tests -v
bash -n home/.bashrc
sh -n home/.profile
sh -n home/.xinputrc
zsh -n home/.zshrc
zsh -n home/.zprofile
```

文件恢复测试使用临时主目录；GNOME 测试使用内存后端，不修改真实桌面。测试验证路径冲突、符号链接备份、重复恢复、GNOME 设置值兼容性及备份撤销；实际字体、窗口渲染与输入体验需登录后确认。

## 来源和许可

- Candlelight 主题来自 [thep0y/fcitx5-themes-candlelight](https://github.com/thep0y/fcitx5-themes-candlelight)，MIT 许可见 `licenses/candlelight-LICENSE`。
- 小鹤键位来自 [rime/rime-double-pinyin](https://github.com/rime/rime-double-pinyin)，GPLv3 许可见 `licenses/rime-double-pinyin-LICENSE`。
