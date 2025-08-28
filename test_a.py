from preprocessor import preprocessor,compress_until_below_limit
import json

preprocessed=preprocessor("inbox_emails")
submit=compress_until_below_limit(preprocessed,131072)
print(len(submit))
with open("demo.json","w",encoding="utf-8") as f:
    json.dump(submit,f,ensure_ascii=False)
