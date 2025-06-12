from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == '__main__':
    try:
        client = OpenAI(
            base_url='https://api.oaipro.com/v1',
            api_key=os.getenv('OPENAI_API_KEY'),
        )
        
        print("OpenAI客户端创建成功")
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "hello",
                }
            ],
            model="gpt-4o-mini",
        )
        
        print("API调用成功:")
        print(chat_completion.choices[0].message.content)
        
    except Exception as e:
        print(f"错误: {e}")
