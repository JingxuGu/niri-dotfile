# Ubuntu Niri 桌面配置

Ubuntu 26.04.1 LTS、Niri、DankMaterialShell 的桌面与 Shell 配置快照。配置按用户主目录布局保存在 `home/`，可检查后恢复。快照日期：2026 年 10 月 13 日。

## 当前效果

| 组件 | 配置 |
| --- | --- |
| Niri | 窗口间距 8、DP-2 输出缩放 110%、Kitty 圆角和背景模糊 |
| Kitty | JetBrainsMono Nerd Font Mono、12 号字体、0.65 背景不透明度、8 点 padding、隐藏窗口装饰、原生 Wayland |
| Fuzzel | Super + Space、居中深色半透明面板、20 像素圆角、背景模糊与阴影 |
| Zsh / Starship | 原生补全与历史记录；单行目录、Git 状态、Python/Conda 环境、命令耗时和 SSH 主机名 |
| Fastfetch | 纯 ASCII Ubuntu 标志、Nerd Font 标签、淡蓝紫色、对齐的 ` > ` 分隔符，无底部色块 |
| Fcitx5 / Rime | 小鹤双拼、默认简体、显示名称“双拼（小鹤）”、简称“双” |
| Fcitx5 外观 | Candlelight macOS Dark；当前候选字体 Sans 12 |
| 截图 | F1 选区 → Satty 标注 → Enter 保存并复制；截图锁不会被剪贴板后台进程继承 |
| DMS | 动态主题、Dank Island、壁纸插件设置及当前生成的配色文件 |

快照记录的是这台机器的实际配置。DP-2 输出名、壁纸目录和代理端口是机器相关设置；迁移时请调整。Niri 中保留了当前的 `waybar` 启动项，DMS 的系统软件与服务需单独安装和管理。

## 内容

- `home/.config/`：Niri、Kitty、Fuzzel、Fastfetch、Starship、Satty、Fcitx5、DMS 及 GTK/Qt 配色。
- `home/.local/share/fcitx5/`：小鹤方案、用户补丁和 macOS Dark 主题。
- `home/.local/bin/`：截图脚本、Satty 安装脚本，以及当前壁纸后端的启动包装脚本。
- `home/.zshrc`、`.zprofile`、`.profile`、`.bashrc`、`.xinputrc`：Shell 与输入法配置。
- `plugins.json`：DMS 插件仓库与固定提交；`patches/`：mpvpaper 插件的本地修改。
- `snapshot.json`：快照清单；`restore.py`：预览、备份与恢复工具。

程序二进制、字体文件、壁纸/Steam 素材、浏览器数据、SSH/云凭据、缓存、历史记录、Rime 学习词库和生成的 Rime 编译文件不在仓库中。DMS 配色文件是当前快照，启用动态主题后会继续由 DMS 生成。

## 恢复配置

先安装对应组件：Niri 26.04 或更新版本、DankMaterialShell、Matugen、Kitty、Fuzzel、Fastfetch、Zsh、Starship、Fcitx5/Rime、grim、slurp、wl-clipboard、Satty。截图脚本依赖 Bash、Python 3 和 flock。字体需要 JetBrainsMono Nerd Font Mono、Noto Sans 和 Noto Sans CJK。

字体可从 [Nerd Fonts 官方发布页](https://github.com/ryanoasis/nerd-fonts/releases)下载 JetBrainsMono 包，安装到 `~/.local/share/fonts/` 后执行 `fc-cache -f`。

```bash
git clone https://github.com/JingxuGu/niri-dotfile.git
cd niri-dotfile

# 仅预览，不修改当前系统
python3 restore.py

# 确认清单后恢复；现有文件先备份
python3 restore.py --apply

niri validate
fuzzel --check-config
zsh -n ~/.zshrc
```

恢复工具会把文本中的 `/home/grainrain` 改成目标用户的主目录。已有文件备份到 `~/.local/state/niri-dotfile-backups/<时间>/`。它不会安装软件、修改默认 Shell、启用服务或下载壁纸。

Kitty 配置明确使用 `/usr/bin/zsh -l`，所以恢复前应先安装 Zsh。修改账户默认 Shell：

```bash
chsh -s /usr/bin/zsh
```

需要安装 Satty 时，可以检查并运行仓库中的安装脚本：

```bash
bash home/.local/bin/install-screenshot-tools
```

该脚本安装截图依赖，下载并校验 Satty 0.22.0 的 x86_64 发布包。安装完成后，F1 是选区截图快捷键。

Rime 需要系统中的 `/usr/share/rime-data` 包含明月拼音和笔画方案，然后重新部署：

```bash
rime_deployer --build ~/.local/share/fcitx5/rime /usr/share/rime-data ~/.local/share/fcitx5/rime/build
```

可在 Fcitx5 的 Rime 菜单中重新部署。之后重新打开 Kitty；更换登录 Shell 或会话环境变量时注销后重新登录。

## 快捷键

| 按键 | 功能 |
| --- | --- |
| Super + T | Kitty |
| Super + Space | Fuzzel |
| F1 | 选区截图并打开 Satty |
| Super + Print | 全屏截图并打开 Satty |
| Super + Shift + Print | 当前窗口截图并打开 Satty |
| Ctrl + Print | Niri 原生全屏截图 |
| Alt + Print | Niri 原生窗口截图 |
| Ctrl + Space | 切换输入法 |
| Satty 中 Enter | 保存、复制并退出 |
| Satty 中 Escape | 取消并退出 |

## DMS 壁纸插件

插件代码与渲染器需要单独安装。`plugins.json` 记录当前源码提交：

- [dms-wallpaperengine](https://github.com/sgtaziz/dms-wallpaperengine)
- [dms-mpvpaper](https://github.com/kanghengliu/dms-mpvpaper)

将相应仓库放到 `~/.config/DankMaterialShell/plugins/`，切换到 `plugins.json` 中的提交。mpvpaper 还有本地补丁：

```bash
git -C ~/.config/DankMaterialShell/plugins/dms-mpvpaper apply "$PWD/patches/dms-mpvpaper.patch"
```

当前 Wallpaper Engine 后端为 Kirie。`haru` 与 `linux-wallpaperengine` 包装脚本引用 `~/.local/lib/` 和 `~/.local/share/` 中的渲染器、资源及代理库，仓库没有打包这些依赖。Haru 使用本地 7897 端口代理；不需要代理时应调整包装脚本与 proxychains 配置。壁纸素材应自行准备。

## 来源和许可

- Candlelight 主题来自 [thep0y/fcitx5-themes-candlelight](https://github.com/thep0y/fcitx5-themes-candlelight)，MIT 许可见 `licenses/candlelight-LICENSE`。
- 小鹤方案的键位映射来自 [rime/rime-double-pinyin](https://github.com/rime/rime-double-pinyin)，GPLv3 许可见 `licenses/rime-double-pinyin-LICENSE`。
- DMS 插件按其各自上游许可使用。
