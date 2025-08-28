# Sinopec-auto-list  
通用任务看板的一个简易实现，利用DeepSeek提供邮件分类功能。

[中文](./README-zh.md)|[English](./README.md)

## 前言  
在化工行业的日常运营中，海量电子邮件承载着项目进度、安全警报、审批流程和供应链协调等关键信息。传统的人工分类、优先级判定与进度跟踪方式不仅效率低、易出错，也难以应对日益增长的信息处理需求，可能导致重要信息被遗漏或响应延迟，进而对项目推进和安全管理带来隐患。

为此，我们开发了这套智能邮件分类与协同管理系统。该系统依托人工智能技术，结合化工领域的专业语境，实现对每日数百封邮件的精准自动分类，涵盖工程进度、安全事故处理、文件报批等核心事务类型。分类完成后，系统还能智能评估事件的紧急程度与重要性，自动生成动态排序的待办清单，为团队提供清晰的工作优先级指引。

该系统的核心价值在于其闭环管理能力：不仅能生成任务清单，还可持续追踪邮件的后续交互（例如回复与状态更新）。系统根据最新进展实时自动更新待办事项状态（如"已完成""进行中""待跟进"），确保清单始终与实际情况同步，显著提升团队协作效率与事务处理的透明度。

本系统是我们利用智能化手段应对化工行业信息管理难题的一次积极探索与实践。我们相信，通过对邮件流程关键环节的自动化处理，本系统能够帮助化工企业团队节约精力，聚焦于更高价值的决策与行动，从而全面提升运营效率与风险控制能力。

## 项目亮点

### 智能分批处理机制
- 针对大模型输入限制和幻觉问题，创新性地采用分治算法，将大批量邮件分批次处理
- 每批次处理2封邮件，既保证处理质量，又实现高效批量处理（支持单次处理100+邮件）

### 智能触发优化
- 引入防抖机制（Debounce），设置30秒无新增邮件上传后自动开始分类
- 有效减少不必要的计算资源消耗，提升系统响应效率

### 人性化交互设计
- 采用呼吸灯动画效果，直观展示系统实时处理状态
- 简约而不失科技感的UI设计，提供流畅的用户体验

### 工业场景适配
- 专门针对化工行业邮件特点进行优化训练
- 实际应用于中石化相关业务场景，经过实践验证

## 技术栈  
- 后端：FastAPI, OpenAI, DeepSeek, Scikit-learn  
- 前端：Vue, TDesign  
- 通信协议：WebSocket, HTTP  
- Python 环境：3.12

## 环境搭建

### 1. 安装 Python

注：本文推荐使用 Anaconda 创建虚拟环境。如您已安装 Python 3.12 或不想使用 Anaconda，可跳过本节，直接进入"安装依赖"部分。

请先安装 [Anaconda](https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/Anaconda3-2025.06-1-Windows-x86_64.exe)。

安装完成后，打开 Anaconda Prompt（后文简称"终端"），并依照[清华镜像源 Anaconda 配置教程](https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/)完成配置。

配置完成后，在终端中执行：

```shell
conda create -n auto_list python=3.12 -y
```

完成后激活环境：

```shell
conda activate auto_list
```

### 2. 安装依赖

进入项目根目录，在终端中运行：

```shell
pip install -r requirements.txt
```

### 3. 修改配置文件

修改项目目录下的 `.env` 文件，内容如下所示：

```env
DEEPSEEK_ENDPOINT="https://api.deepseek.com"
API_KEY="sk-******"
```

请将 `API_KEY` 替换为您在 DeepSeek 平台获取的实际 API_KEY。

## 启动系统

在终端中（如使用了虚拟环境需先激活）运行以下命令启动服务：

```shell
uvicorn server:app
```

也可指定主机与端口：

```shell
uvicorn server:app --host 0.0.0.0 --port 8000
```

启动后，访问相应地址即可进入任务看板页面。

## 演示材料
- [系统运行截图](./screenshots/) 
<img src="./screenshots/1.jpg"></img>
- [完整功能录屏](./demo/video.mp4)
<video src="./demo/video.mp4"></video>

## API 接口文档

### 邮件上传接口
- 路径：`POST /upload-email/`
- 功能：上传邮件文件（.eml格式）至服务器进行处理
- 请求格式：`multipart/form-data`

请求参数：

| 参数名 | 类型 | 是否必须 | 说明 |
|--------|------|----------|------|
| file   | File | 是       | 邮件文件 |

响应示例（成功）：
```json
{
  "status": "success",
  "filename": "唯一生成的文件名",
  "queue_size": "当前队列大小"
}
```

响应示例（失败）：
```json
{
  "status": "error",
  "message": "错误信息"
}
```

调用示例：
```bash
curl -X POST http://your-server/upload-email/ -F "file=@email.eml"
```

### 邮件回复标记接口
- 路径：`GET /email_reply/{msg_id}`
- 功能：将指定邮件标记为"已回复"状态

URL 参数：

| 参数名 | 类型   | 是否必须 | 说明               |
|--------|--------|----------|--------------------|
| msg_id | String | 是       | 邮件的 Message-ID |

响应：字符串 `OK`

说明：该操作会更新邮件状态为"replied"，并通过 WebSocket 广播事件：

```json
{
  "event": "email_reply",
  "data": {
    "task_id": "对应的任务ID"
  }
}
```

调用示例：
```bash
curl -X GET http://your-server/email_reply/123456789@example.com
```

## 实践心得
通过本项目，我深入了解了DeepSeek API在实际工业场景中的应用，探索了大模型处理批量任务的优化方案。在开发过程中，针对模型幻觉和系统负载问题，创新性地提出了分批处理和防抖触发机制，显著提升了系统的稳定性和实用性。这次经历让我对AI技术的落地应用有了更深刻的理解，也锻炼了全栈开发和系统架构能力。

期待未来能在DeepSeek平台进一步探索大模型技术的创新应用！