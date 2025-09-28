"""
Example usage of the Conversation AI API endpoints
Run this after starting your FastAPI server
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"  # Change this to your server URL
# For Railway: BASE_URL = "https://gloss-backend-production.up.railway.app"

def test_conversation_api():
    """Test the conversation API endpoints"""
    print("🎮 Testing Gloss Conversation API")
    print("=" * 50)
    
    # Test 1: Check if conversation AI is available
    print("\n🔍 Checking API status...")
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API Status: {data['message']}")
        print(f"🤖 Conversation AI: {data.get('conversation_ai', 'unknown')}")
        if data.get('conversation_ai') == 'disabled':
            print("⚠️ Conversation AI is disabled (missing OPENAI_API_KEY)")
            return
    else:
        print(f"❌ API not available: {response.status_code}")
        return
    
    # Test 2: Get conversation examples
    print(f"\n📋 Getting conversation examples...")
    response = requests.get(f"{BASE_URL}/conversation/examples")
    if response.status_code == 200:
        examples = response.json()
        print("✅ Available examples:")
        for example in examples['examples']:
            print(f"  - {example['language']}: {example['description']}")
    
    # Test 3: Start a conversation
    print(f"\n🚀 Starting new conversation...")
    start_request = {
        "user_id": "demo-user-123",
        "language": "es",
        "custom_prompt": "I am an old man who will ask you how old you are"
    }
    
    response = requests.post(f"{BASE_URL}/conversation/start", json=start_request)
    if response.status_code == 200:
        conversation_data = response.json()
        conversation_id = conversation_data["conversation_id"]
        print(f"✅ Started conversation: {conversation_id}")
        print(f"🎭 Prompt: {conversation_data['custom_prompt']}")
    else:
        print(f"❌ Failed to start conversation: {response.status_code} - {response.text}")
        return
    
    # Test 4: Send test messages
    test_messages = [
        "Hola",
        "Tengo 25 años",  # Should validate positive
        "No te voy a decir mi edad",  # Should validate negative
        "¿Cuántos años tienes tú?"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n💬 Test {i}: Sending '{message}'")
        
        message_request = {
            "conversation_id": conversation_id,
            "message": message
        }
        
        response = requests.post(f"{BASE_URL}/conversation/message", json=message_request)
        if response.status_code == 200:
            data = response.json()
            print(f"🤖 Response: {data['message'][:100]}...")
            if data.get('validation_result'):
                validation = data['validation_result']
                print(f"✅ Validation: {validation['is_valid']} - {validation['reason']}")
            print(f"⚡ Processing Time: {data['processing_time_ms']}ms")
        else:
            print(f"❌ Failed to send message: {response.status_code} - {response.text}")
        
        time.sleep(1)  # Be nice to the API
    
    # Test 5: Get conversation history
    print(f"\n📚 Getting conversation history...")
    response = requests.get(f"{BASE_URL}/conversation/{conversation_id}/history")
    if response.status_code == 200:
        history = response.json()
        print(f"✅ History: {history['total_messages']} messages in {history['language']}")
        print(f"🎭 Prompt: {history['custom_prompt']}")
    else:
        print(f"❌ Failed to get history: {response.status_code}")
    
    # Test 6: End conversation
    print(f"\n🏁 Ending conversation...")
    response = requests.delete(f"{BASE_URL}/conversation/{conversation_id}")
    if response.status_code == 200:
        print("✅ Conversation ended successfully")
    else:
        print(f"❌ Failed to end conversation: {response.status_code}")
    
    print(f"\n🎉 API testing completed!")

if __name__ == "__main__":
    test_conversation_api()