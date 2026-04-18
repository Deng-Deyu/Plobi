#!/usr/bin/env python
"""
Test LLM Engine directly
"""
import os
import sys
from pathlib import Path

# Force disable proxy
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1"

print("=" * 60)
print("LLM Engine Test")
print("=" * 60)

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from core.llm_engine import get_llm_engine, LLMEngine

# Create engine
print("Creating LLM engine...")
engine = get_llm_engine()

print(f"Models config loaded: {len(engine.models_config.get('models', []))} models")
print(f"Agents config loaded: {len(engine.agents_config.get('agents', []))} agents")

# Check DeepSeek model config
deepseek_config = engine.get_model_config("deepseek")
if deepseek_config:
    print(f"\nDeepSeek model config:")
    print(f"  ID: {deepseek_config.get('id')}")
    print(f"  Name: {deepseek_config.get('name')}")
    print(f"  Active: {deepseek_config.get('active', False)}")
    print(f"  API Key: {deepseek_config.get('api_key', '')[:12]}...")
    print(f"  Default Model: {deepseek_config.get('default_model', 'deepseek-chat')}")
else:
    print("\n[ERROR] DeepSeek model config not found!")
    sys.exit(1)

# Check agent mapping
agent_id = "assistant"
model_id = engine.get_agent_model_id(agent_id)
print(f"\nAgent '{agent_id}' uses model: {model_id}")

# Clear any cached clients
print("\nClearing any cached clients...")
engine.clear_model_cache()

# Test generating a response
print(f"\nTesting generate_stream for agent '{agent_id}'...")
try:
    # Get generator
    generator = engine.generate_stream(
        agent_id=agent_id,
        message="Hello, just say 'OK' if you can hear me.",
        history=None,
        temperature=0.1,
        max_tokens=10
    )

    # Collect response
    response_parts = []
    for chunk in generator:
        response_parts.append(chunk)
        print(f"  Chunk: {repr(chunk)}")

    full_response = "".join(response_parts)
    print(f"\nFull response: {repr(full_response)}")

    if "❌" in full_response or "错误" in full_response:
        print("[ERROR] LLM engine returned an error")
    else:
        print("[OK] LLM engine call successful")

except Exception as e:
    print(f"[ERROR] Exception during generate_stream: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test completed")
print("=" * 60)