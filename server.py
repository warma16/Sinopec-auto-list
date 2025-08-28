from fastapi import FastAPI, Request, BackgroundTasks, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from llm import LLM, sys_prompt
from dotenv import load_dotenv
from uuid import uuid4
import json
from preprocessor import  compress_until_below_limit, extract_eml_metadata, extract_eml_text
from contextlib import asynccontextmanager
import time
import os
import shutil
import random
import asyncio
from typing import Dict, List
import threading
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("email_processor")

#env

# 加载 .env 文件中的环境变量
load_dotenv()  # 默认加载当前目录下的 .env 文件

# 获取环境变量
endpoint_ = os.getenv("DEEPSEEK_ENDPOINT")
api_key = os.getenv("API_KEY")

# 全局状态管理
batch_jobs: Dict[str, Dict] = {}  # 存储所有批处理任务的状态
completed_batches: Dict[str, Dict] = {}  # 存储已完成的批处理任务
file_processing_queue = []  # 文件处理队列
last_upload_time = 0  # 最后上传时间戳
is_processing = False  # 是否正在处理
BATCH_SIZE = 2  # 每批处理的邮件数量
PROCESSING_FOLDER = "processing"
PROCESSED_FOLDER = "processed"
UPLOAD_DIR = "inbox_emails"
RESULTS_DIR = "results"  # 结果存储目录
SUSTAIN_DIR="sustain_results"
RETENTION_MINUTES = 60  # 结果保留时间(分钟)
CKPT_CONTENT={
    "list":[],
    "mail2id":{},
    "id2mail":{}
}
# 定义锁
lock = threading.Lock()  # 用于同步阻塞操作
async_lock = asyncio.Lock()  # 用于异步操作

# 创建必要的目录
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSING_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(SUSTAIN_DIR,exist_ok=True)

# WebSocket管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event: str, data: dict):
        """向所有客户端广播事件"""
        message = json.dumps({"event": event, "data": data})
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.disconnect(connection)

manager = ConnectionManager()

async def broadcast_global_event(event: str, data: dict):
    """向所有客户端广播事件（通过WebSocket）"""
    await manager.broadcast(event, data)

