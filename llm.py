import json
from typing import List,Dict
from uuid import uuid4
from random import randint
from datetime import datetime
import time
sys_prompt='''
{
  "system": "您是一台化工事件分析终端，处理邮件列表并输出风险看板,提取化工邮件中的超期/极速响应特征，按事务分区+紧急度降序输出,所有邮件必须分类并输出,只需要输出干净的json数据即可",输出邮件的个数与我给你的要匹配上
  "input_format": [
    {
      "id": "邮件唯一标识",
      "title": "邮件标题",
      "content": "邮件正文",
      "send_date":"邮件发送日期"
    }
  ],
  "processing_rules": {
    "时间熔断机制": {
      "1级响应": ["半小时", "1小时内", "立即处置", "马上反馈"],
      "2级超期": ["今天到期", "超期罚款", "逾期停工", "限期整改"],
      "3级预警": ["本周截止", "施工期限", "验收节点"]
    },
    "分类标准": {
      "安全环保": ["泄漏", "爆炸", "应急预案", "环保处罚"],
      "工程进度": ["工期延误", "节点超期", "验收延期"],
      "文件报批": ["许可证到期", "环评超期", "安全证年审"],
      "生产运维": ["紧急停车", "工艺调整", "质检超时"],
      "日常事务": ["三会一课","员工体检等"]
    },
    "风险升级逻辑": [
      "含1级响应词 → 强制升为1级",
      "处罚金额>10万 → 自动升1级",
      "涉及政府检查 → 升1级",
      "你也可以根据语句以及内容进行自动升级",
      "风险等级的最基础的评估标准是结合发生的概率以及发生之后的影响综合考虑的"
    ]
  },
  "output_schema": {
    "format": "JSON",
    "structure":
      [
        {
          "id": "输入邮件ID",
          "level": "1-4级",
          "deadline": "截止日期",
          "riskLevel": "风险,你可以在[大,中,小]里面选择一个最恰当的输出",
          
          "reason": "分类依据关键词",
          "category": "这是什么类别，结果应该在在分类标准中",
          "theme":"在default,primary,success,warning,danger中选择，影响之后展示事件的颜色。default:灰色,primary:蓝色,success:绿色,warning:橙色,danger:红色",
          "name":"你觉得这个邮件背后的任务展现在看板上怎么说最合适，最好20个字以内"
        }
      ],
    "排序规则": [
      "1. 按分区固定顺序：安全环保>工程进度>文件报批>生产运维",
      "2. 分区内按：1级>2级>3级>4级",
      "3. 同等级按：即时响应>超期惩罚>期限预警"
    ]
  }
}

===邮件内容===
'''
from openai import OpenAI
class LLM:
    def __init__(self,endpoint,ak):
        global sys_prompt
        self.endpoint=endpoint
        self.api_key=ak
        self.client=OpenAI(
            base_url=self.endpoint,
            api_key=self.api_key
        )
    def call_llm(self,sys_prompt:str="",user_inputs:List[str]=[""],model:str=""):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("calling llm",flush=True)
        msg=[]
        resp={
            "reasoning":"",
            "reply":""
        }
        if sys_prompt != "":
            msg.append({
                "role":"system",
                "content":f"当前系统时间是:{current_time}\n"+sys_prompt
            })
        for usr_input in user_inputs:
            msg.append({
                "role":"user",
                "content":usr_input
            })
        print("hihihi")
        response = self.client.chat.completions.create(
            # model='Pro/deepseek-ai/DeepSeek-R1',
            model=model,
            messages=msg,
            response_format={
                'type': 'json_object'
            }
        )
        res=response.choices[0].message.content
        #print(res)
        #print("[" in res)
        if "[" not in res:
            print("detect [ missing")
            res="[\n"+str(res)
        if "]" not in res:
            print("detect ] missing")
            res=str(res)+"\n]"
        print(res)

        return res
    def call_llm_usr(self,sys_prompt:str="",user_inputs:List[str]=[""],model:str=""):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("calling llm",flush=True)
        msg=[]
        resp={
            "reasoning":"",
            "reply":""
        }
        usr_inp_str='\n'.join(user_inputs)
        if sys_prompt != "":
            msg.append({
                "role":"user",
                "content":f"当前系统时间是:{current_time}\n"+sys_prompt+f"\n{usr_inp_str}"
            })
        print("hihihi")
        response = self.client.chat.completions.create(
            # model='Pro/deepseek-ai/DeepSeek-R1',
            model=model,
            messages=msg
        )
        print(response.choices[0].message.content)
        return response.choices[0].message.content
    def gn_abstract(self,email_text:str=""):
        msg=[]
        msg.append({
            "role":"user",
            "content":f"[系统指令] 你是一台超导信息蒸馏机，请执行：\n1. 删除问候语/签名等冗余（原样保留关键数字和日期）\n2. 用3类标签标记内容：[需求][承诺][风险]\n3. 输出长度压缩至原文20% 但信息保留率＞95%\n[原文开始]{email_text}[原文结束]"
        })
        print("hihihi")
        response = self.client.chat.completions.create(
            # model='Pro/deepseek-ai/DeepSeek-R1',
            model="deepseek-chat",
            messages=msg,
        )
        return response.choices[0].message.content
    def test_mock_llm(self,sys_prompt,user_inputs,model,data):
        def gn_(io,_id):
            template={
                "id": f"{_id}",
                "level": f"{randint(1,4)}",
                "deadline": "年度更新",
                "riskLevel": f"{["低","中","高"][randint(0,2)]}",
                "reason": "系统版本老旧",
                "category": f"{["安全环保","工程进度","文件报批","生产运维","日常事务"][randint(0,4)]}",
                "theme": f"{["default","primary","success","warning","danger"][randint(0,4)]}",
                "name": f"事件-{io}"
            }
            return template
        
        test_data=[]
        i=0
        for task in data:
            print(task)
            id__=task["id"]
            mock_data=gn_(i,id__)
            test_data.append(mock_data)
            i+=1
        json_data={
            "data":test_data
        }
        time.sleep(10)
        return  json.dumps(json_data)
    def test_mock_abstract(self,email_text:str=""):
        return "曼涡栽灾休贡财道苗纹越迈支同剥举口命窝然迎珩幻惑丙将蔡七管就抗奇辣虾守瑟愚大逻换盾荒赖峡字肾虏喉磨俱。"