\# 🤖 Day 2 · 从 RAG 到智能体的跨越 —— 我与 DeepSeek 的第一次对话



> 学习记录 · AI Agent 学习计划  

> 作者：PeterPan  

> 日期：2025-10-17  



---



\## 🧭 今天我做了什么



在 Day 1 我只是做出了一个简单的 RAG（Retrieval-Augmented Generation）知识问答系统，  

它能检索知识库、然后回答问题。  

但今天，我真正\*\*理解了“Agent”是什么\*\*，并且亲手实现了一个\*\*规则驱动型智能体（Rule-based Agent）\*\*。



---



\## 🧠 从“检索”到“思考”的觉醒



在昨天，我的 RAG 系统逻辑是这样的：



```

用户问题 → 知识检索 → 总结输出

```



它只是“被动回答”，而不会思考“问题的目的是什么”。



而今天，我学到的真正的智能体逻辑是：



```

用户问题

&nbsp;→ 意图识别（Planner）

&nbsp;→ 决定使用哪个工具（Tool）

&nbsp;→ 执行任务并汇总结果（Executor）

&nbsp;→ 生成最终回答

```



也就是说，一个真正的 Agent \*\*会“想”\*\*：  

> “这是什么类型的问题？”  

> “我应该调用知识检索、还是分析函数？”  

> “如何组织结果让人类看懂？”



这种思考方式让我第一次感受到：  

> Agent 不是聊天机器人，而是能自主决策的思维系统。



---



\## 🔧 项目结构



```

ai\_agent\_day2/

│

├── main.py                # 主程序（规则驱动智能体）

├── requirements.txt        # 依赖库

├── .env.example            # DeepSeek Key 示例（不上传真实 key）

└── README.md               # 本文档

```



---



\## ⚙️ 安装与运行



\### 1️⃣ 克隆项目

```bash

git clone https://github.com/<你的用户名>/ai\_agent\_day2.git

cd ai\_agent\_day2

```



\### 2️⃣ 创建虚拟环境并安装依赖

```bash

python -m venv venv

venv\\Scripts\\activate      # Windows

pip install -r requirements.txt

```



\### 3️⃣ 配置 DeepSeek Key

在根目录新建 `.env` 文件：

```

OPENAI\_API\_KEY=你的\_DeepSeek\_API\_KEY

OPENAI\_API\_BASE=https://api.deepseek.com/v1

```



\### 4️⃣ 运行项目

```bash

python main.py

```



---



\## 💻 核心逻辑讲解



\### 🧩 1. 意图识别（Planner 雏形）



```python

def detect\_intent(user\_input: str) -> str:

&nbsp;   if re.search(r"(好不好|优缺点|值得买吗|评价|哪个好|对比)", user\_input):

&nbsp;       return "analysis"

&nbsp;   elif re.search(r"(是什么|定义|介绍|功能)", user\_input):

&nbsp;       return "fact"

&nbsp;   else:

&nbsp;       return "default"

```

这一部分相当于让智能体“理解任务类型”。



---



\### 🧰 2. 工具函数（Tools）



```python

def search\_knowledge(query: str):

&nbsp;   docs = {

&nbsp;       "百岁山": "百岁山是天然矿泉水品牌，强调‘天然好水’的理念。",

&nbsp;       "农夫山泉": "农夫山泉以‘我们不生产水，我们只是大自然的搬运工’为口号。"

&nbsp;   }

&nbsp;   return docs.get(query, "未找到相关资料。")



def compare\_products(p1, p2):

&nbsp;   return f"{p1}在品牌理念上更强调自然纯净，而{p2}注重市场传播与用户触达。"

```



在未来的 Agent 中，这部分可以扩展为：数据库调用、API 查询、数据分析等真实工具。



---



\### ⚙️ 3. 主控制逻辑（Executor）



```python

def agent\_response(user\_input):

&nbsp;   intent = detect\_intent(user\_input)

&nbsp;   print(f"✅ 识别意图：{intent}")



&nbsp;   if intent == "fact":

&nbsp;       product = user\_input.replace("是什么", "").strip()

&nbsp;       info = search\_knowledge(product)

&nbsp;       return f"{product}的简介如下：{info}"



&nbsp;   elif intent == "analysis":

&nbsp;       products = re.findall(r"(百岁山|农夫山泉|怡宝)", user\_input)

&nbsp;       if len(products) == 2:

&nbsp;           return compare\_products(products\[0], products\[1])

&nbsp;       else:

&nbsp;           return f"关于{products\[0]}的总体评价：口感纯净，定位较高端。"



&nbsp;   else:

&nbsp;       return default\_chain.invoke({"question": user\_input})

```



---



\## 🧩 输出示例



```

✅ 识别意图：fact

百岁山的简介如下：百岁山是天然矿泉水品牌，强调“天然好水”的品牌理念。



✅ 识别意图：analysis

百岁山在品牌理念上更强调自然纯净，而农夫山泉注重市场传播与用户触达。



✅ 识别意图：default

（DeepSeek 自由回答）

```



---



\## 🧠 我的成长与反思



> 在此之前，我以为智能体就是“能聊天 + 调知识库”。  

> 但今天我明白了：真正的 Agent，是会思考、会决策、会调用工具的系统。



从今天开始，我已经不仅仅是在“调用模型”，  

而是在“设计智能体的思维逻辑”。



---



\## 🔭 明日目标（Day 3 预告）



> 让模型接管意图识别部分，  

> 让 DeepSeek 自己推理、自己选择调用哪个工具 ——  

> 实现真正的「模型驱动智能体」。



---



\## ✨ 给后来者的建议



如果你也想试试，可以按照本文步骤亲手做出你的第一个智能体：  

1\. 先写一个简单的 RAG。  

2\. 再做一版规则驱动的 Agent。  

3\. 最后让模型自动规划任务。  



> 不要等“AI 成熟”后才上车，  

> 因为那时，你只能当乘客。🚀



