# Cursor Switcher (Cursor 账号切换助手)

一个专为 Cursor 开发者设计的账号管理与快速切换工具。支持多账号管理、机器 ID 自动重置、批量导入导出等功能，帮助您无缝切换不同的开发环境。

![App Icon](assets/icon.svg)

## 🚀 核心功能

- **多账号管理**：支持添加、删除单个账号，或批量管理多个 Cursor 账号。
- **一键切换**：在多个账号之间快速切换，切换时自动重置 Machine ID 以确保账号独立性。
- **自动重置**：切换账号时自动执行重置逻辑，解决账号登录失效问题。
- **批量操作**：支持 JSON 格式的账号批量导入与导出，方便备份与分享。
- **现代化界面**：基于 Electron 构建，采用 Tailwind CSS 设计，提供清晰的表格视图与分页查询。
- **日志监控**：内置实时日志弹窗，随时掌握切换进度与系统状态。

## 🛠️ 安装与运行

### 环境要求
- Node.js (建议 v16+)
- Python 3.x

### 开发环境运行
1. 克隆代码到本地
2. 安装依赖：
   ```bash
   npm install
   ```
3. 启动应用：
   ```bash
   npm start
   ```

### 项目打包

根据您的操作系统，选择对应的打包命令。打包后的安装包将生成在 `dist` 目录下。

#### macOS (DMG)
支持 Intel 芯片 (x64) 和 Apple Silicon (M1/M2/M3, arm64)。

- **打包所有 macOS 版本**:
  ```bash
  npm run build:mac
  ```
- **仅打包 Apple Silicon (M系列芯片)**:
  ```bash
  npm run build:mac-arm
  ```
- **仅打包 Intel 芯片**:
  ```bash
  npm run build:mac-x64
  ```

#### Windows (EXE)
支持 x64、x86 (32位) 以及 ARM64 架构。

- **打包所有 Windows 版本**:
  ```bash
  npm run build:win
  ```
- **仅打包 x64 (64位)**:
  ```bash
  npm run build:win64
  ```
- **仅打包 x86 (32位)**:
  ```bash
  npm run build:win32
  ```
- **仅打包 ARM64**:
  ```bash
  npm run build:winarm
  ```

## 📖 使用说明

### 1. 添加账号
点击界面顶部的 **"添加账号"** 按钮，输入 `email`、`access_token` 和 `refresh_token` 即可。

### 2. 切换账号
在列表中找到目标账号，点击右侧操作栏的 **"切换"** 按钮。系统会自动：
- 备份当前配置
- 重置 Machine ID
- 写入新账号 Token

### 3. 批量导入/导出
- **导出**：点击 **"批量导出"**，系统将生成包含所有账号信息的 `cursor_accounts_backup.json`。
- **导入**：点击 **"批量导入"**，选择符合格式的 JSON 文件即可快速同步。

### 4. 账号删除
- 点击单个账号后的 **"删除"** 按钮进行单项删除。
- 勾选多个账号后，点击顶部的 **"批量删除"** 按钮进行清理。

## ⚠️ 注意事项
- 本工具会修改 Cursor 的本地配置文件，建议在操作前进行账号导出备份。
- 切换账号后，Cursor 可能需要重启以应用新的配置。

## 📄 开源协议
MIT License
