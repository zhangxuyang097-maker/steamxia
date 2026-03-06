# Steam 客户端下载工具

一款简洁美观的 Steam 客户端下载工具，支持网络加速功能，帮助用户更流畅地访问 Steam。

## 功能特点

- **网络加速** - 两种加速模式可选
  - DNS优化模式（推荐）- 无需管理员权限
  - Hosts加速模式 - 需要管理员权限
- **一键下载** - 从 Steam 官方 CDN 下载客户端
- **实时进度** - 显示下载进度和速度
- **现代界面** - 深色主题，美观易用
- **快捷操作** - 打开官网、打开下载目录、刷新DNS缓存

## 截图

![Steam下载工具界面](screenshot.png)

## 安装使用

### 方式一：直接运行 exe（推荐）

1. 下载 `dist/Steam下载工具.exe`
2. 双击运行即可
3. 如需使用 Hosts 加速功能，请右键以管理员身份运行

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/你的用户名/steam-downloader.git
cd steam-downloader

# 运行程序
python steam_downloader.py
```

### 打包为 exe

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
pyinstaller --onefile --noconsole --name "Steam下载工具" steam_downloader.py
```

## 使用说明

1. **开启加速**
   - 默认使用 DNS 优化模式，无需管理员权限
   - 切换到 Hosts 模式可获得更好的加速效果（需管理员权限）

2. **下载 Steam**
   - 点击"下载 Steam 客户端"按钮
   - 选择保存位置（默认为下载文件夹）
   - 等待下载完成后可直接安装

## 技术栈

- Python 3.10+
- Tkinter (GUI)
- PyInstaller (打包)

## 目录结构

```
steam-downloader/
├── steam_downloader.py    # 主程序
├── dist/                  # 打包后的exe文件
├── build/                 # 打包临时文件
├── README.md              # 说明文档
└── .gitignore             # Git忽略文件
```

## 注意事项

- 本工具仅供学习交流使用
- 请从官方渠道下载 Steam 客户端
- 加速效果因网络环境而异

## 开源协议

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
