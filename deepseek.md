推理模型 (deepseek-reasoner)
deepseek-reasoner 是 DeepSeek 推出的推理模型。在输出最终回答之前，模型会先输出一段思维链内容，以提升最终答案的准确性。我们的 API 向用户开放 deepseek-reasoner 思维链的内容，以供用户查看、展示、蒸馏使用。

在使用 deepseek-reasoner 时，请先升级 OpenAI SDK 以支持新参数。

pip3 install -U openai

API 参数
输入参数：

max_tokens：模型单次回答的最大长度（含思维连输出），默认为 32K，最大为 64K。
输出字段：

reasoning_content：思维链内容，与 content 同级，访问方法见访问样例。
content：最终回答内容。
上下文长度：API 最大支持 64K 上下文，输出的 reasoning_content 长度不计入 64K 上下文长度中。

支持的功能：Function Calling、Json Output、对话补全，对话前缀续写 (Beta)

不支持的功能：FIM 补全 (Beta)

不支持的参数：temperature、top_p、presence_penalty、frequency_penalty、logprobs、top_logprobs。请注意，为了兼容已有软件，设置 temperature、top_p、presence_penalty、frequency_penalty 参数不会报错，但也不会生效。设置 logprobs、top_logprobs 会报错。

上下文拼接
在每一轮对话过程中，模型会输出思维链内容（reasoning_content）和最终回答（content）。在下一轮对话中，之前轮输出的思维链内容不会被拼接到上下文中，如下图所示：


请注意，如果您在输入的 messages 序列中，传入了reasoning_content，API 会返回 400 错误。因此，请删除 API 响应中的 reasoning_content 字段，再发起 API 请求，方法如访问样例所示。

访问样例
下面的代码以 Python 语言为例，展示了如何访问思维链和最终回答，以及如何在多轮对话中进行上下文拼接。
非流式：
from openai import OpenAI
client = OpenAI(api_key="<DeepSeek API Key>", base_url="https://api.deepseek.com")

# Round 1
messages = [{"role": "user", "content": "9.11 and 9.8, which is greater?"}]
response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=messages
)

reasoning_content = response.choices[0].message.reasoning_content
content = response.choices[0].message.content

# Round 2
messages.append({'role': 'assistant', 'content': content})
messages.append({'role': 'user', 'content': "How many Rs are there in the word 'strawberry'?"})
response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=messages
)
# ...

流式：
from openai import OpenAI
client = OpenAI(api_key="<DeepSeek API Key>", base_url="https://api.deepseek.com")

# Round 1
messages = [{"role": "user", "content": "9.11 and 9.8, which is greater?"}]
response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=messages,
    stream=True
)

reasoning_content = ""
content = ""

for chunk in response:
    if chunk.choices[0].delta.reasoning_content:
        reasoning_content += chunk.choices[0].delta.reasoning_content
    else:
        content += chunk.choices[0].delta.content

# Round 2
messages.append({"role": "assistant", "content": content})
messages.append({'role': 'user', 'content': "How many Rs are there in the word 'strawberry'?"})
response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=messages,
    stream=True
)
# ...