import os
import requests
from email.parser import BytesParser
from email.policy import default
from glob import glob
import time

# 配置信息
BASE_URL = "http://localhost:8000"  # 根据你的实际部署地址修改
UPLOAD_ENDPOINT = "/upload-email/"
DATASET_DIR = "datasets"  # 存放.eml文件的目录

def extract_email_metadata(eml_path):
    """提取邮件基本信息"""
    with open(eml_path, "rb") as f:
        msg = BytesParser(policy=default).parse(f)
    
    return {
        "subject": msg.get("Subject", "无主题"),
        "from": msg.get("From", "未知发件人"),
        "to": msg.get("To", "未知收件人"),
        "date": msg.get("Date", "未知日期"),
        "size": os.path.getsize(eml_path)
    }

def upload_email_files():
    """上传所有.eml文件到服务器"""
    eml_files = glob(os.path.join(DATASET_DIR, "*.eml"))
    
    print(f"找到 {len(eml_files)} 个邮件文件待上传:")
    
    for i, eml_path in enumerate(eml_files):
        metadata = extract_email_metadata(eml_path)
        print(f"[{i+1}/{len(eml_files)}] 上传: {metadata['subject']} ({metadata['size']}字节)")
        
        with open(eml_path, "rb") as f:
            response = requests.post(
                f"{BASE_URL}{UPLOAD_ENDPOINT}",
                files={"file": (os.path.basename(eml_path), f, "message/rfc822")}
            )
            
        if response.status_code == 200:
            result = response.json()
            print(f"  成功 → 保存为: {result['filename']}")
        else:
            print(f"  失败! 状态码: {response.status_code}")

if __name__ == "__main__":
    #time.sleep(60)
    upload_email_files()
    print("\n所有邮件上传完成!")