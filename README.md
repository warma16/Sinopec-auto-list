# Sinopec-auto-list  
A lightweight implementation of a universal task board, leveraging DeepSeek for email classification.

[中文](./README-zh.md)|[English](./README.md)

## Introduction  
In the daily operations of the chemical industry, a massive volume of emails carries critical information such as project progress, safety alerts, approval processes, and supply chain coordination. Traditional manual methods for categorization, priority assessment, and progress tracking are not only inefficient and error-prone but also struggle to cope with the growing demand for information processing. This may lead to missed critical information or delayed responses, thereby posing risks to project execution and safety management.

To address this, we developed this intelligent email classification and collaborative management system. The system utilizes artificial intelligence technology, tailored to the professional context of the chemical industry, to achieve precise automatic classification of hundreds of daily emails. It covers core transaction types such as engineering progress, safety incident handling, and document approvals. After classification, the system can intelligently assess the urgency and importance of events, automatically generating a dynamically sorted to-do list to provide teams with clear work priority guidance.

The core value of the system lies in its closed-loop management capability: it not only generates task lists but also continuously tracks subsequent email interactions (such as replies and status updates). The system automatically updates the status of to-do items (e.g., "completed," "in progress," "pending follow-up") in real time based on the latest developments, ensuring the list remains synchronized with the actual situation and significantly improving team collaboration efficiency and transaction processing transparency.

This system represents our active exploration and practice in using intelligent methods to tackle information management challenges in the chemical industry. We believe that by automating key processes in email management, this system can help chemical industry teams save energy and focus on higher-value decisions and actions, thereby enhancing overall operational efficiency and risk control capabilities.

## Key Features

### Intelligent Batch Processing Mechanism
- Addresses large model input limitations and hallucination issues with an innovative divide-and-conquer algorithm, processing large volumes of emails in batches.
- Processes 2 emails per batch, ensuring both quality and efficiency (supports processing 100+ emails in a single run).

### Smart Trigger Optimization
- Incorporates a debounce mechanism, automatically starting classification 30 seconds after no new emails are uploaded.
- Effectively reduces unnecessary computational resource consumption and improves system responsiveness.

### User-Friendly Interaction Design
- Features a breathing light animation to intuitively display real-time processing status.
- Minimalist yet tech-inspired UI design ensures a smooth user experience.

### Industrial Scenario Adaptation
- Optimized and trained specifically for the characteristics of chemical industry emails.
- Practically applied in Sinopec-related business scenarios and validated through real-world use.

## Tech Stack  
- Backend: FastAPI, OpenAI, DeepSeek, Scikit-learn  
- Frontend: Vue, TDesign  
- Communication Protocols: WebSocket, HTTP  
- Python Environment: 3.12

## Environment Setup

### 1. Install Python

Note: This guide recommends using Anaconda to create a virtual environment. If you already have Python 3.12 installed or prefer not to use Anaconda, you can skip this section and proceed directly to the "Install Dependencies" part.

First, install [Anaconda](https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/Anaconda3-2025.06-1-Windows-x86_64.exe).

After installation, open Anaconda Prompt (referred to as the "terminal" hereafter) and follow the [Tsinghua Mirror Anaconda Configuration Guide](https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/) to complete the setup.

Once configured, execute the following in the terminal:

```shell
conda create -n auto_list python=3.12 -y
```

After completion, activate the environment:

```shell
conda activate auto_list
```

### 2. Install Dependencies

Navigate to the project root directory and run the following in the terminal:

```shell
pip install -r requirements.txt
```

### 3. Modify Configuration File

Update the `.env` file in the project directory with the following content:

```env
DEEPSEEK_ENDPOINT="https://api.deepseek.com"
API_KEY="sk-******"
```

Replace `API_KEY` with your actual API_KEY obtained from the DeepSeek platform.

## Launch the System

In the terminal (ensure the virtual environment is activated if used), run the following command to start the service:

```shell
uvicorn server:app
```

You can also specify the host and port:

```shell
uvicorn server:app --host 0.0.0.0 --port 8000
```

After launching, access the corresponding address to enter the task board page.

## Demo Materials
- [System Screenshots](./screenshots/) 
<img src="./screenshots/1.jpg"></img>
- [Full Feature Video](./demo/video.mp4)
<video src="./demo/video.mp4"></video>

## API Documentation

### Email Upload Interface
- Endpoint: `POST /upload-email/`
- Function: Upload email files (.eml format) to the server for processing
- Request Format: `multipart/form-data`

Request Parameters:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file      | File | Yes      | Email file  |

Response Example (Success):
```json
{
  "status": "success",
  "filename": "uniquely generated filename",
  "queue_size": "current queue size"
}
```

Response Example (Failure):
```json
{
  "status": "error",
  "message": "error message"
}
```

Example Call:
```bash
curl -X POST http://your-server/upload-email/ -F "file=@email.eml"
```

### Email Reply Marking Interface
- Endpoint: `GET /email_reply/{msg_id}`
- Function: Mark a specified email as "replied"

URL Parameters:

| Parameter | Type   | Required | Description           |
|-----------|--------|----------|-----------------------|
| msg_id    | String | Yes      | Email Message-ID     |

Response: String `OK`

Description: This operation updates the email status to "replied" and broadcasts an event via WebSocket:

```json
{
  "event": "email_reply",
  "data": {
    "task_id": "corresponding task ID"
  }
}
```

Example Call:
```bash
curl -X GET http://your-server/email_reply/123456789@example.com
```

## Reflections
Through this project, I gained in-depth understanding of DeepSeek API’s application in real industrial scenarios and explored optimization strategies for batch task processing with large models. During development, to address model hallucination and system load issues, I innovatively proposed batch processing and debounce triggering mechanisms, significantly enhancing system stability and practicality. This experience deepened my understanding of AI technology implementation and honed my full-stack development and system architecture skills.

I look forward to further exploring innovative applications of large model technology on the DeepSeek platform in the future!