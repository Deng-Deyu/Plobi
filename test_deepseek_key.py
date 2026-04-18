import openai
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 强制绕过系统代理
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"

# 从环境变量读取配置
api_key = os.getenv("DEEPSEEK_API_KEY")
api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")

if not api_key:
    print("❌ Error: DEEPSEEK_API_KEY not found in environment variables")
    print("Please create a .env file with your API key")
    exit(1)

print(f"Testing DeepSeek API Key: {api_key[:12]}...{api_key[-4:]}")
print(f"API Base: {api_base}")

# 创建客户端
client = openai.OpenAI(
    api_key=api_key,
    base_url=api_base
)

try:
    # 尝试一个简单的调用
    print("\nTesting API connection...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10,
        stream=False
    )
    print(f"✅ Success! Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {str(e)}")
    if hasattr(e, 'response') and e.response:
        print(f"Response status: {e.response.status_code}")
        try:
            print(f"Response body: {e.response.text}")
        except:
            pass