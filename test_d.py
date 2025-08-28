s='''
{
    "id": "9d2efa70388b4498aea573434d8ed32f.eml",
    "level": "1",
    "deadline": "2025-07-10",
    "riskLevel": "大",
    "reason": "冷却系统介质变更超期72小时（威胁停工）",
    "category": "工程进度",
    "theme": "danger",
    "name": "冷却系统设计变更冲突️"
  },
  {
    "id": "515c6a0b4a2a4b3ebfc3c4e742a80527.eml",
    "level": "1",
    "deadline": "2025-07-10",
    "riskLevel": "大",
    "reason": "存在3处技术参数矛盾及72小时超期审批节点",
    "category": "工程进度",
    "theme": "danger",
    "name": " glycol冷却系统核心设计争议"
  },
  {
    "id": "768673afa2f3482b8376f5158a9496c3.eml",
    "level": "2",
    "deadline": "今天到期",
    "riskLevel": "中",
    "reason": "PSA/动设备等130份超期技术文件待归档",
    "category": "文件报批",
    "theme": "warning",
    "name": "设备资料批量超期处理"
  },
  {
    "id": "09eb2a2c31954cc5908ed7479a650198.eml",
    "level": "1",
    "deadline": "2025-07-10",
    "riskLevel": "大",
    "reason": "冷却系统设计参数争议致进度延误超72h",
    "category": "工程进度",
    "theme": "danger",
    "name": " glycol系统交付冲突"
  },
  {
    "id": "9d2efa70388b4498aea573434d8ed32f.eml",
    "level": "1",
    "deadline": "2025-07-10",
    "riskLevel": "大",
    "reason": "存在3处技术参数矛盾及72小时超期审批节点",
    "category": "工程进度",
    "theme": "danger",
    "name": " glycol冷却系统核心设计争议"
  }
'''
import json
s=s.replace("  {","{")
s=s.replace("  }","}")
json.loads(s)