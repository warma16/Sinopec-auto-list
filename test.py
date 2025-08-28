from preprocessor import preprocessor,compress_until_below_limit
import json
from typing import List,Dict
sys_prompt='''
{
  "system": "您是一台化工事件分析终端，处理邮件列表并输出风险看板,提取化工邮件中的超期/极速响应特征，按事务分区+紧急度降序输出,所有邮件必须分类并输出,只需要输出干净的json数据即可，我给你输入几封邮件，你就给我输出几封邮件",
  "input_format": [
    {
      "id": "邮件唯一标识",
      "title": "邮件标题",
      "content": "邮件正文"
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
    "structure": {
      "data": [
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
      ]
    },
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
    def __init__(self):
        global sys_prompt
        self.endpoint="https://api.siliconflow.cn/v1"
        self.api_key="sk-lnorkhqfcnakfdcxrnqkgbrrtcbcdycifofjhbrigvxqsvzw"
        self.client=OpenAI(
            base_url=self.endpoint,
            api_key=self.api_key
        )
    def call_llm(self,sys_prompt:str="",user_inputs:List[str]=[""],model:str="",stream:bool=False):
        print("calling llm",flush=True)
        msg=[]
        resp={
            "reasoning":"",
            "reply":""
        }
        if sys_prompt != "":
            msg.append({
                "role":"system",
                "content":sys_prompt
            })
        for usr_input in user_inputs:
            msg.append({
                "role":"user",
                "content":usr_input
            })
        print("hihihi")
        print(stream)
        response = self.client.chat.completions.create(
            # model='Pro/deepseek-ai/DeepSeek-R1',
            model=model,
            messages=msg,
            stream=stream
        )
        def generate(resp:Dict[str,str]):
            for chunk in response:
                content = chunk.choices[0].delta.content or ""
                reason=chunk.choices[0].delta.reasoning_content or ""
                resp["reply"]=content
                resp["reasoning"]=reason
                yield resp
            # 如果需要最终完整内容，可以额外yield一次
            # yield "".join(full_content)
        if stream:
            
            return generate(resp)
        else:
            resp["reply"]=response.choices[0].message.content
            resp["reasoning"]=response.choices[0].message.reasoning_content
            return resp

preprocessed=preprocessor("inbox_emails")
llm=LLM()
submit=compress_until_below_limit(preprocessed[:10],131072)
'''for idx in range(len(submit)):
    print(len(submit[idx]["content"]))
    if len(submit[idx]["content"]) >= 100000:
        print("检测到大文件，正在开始压缩")
        submit[idx]["content"]=process_industrial_document(submit[idx]["content"])["summary"]'''
print(len(submit))
respp=llm.call_llm(
    sys_prompt,
    user_inputs=[
        f"邮件数目：{len(submit)}\njson格式\n{json.dumps(submit,ensure_ascii=False)}"
    ],
    model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
)
print("思考过程")
print(respp["reasoning"])
print(respp["reply"])