def broadcast_global_batch_status():
    """广播所有批处理任务状态更新"""
    # 收集所有批处理任务状态
    active_batches = []
    for batch_id, state in batch_jobs.items():
        # 计算整体进度
        total_tasks = len(state["tasks"])
        completed_tasks = sum(1 for t in state["tasks"] if t.get("complete", False))
        progress = int((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0
        
        active_batches.append({
            "batch_id": batch_id,
            "progress": progress,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "status": state.get("status", ""),
            "start_time": state.get("start_time", 0),
            "tasks": [
                {
                    "task_id": t["task_id"],
                    "status": t.get("status", ""),
                    "complete": t.get("complete", False),
                    "results_available": t.get("results") is not None
                }
                for t in state.get("tasks", [])
            ]
        })
    
    # 广播全局状态
    asyncio.create_task(broadcast_global_event("batch_status", {
        "active_batches": active_batches,
        "queue_size": len(file_processing_queue)
    }))

async def process_single_task(batch_id: str, task_id: str, files: List[str]):
    """处理单个任务（一批邮件）并保存结果"""
    if batch_id not in batch_jobs:
        return
        
    batch_state = batch_jobs[batch_id]
    task_state = next((t for t in batch_state["tasks"] if t["task_id"] == task_id), None)
    
    if not task_state:
        return
        
    # 更新任务状态为"处理中"
    task_state["status"] = "处理中"
    broadcast_global_batch_status()
    
    # 移动文件到处理目录
    batch_files = []
    for filename in files:
        src = os.path.join(UPLOAD_DIR, filename)
        dest = os.path.join(PROCESSING_FOLDER, filename)
        try:
            shutil.move(src, dest)
            batch_files.append(dest)
        except Exception as e:
            task_state["status"] = f"移动文件错误: {str(e)}"
            broadcast_global_batch_status()
    
    # 处理邮件内容
    batch_data = []
    idx=0
    for filepath in batch_files:
        try:
            metadata = extract_eml_metadata(filepath)
            text_content = extract_eml_text(filepath)
            title=metadata.get('Subject', f'无主题-${idx}')
            send_date=metadata.get("Date","今日")
            msg_id=metadata.get("Message-ID","")
            loop_abs = asyncio.get_running_loop()
            # 生成摘要（根据内容长度决定）
            if len(text_content) >= 2000 and len(text_content)<100000:
                task_state["status"] = "生成邮件摘要"
                broadcast_global_batch_status()
                abstract_ = await loop_abs.run_in_executor(
                    None, 
                    lambda: LLM(
                        endpoint_,
                        api_key
                    ).gn_abstract(
                        text_content
                    )
                )
                content = abstract_
            else:
                content = text_content
            
            batch_data.append({
                "id": os.path.basename(filepath),
                "title": title,
                "content": content[:2000],  # 限制输入长度
                "send_date":send_date
            })
            if msg_id == "":
                print("无msg_id")
            else:
                CKPT_CONTENT["mail2id"].update({
                    msg_id:os.path.basename(filepath)
                })
                CKPT_CONTENT["id2mail"].update({
                    os.path.basename(filepath):msg_id
                })
            
        except Exception as e:
            print(e)
            task_state["status"] = f"处理文件错误: {str(e)}"
            broadcast_global_batch_status()
    #print(task_id)
    #print("in1 batch")
    #print(batch_data)
    loop_compress = asyncio.get_running_loop()
    batch_data=await loop_compress.run_in_executor(
        None,
        lambda:compress_until_below_limit(batch_data,131072)
    )
    #print(task_id)
    #print("in2 batch")
    #print(batch_data)
    # LLM处理
    task_state["status"] = "AI分析中"
    broadcast_global_batch_status()
    
    try:
        loop = asyncio.get_running_loop()
        print(task_id)
        print("after batch")
        print(batch_data)
        # 在单独的线程中运行同步的LLM调用
        full_output = await loop.run_in_executor(
            None, 
            lambda: LLM(
                endpoint_,
                api_key
            ).call_llm(
                sys_prompt,
                user_inputs=[
                    f"邮件数目：{len(batch_data)}\njson格式\n{json.dumps(batch_data, ensure_ascii=False)}"
                ],
                #model="deepseek-reasoner"
                model="deepseek-chat"
            )
        )
        
        
        # 处理流式输出
        
        
        # 解析LLM输出
        try:
            # 尝试提取JSON部分
            json_start = full_output.find('[')
            json_end = full_output.rfind(']') + 1
            json_str = full_output[json_start:json_end]
            #print("fetch_json")
            #print(json_str)
            
            result = json.loads(json_str)
            task_results = result
            for i in range(len(task_results)):
                task_result=task_results[i]
                task_result.update({
                    "status":"pending"
                })
                task_results[i]=task_result
            
            # 保存任务结果
            task_state["results"] = task_results
            task_state["status"] = "处理完成"
            
            # 保存结果到文件
            result_filename = f"task_{task_id}_results.json"
            result_path = os.path.join(RESULTS_DIR, result_filename)
            with open(result_path, "w") as f:
                json.dump({
                    "task_id": task_id,
                    "batch_id": batch_id,
                    "files": files,
                    "results": task_results,
                    "timestamp": time.time(),
                    "status":task_state["status"]
                }, f)
            
            logger.info(f"任务 {task_id} 完成，结果保存至 {result_path}")
        except json.JSONDecodeError as e:
            print("解析数据失败")
            print(e)
            task_state["status"] = "解析失败"
            task_state["results"] = [{
                "error": "解析失败",
                "raw_output": full_output[:500] + "..." if len(full_output) > 500 else full_output
            }]
            
    except Exception as e:
        logger.exception(f"处理任务 {task_id} 时发生错误")  # 记录完整堆栈
        task_state["status"] = f"处理错误: {str(e)}"
        task_state["results"] = [{"error": str(e)}]
        task_state["complete"] = True
        task_state["end_time"] = time.time()
    
    # 移动已处理文件
    for filepath in batch_files:
        try:
            dest = os.path.join(PROCESSED_FOLDER, os.path.basename(filepath))
            shutil.move(filepath, dest)
        except Exception as e:
            task_state["status"] = f"移动文件错误: {str(e)}"
    
    # 标记任务完成
    task_state["complete"] = True
    task_state["end_time"] = time.time()
    broadcast_global_batch_status()

async def batch_processing_pipeline(batch_id: str):
    global is_processing,CKPT_CONTENT,SUSTAIN_DIR
    
    if batch_id not in batch_jobs:
        return
        
    batch_state = batch_jobs[batch_id]
    total_emails = batch_state["total_emails"]
    email_list = batch_state["email_list"]
    
    # 计算需要多少任务（批次）
    num_tasks = (total_emails + BATCH_SIZE - 1) // BATCH_SIZE
    batch_state["num_tasks"] = num_tasks
    
    # 创建任务
    batch_state["tasks"] = []
    for i in range(num_tasks):
        start_idx = i * BATCH_SIZE
        end_idx = min((i + 1) * BATCH_SIZE, total_emails)
        task_files = email_list[start_idx:end_idx]
        
        task_id = f"task_{i+1}_{uuid4().hex[:6]}"
        batch_state["tasks"].append({
            "task_id": task_id,
            "files": task_files,
            "status": "等待中",
            "progress": 0,
            "reasoning": "",
            "reply": "",
            "results": None,  # 初始化为None，完成后填充
            "complete": False,
            "start_time": time.time()
        })
    
    # 广播初始状态
    broadcast_global_batch_status()
    
    batch_state["status"] = "分析邮件内容特性..."
    broadcast_global_batch_status()
    await asyncio.sleep(random.uniform(1.0, 3.0))
    
    batch_state["status"] = "检测关键主题和优先级..."
    broadcast_global_batch_status()
    await asyncio.sleep(random.uniform(1.0, 2.0))
    
    # 并行处理所有任务
    task_coroutines = []
    for task in batch_state["tasks"]:
        coro = process_single_task(batch_id, task["task_id"], task["files"])
        task_coroutines.append(coro)
    
    # 使用gather并行运行所有任务
    await asyncio.gather(*task_coroutines)
    
    # 收集所有任务结果
    all_results = []
    for task in batch_state["tasks"]:
        if task.get("results"):
            all_results.extend(task["results"])
    
    # 保存批处理结果
    result_filename = f"batch_{batch_id}_results.json"
    result_path = os.path.join(RESULTS_DIR, result_filename)
    ckpt_path = os.path.join(SUSTAIN_DIR, "checkpoint.json")
    for new_task in all_results:
        CKPT_CONTENT["list"].append(new_task)
    with open(result_path, "w") as f:
        json.dump({
            "batch_id": batch_id,
            "total_emails": batch_state["total_emails"],
            "start_time": batch_state["start_time"],
            "end_time": time.time(),
            "tasks": [
                {
                    "task_id": t["task_id"],
                    "files": t["files"],
                    "results": t.get("results", [])
                }
                for t in batch_state["tasks"]
            ],
            "all_results": all_results
        }, f)
    with open(ckpt_path,"w",encoding="utf-8") as f:
        json.dump(CKPT_CONTENT,f,ensure_ascii=False)
    
    # 所有任务完成后
    batch_state["status"] = f"完成所有 {total_emails} 封邮件处理"
    batch_state["complete"] = True
    batch_state["end_time"] = time.time()
    batch_state["results_path"] = result_path
    batch_state["all_results"] = all_results
    is_processing = False
    
    # 将完成的批处理添加到已完成的批处理列表
    completed_batches[batch_id] = batch_state
    
    # 广播最终完成事件
    asyncio.create_task(broadcast_global_event("batch_complete", {
        "batch_id": batch_id,
        "total_emails": batch_state["total_emails"],
        "processing_time": batch_state["end_time"] - batch_state["start_time"],
        "results_available": True,
        "results_path": result_path
    }))
    
    # 5分钟后删除批处理任务状态
    await asyncio.sleep(RETENTION_MINUTES * 60)
    if batch_id in completed_batches:
        del completed_batches[batch_id]
        logger.info(f"批处理 {batch_id} 结果已过期删除")

async def cleanup_old_results():
    """清理旧的结果文件"""
    while True:
        try:
            now = time.time()
            for filename in os.listdir(RESULTS_DIR):
                filepath = os.path.join(RESULTS_DIR, filename)
                file_creation_time = os.path.getctime(filepath)
                if now - file_creation_time > RETENTION_MINUTES * 60:
                    os.remove(filepath)
                    logger.info(f"删除旧结果文件: {filename}")
            expired_batches = []
            for batch_id, state in completed_batches.items():
                if now - state.get("end_time", 0) > RETENTION_MINUTES * 60:
                    expired_batches.append(batch_id)
            
            for batch_id in expired_batches:
                del completed_batches[batch_id]
                logger.info(f"批处理 {batch_id} 结果已过期删除")
                
        except Exception as e:
            logger.error(f"清理错误: {str(e)}")
        
        await asyncio.sleep(3600)  # 每小时清理一次

async def check_and_process_queue():
    """检查并处理队列的定时任务"""
    global is_processing, last_upload_time
    
    while True:
        try:
            # 30秒无新上传且队列不为空时触发处理
            if (time.time() - last_upload_time > 30 and 
                file_processing_queue and 
                not is_processing):
                
                is_processing = True
                logger.info("开始处理队列中的邮件...")

                current_batch = file_processing_queue.copy()
                file_processing_queue.clear()
                
                # 创建新批处理任务
                batch_id = f"batch_{int(time.time())}"
                total_emails = len(current_batch)
                
                # 初始化批处理任务状态
                batch_jobs[batch_id] = {
                    "batch_id": batch_id,
                    "total_emails": total_emails,
                    "status": "准备开始",
                    "start_time": time.time(),
                    "complete": False,
                    "tasks": [],
                    "email_list":current_batch
                }
                
                # 启动处理管道
                asyncio.create_task(batch_processing_pipeline(batch_id))
                
        except Exception as e:
            logger.error(f"队列处理错误: {str(e)}")
        
        await asyncio.sleep(5)  # 每5秒检查一次

def load_ckpt():
    global CKPT_CONTENT,SUSTAIN_DIR
    ckpt_path = os.path.join(SUSTAIN_DIR, "checkpoint.json")
    try:
        with open(ckpt_path,"r",encoding="utf-8") as f:
            CKPT_CONTENT=json.load(f)
    except FileNotFoundError:
        with open(ckpt_path,"w",encoding="utf-8") as f:
            json.dump(CKPT_CONTENT,f,ensure_ascii=False)
    finally:
        print("loaded ckpt")
# 使用新的lifespan管理方式
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global CKPT_CONTENT, lock, async_lock
    CKPT_CONTENT={
        "list":[],
        "mail2id":{},
        "id2mail":{}
    }
    load_ckpt()
    lock = threading.Lock()
    async_lock = asyncio.Lock()
    # 初始化状态存储
    batch_jobs.clear()
    completed_batches.clear()
    file_processing_queue.clear()

    
    # 启动后台任务
    logger.info("应用启动: Ciallo～(∠・ω< )⌒★开始后台任务")
    asyncio.create_task(check_and_process_queue())
    asyncio.create_task(cleanup_old_results())
    
    yield  # 应用运行中
    
    # 清理资源
    logger.info("应用关闭: 清理资源")
    logger.info("Ciallo～(∠・ω< )⌒★ Bye")
    batch_jobs.clear()
    completed_batches.clear()
    file_processing_queue.clear()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# 使用lifespan创建FastAPI应用
app = FastAPI(lifespan=lifespan)
app.mount("/dist", StaticFiles(directory=os.path.join(BASE_DIR, 'auto_list/auto_list_frontend/dist')), name="dist")
app.mount("/assets", StaticFiles(directory=os.path.join(BASE_DIR, 'auto_list/auto_list_frontend/dist/assets')), name="assets")
@app.get("/")
def main():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_list_frontend/dist', 'index.html')
    html_content = ''
    with open(html_path) as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

# 允许所有来源的请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload-email/")
async def upload_email(file: UploadFile = File(...)):
    """接收并保存上传的邮件文件，添加到处理队列"""
    global last_upload_time
    
    # 更新最后上传时间
    last_upload_time = time.time()
    
    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid4().hex}{file_ext}"
    save_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # 保存文件
    try:
        with open(save_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 添加到处理队列
        file_processing_queue.append(unique_filename)
        await broadcast_global_event("file_uploaded", {
            "filename": unique_filename,
            "queue_size": len(file_processing_queue)
        })
        
        logger.info(f"新邮件上传: {unique_filename} (队列大小: {len(file_processing_queue)})")
        await broadcast_global_event("queue_updated", {
            "queue_size": len(file_processing_queue)
        })
        
        return {
            "status": "success", 
            "filename": unique_filename,
            "queue_size": len(file_processing_queue)
        }
    except Exception as e:
        logger.error(f"邮件上传错误: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket通信端点"""
    await manager.connect(websocket)
    logger.info(f"新WebSocket连接: {websocket.client}")
    try:
        # 当连接建立时立即发送当前状态
        broadcast_global_batch_status()
        
        # 保持连接打开
        while True:
            # 客户端可以发送心跳保持连接
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
            # 可以处理客户端消息（如果需要）
            # 例如：{"action": "get_status"}
    except WebSocketDisconnect:
        logger.info(f"WebSocket断开: {websocket.client}")
        manager.disconnect(websocket)

@app.get("/active-batches")
async def get_active_batches():
    """获取当前活动批处理列表"""
    return {
        "active_batches": [
            {
                "batch_id": batch_id,
                "status": state.get("status", ""),
                "total_emails": state.get("total_emails", 0),
                "start_time": state.get("start_time", 0),
                "tasks": [
                    {
                        "task_id": t["task_id"],
                        "status": t.get("status", ""),
                        "complete": t.get("complete", False),
                        "results_available": t.get("results") is not None
                    }
                    for t in state.get("tasks", [])
                ]
            }
            for batch_id, state in batch_jobs.items()
        ]
    }

@app.get("/batch/{batch_id}")
async def get_batch_results(batch_id: str):
    """获取批处理结果"""
    # 首先检查活动批处理
    if batch_id in batch_jobs:
        batch_state = batch_jobs[batch_id]
        return {
            "batch_id": batch_id,
            "status": batch_state.get("status", ""),
            "total_emails": batch_state.get("total_emails", 0),
            "start_time": batch_state.get("start_time", 0),
            "end_time": batch_state.get("end_time", None),
            "tasks": [
                {
                    "task_id": t["task_id"],
                    "files": t.get("files", []),
                    "status": t.get("status", ""),
                    "results": t.get("results", [])
                }
                for t in batch_state.get("tasks", [])
            ],
            "all_results": batch_state.get("all_results", [])
        }
    
    # 然后检查已完成批处理
    if batch_id in completed_batches:
        batch_state = completed_batches[batch_id]
        return {
            "batch_id": batch_id,
            "status": batch_state.get("status", ""),
            "total_emails": batch_state.get("total_emails", 0),
            "start_time": batch_state.get("start_time", 0),
            "end_time": batch_state.get("end_time", None),
            "tasks": [
                {
                    "task_id": t["task_id"],
                    "files": t.get("files", []),
                    "status": t.get("status", ""),
                    "results": t.get("results", [])
                }
                for t in batch_state.get("tasks", [])
            ],
            "all_results": batch_state.get("all_results", [])
        }
    
    return {"status": "not_found", "message": "批处理ID不存在或已过期"}

@app.get("/task/{task_id}")
async def get_task_results(task_id: str):
    """获取特定任务结果"""
    # 查找任务所在批处理
    for batch_id, batch_state in {**batch_jobs, **completed_batches}.items():
        for task in batch_state.get("tasks", []):
            if task["task_id"] == task_id:
                return {
                    "task_id": task_id,
                    "batch_id": batch_id,
                    "files": task.get("files", []),
                    "status": task.get("status", ""),
                    "results": task.get("results", []),
                    "start_time": task.get("start_time", 0),
                    "end_time": task.get("end_time", None)
                }
    
    # 尝试从结果文件加载
    result_filename = f"task_{task_id}_results.json"
    result_path = os.path.join(RESULTS_DIR, result_filename)
    if os.path.exists(result_path):
        try:
            with open(result_path, "r") as f:
                return json.load(f)
        except:
            pass
    
    return {"status": "not_found", "message": "任务ID不存在或结果已过期"}

@app.get("/queue-status")
async def get_queue_status():
    """获取当前队列状态"""
    return {
        "queue_size": len(file_processing_queue),
        "last_upload_time": last_upload_time,
        "is_processing": is_processing,
        "active_batches_count": len(batch_jobs),
        "completed_batches_count": len(completed_batches)
    }

@app.get("/list")
async def get_list():
    global CKPT_CONTENT
    return CKPT_CONTENT["list"]

@app.get("/email_reply/{msg_id}")
async def handle_email_reply(msg_id:str):
    global CKPT_CONTENT
    list_=CKPT_CONTENT["list"]
    target={}
    new_list=[]
    task_id=CKPT_CONTENT["mail2id"][msg_id]
    await broadcast_global_event("email_reply",{
        "task_id":task_id
    })
    for task in list_:
        if task["id"] == task_id:
            target=task
        else:
            new_list.append(task)
    if target != {}:
        print("get target")
        target["status"]="replied"
        new_list.append(target)
    
    CKPT_CONTENT["list"]=new_list

    return "OK"

@app.get("/task_complete/{task_id}")
async def handle_task_complete(task_id:str):
    global CKPT_CONTENT
    list_=CKPT_CONTENT["list"]
    target={}
    new_list=[]
    for task in list_:
        if task["id"] == task_id:
            target=task
        else:
            new_list.append(task)
    if target != {}:
        print("get target")
        target["status"]="replied"
        new_list.append(target)
    
    CKPT_CONTENT["list"]=new_list
    return {"code":0}

