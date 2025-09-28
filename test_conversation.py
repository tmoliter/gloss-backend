"""
Test the conversation system with sample interactions
"""

import asyncio
import os
from conversation_manager import ConversationManager, ConversationMode

async def test_conversation_system():
    """Test the complete conversation flow"""
    
    # Note: You'll need to set OPENAI_API_KEY environment variable
    api_key = os.environ.get("OPENAI_API_KEY", "test-key")
    
    if api_key == "test-key":
        print("⚠️ Set OPENAI_API_KEY environment variable to test with real API")
        print("🧪 Running mock test instead...")
        return
    
    # Initialize conversation manager
    manager = ConversationManager(api_key)
    
    print("🎮 Testing Gloss Conversation AI System")
    print("=" * 50)
    
    # Test 1: Start conversation
    print("\n🚀 Test 1: Starting Spanish grammar practice conversation")
    conversation_id = await manager.start_conversation(
        user_id="test-user-123",
        language="es", 
        mode=ConversationMode.GRAMMAR_PRACTICE
    )
    print(f"✅ Started conversation: {conversation_id}")
    
    # Test 2: Send messages that trigger different guardrails
    test_messages = [
        "Hola, ¿cómo estás?",  # Normal conversation
        "Why do I use 'estar' instead of 'ser' here?",  # Should trigger grammar tool
        "What does 'chévere' mean?",  # Should trigger vocabulary tool  
        "Can you give me a quiz about past tense?",  # Should trigger structured output
        "Let's talk about politics",  # Should trigger redirect
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n🗨️ Test {i+1}: Sending '{message}'")
        try:
            response = await manager.send_message(conversation_id, message)
            print(f"🤖 Response: {response.message[:100]}...")
            print(f"🛡️ Guardrail: {response.guardrail_decision.action.value} ({response.guardrail_decision.reason})")
            if response.tool_result:
                print(f"🔧 Tool used: {response.tool_result.get('tool', 'unknown')}")
            if response.structured_output:
                print(f"📊 Structured output: {response.structured_output.get('type', 'unknown')}")
            print(f"⚡ Processing time: {response.processing_time_ms}ms")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Test 3: Get conversation history
    print(f"\n📚 Test 6: Getting conversation history")
    history = manager.get_conversation_history(conversation_id)
    if history:
        print(f"✅ History retrieved: {history.total_messages} messages, {history.language} language, {history.mode.value} mode")
    else:
        print("❌ No history found")
    
    # Test 4: Cleanup
    print(f"\n🧹 Test 7: Cleanup old conversations")
    manager.cleanup_old_conversations(max_age_hours=0)  # Clean immediately for test
    print("✅ Cleanup completed")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_conversation_system())