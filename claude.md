Claude API 使用说明
已支持原生 Claude API 请求方式。
BaseURL: https://api.oaipro.com，可参考官方文档(https://docs.anthropic.com/en/api/messages)使用。

也支持转成 OpenAI API 请求方式，可参考OpenAI官方文档(https://platform.openai.com/docs/api-reference/chat)格式。

费率跟官方完全一致，请参考：Anthropic API Pricing

API Key: 在令牌页面生成获取。在有些软件比如官方SDK，可通过参数设置，也可通过环境变量 OPENAI_API_KEY 设置。

BaseURL: https://api.oaipro.com/v1 在有些软件比如官方SDK，可通过参数设置，也可通过环境变量 OPENAI_API_BASE 设置。

在一些Chat客户端中，可直接输入API Key和BaseURL即可使用。

以下为python的使用示例：

claude_demo.py

from openai import OpenAI
 
if __name__ == '__main__':
    client = OpenAI(
        base_url='https://api.oaipro.com/v1',
        api_key='sk-xxx',
    )
 
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "hello",
            }
        ],
        model="claude-3-haiku-20240307",
    )
 
    print(chat_completion)
当前已支持 Thinking 可以通过两种方式使用：
直接自己设置相关参数，以下是一个curl示例：
claude_thinking.sh

curl https://api.oaipro.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-xxx" \
  -d '{
    "model": "claude-3-7-sonnet-20250219",
    "max_tokens": 4096,
    "thinking": {
        "type": "enabled",
        "budget_tokens": 1024
    },
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
thinking参数来自官方文档(https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking)，其中的budget_tokens不能低于1024，且不能大于max_tokens。

如果你希望使用超过8192的超大输出（128K），你可以设置anthropic-beta头为output-128k-2025-02-19，具体参考官方文档

这是一种灵活自定义的方式，对于开发者比较友好。

直接使用我们包裹的模型名claude-3-7-sonnet-20250219-thinking
claude_thinking.sh

curl https://api.oaipro.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-xxx" \
  -d '{
    "model": "claude-3-7-sonnet-20250219-thinking",
    "messages": [
      {
        "role": "user",
        "content": "Hello!"
      }
    ]
  }'
对于这个模型名，我们会自动处理以下内容：

会自动添加thinking参数，为max_tokens的50%。
如果你省略了max_tokens，会帮你设置成8192。
如果你指定的max_tokens超过64000，会自动帮你设置anthropic-beta这个头。
这个特有的模型名完全是为了兼容OpenAI的API格式，使它得以在绝大多数支持OpenAI格式的客户端使用。