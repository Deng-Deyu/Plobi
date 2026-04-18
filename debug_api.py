#!/usr/bin/env python
"""
Debug script to test DeepSeek API connection
"""
import os
import sys
import json
from pathlib import Path

# Force disable proxy
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"

print("=" * 60)
print("DeepSeek API Debug Test")
print("=" * 60)

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Try to import openai
try:
    import openai
    from openai import OpenAI
    print(f"[OK] OpenAI SDK available: {openai.__version__}")
except ImportError as e:
    print(f"[ERROR] OpenAI SDK not available: {e}")
    print("Please install: pip install openai")
    sys.exit(1)

# Load config
config_path = project_root / "config" / "models_config.json"
if not config_path.exists():
    print(f"[ERROR] Config file not found: {config_path}")
    sys.exit(1)

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Find DeepSeek model
deepseek_config = None
for model in config.get("models", []):
    if model.get("id") == "deepseek":
        deepseek_config = model
        break

if not deepseek_config:
    print("[ERROR] DeepSeek model config not found")
    sys.exit(1)

print(f"\n[CONFIG] DeepSeek Configuration:")
print(f"  ID: {deepseek_config.get('id')}")
print(f"  Name: {deepseek_config.get('name')}")
print(f"  Active: {deepseek_config.get('active', False)}")
api_key = deepseek_config.get("api_key", "")
api_base = deepseek_config.get("api_base", "")
print(f"  API Base: {api_base}")
print(f"  API Key: {api_key[:12]}...{api_key[-4:] if len(api_key) > 16 else ''}")
print(f"  Key length: {len(api_key)} chars")
print(f"  Default Model: {deepseek_config.get('default_model', 'deepseek-chat')}")

# Check if key looks valid
if not api_key:
    print("[ERROR] API key is empty!")
    sys.exit(1)

if not api_key.startswith("sk-"):
    print("[WARN]  API key doesn't start with 'sk-', may be invalid format")

# Test API connection
print(f"\n[TEST] Testing API connection...")
try:
    # Create client with custom HTTP client
    import httpx
    http_client = httpx.Client(
        timeout=120
    )

    client = OpenAI(
        api_key=api_key,
        base_url=api_base,
        http_client=http_client
    )

    print("[OK] OpenAI client created successfully")

    # Make a simple request
    response = client.chat.completions.create(
        model=deepseek_config.get("default_model", "deepseek-chat"),
        messages=[{"role": "user", "content": "Hello, just say 'OK' if you can hear me."}],
        max_tokens=10,
        temperature=0.1,
        stream=False
    )

    print(f"[OK] API request successful!")
    print(f"   Response: {response.choices[0].message.content}")
    print(f"   Model: {response.model}")
    print(f"   Usage: {response.usage}")

except openai.AuthenticationError as e:
    print(f"[ERROR] Authentication failed: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"   Status: {e.response.status_code}")
        try:
            error_body = e.response.json()
            print(f"   Error details: {json.dumps(error_body, indent=2)}")
        except:
            print(f"   Response text: {e.response.text[:200]}")

except openai.APIConnectionError as e:
    print(f"[ERROR] Connection failed: {e}")
    print(f"   This could be a network issue. Check your internet connection.")

except openai.APIError as e:
    print(f"[ERROR] API error: {e}")
    if hasattr(e, 'status_code'):
        print(f"   Status code: {e.status_code}")

except Exception as e:
    print(f"[ERROR] Unexpected error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Debug test completed")
print("=" * 60)