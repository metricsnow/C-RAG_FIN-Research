# LangChain Memory Integration

## Overview

The system includes LangChain-compatible conversation memory components for robust conversation management. This integration (TASK-031) provides a `ConversationBufferMemory`-like interface that seamlessly integrates with the RAG chain while maintaining compatibility with Streamlit's session state.

## Features

### Core Capabilities

- **LangChain-Compatible Interface**: Provides `ConversationBufferMemory`-like API for conversation management
- **Streamlit Integration**: Automatically syncs with Streamlit session state (`st.session_state.messages`)
- **Token-Aware Trimming**: Automatically trims conversation history based on token limits and message count
- **Memory Statistics**: Real-time statistics display in UI (message count, token count, limits)
- **Backward Compatible**: Falls back to legacy conversation memory if disabled

### Components

1. **StreamlitChatMessageHistory**: LangChain-compatible chat message history that uses Streamlit session state
2. **ConversationBufferMemory**: Conversation buffer memory with token-aware trimming and context management

## Configuration

### Environment Variables

```bash
# Enable LangChain memory (default: true)
CONVERSATION_USE_LANGCHAIN_MEMORY=true

# Configure memory limits
CONVERSATION_MAX_TOKENS=2000      # Maximum tokens for conversation context
CONVERSATION_MAX_HISTORY=10       # Maximum number of messages to include
```

### Configuration Options

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CONVERSATION_USE_LANGCHAIN_MEMORY` | boolean | `true` | Use LangChain memory components |
| `CONVERSATION_MAX_TOKENS` | integer | `2000` | Maximum tokens for conversation context |
| `CONVERSATION_MAX_HISTORY` | integer | `10` | Maximum number of messages to include |

## Usage

### Automatic Integration

LangChain memory is automatically integrated with the RAG query system. When enabled:

1. **Memory Initialization**: Memory is created when `RAGQuerySystem` is initialized
2. **History Loading**: Conversation history from Streamlit session state is loaded into memory on each query
3. **Context Inclusion**: Memory variables are loaded and included in the prompt
4. **Response Saving**: User queries and AI responses are automatically saved to memory

### Manual Usage

```python
from app.utils.langchain_memory import ConversationBufferMemory, StreamlitChatMessageHistory

# Create memory instance
memory = ConversationBufferMemory(
    max_token_limit=2000,
    max_history=10
)

# Save conversation context
memory.save_context(
    inputs={"input": "What is AI?"},
    outputs={"output": "AI is artificial intelligence."}
)

# Load memory variables for prompt
memory_vars = memory.load_memory_variables({})
history = memory_vars["history"]  # Formatted conversation history

# Get memory statistics
stats = memory.get_memory_stats()
print(f"Messages: {stats['message_count']}, Tokens: {stats['token_count']}")

# Clear memory
memory.clear()
```

### Integration with Streamlit

```python
import streamlit as st
from app.utils.langchain_memory import StreamlitChatMessageHistory, ConversationBufferMemory

# Initialize memory with Streamlit messages
if "messages" not in st.session_state:
    st.session_state.messages = []

# Create memory from Streamlit session state
chat_history = StreamlitChatMessageHistory(messages=st.session_state.messages)
memory = ConversationBufferMemory(chat_memory=chat_history)

# Use memory in RAG system
from app.rag.chain import RAGQuerySystem
rag_system = RAGQuerySystem(memory=memory)
```

## Memory Management

### Automatic Trimming

Memory automatically trims conversation history when limits are exceeded:

- **Token Limit**: Trims messages when total tokens exceed `CONVERSATION_MAX_TOKENS`
- **History Limit**: Trims messages when message count exceeds `CONVERSATION_MAX_HISTORY`
- **Priority**: Recent messages are prioritized over older ones when trimming

### Memory Statistics

Get real-time memory statistics:

```python
stats = memory.get_memory_stats()
# Returns:
# {
#     "message_count": 6,
#     "token_count": 1234,
#     "max_tokens": 2000,
#     "max_history": 10,
#     "user_messages": 3,
#     "assistant_messages": 3
# }
```

## UI Features

### Memory Status Display

The Streamlit UI displays memory statistics:
- Message count
- Token count
- Maximum tokens and history limits

### Clear Conversation

The "Clear Conversation" button:
- Clears Streamlit session state messages
- Clears LangChain memory
- Requires confirmation to prevent accidental loss

## Architecture

### Component Structure

```
StreamlitChatMessageHistory
├── Stores messages in LangChain format (HumanMessage, AIMessage)
├── Converts to/from Streamlit message dictionaries
└── Provides LangChain BaseChatMessageHistory interface

ConversationBufferMemory
├── Manages conversation history with token-aware trimming
├── Provides save_context() and load_memory_variables() methods
├── Integrates with StreamlitChatMessageHistory
└── Returns formatted history for prompt inclusion
```

### Integration Flow

1. **Query Initiation**: User submits query via Streamlit UI
2. **History Loading**: Conversation history from `st.session_state.messages` loaded into memory
3. **Memory Variables**: Memory variables loaded and formatted for prompt
4. **RAG Query**: Query processed with conversation context included
5. **Response Saving**: User query and AI response saved to memory
6. **UI Update**: Memory statistics displayed in UI

## Backward Compatibility

The system maintains backward compatibility:

- **Legacy Mode**: If `CONVERSATION_USE_LANGCHAIN_MEMORY=false`, uses original conversation memory
- **Graceful Fallback**: Automatically falls back if LangChain memory fails
- **Same Interface**: Both modes provide the same user experience

## Testing

Comprehensive unit tests cover:

- StreamlitChatMessageHistory functionality
- ConversationBufferMemory operations
- Memory trimming (by tokens and history)
- Memory statistics
- Integration scenarios

Run tests:
```bash
pytest tests/test_langchain_memory.py -v
```

## Performance

- **Memory Overhead**: Minimal (< 5% additional overhead)
- **Token Counting**: Efficient with caching
- **Trimming**: Fast O(n) operation where n is message count
- **Synchronization**: Automatic sync with Streamlit session state

## Troubleshooting

### Memory Not Clearing

If memory doesn't clear when using "Clear Conversation":
- Ensure `rag_system.memory` exists and is not None
- Check that memory.clear() is called in UI clear handler
- Verify Streamlit session state is cleared

### Memory Not Persisting

If conversation history doesn't persist:
- Verify `CONVERSATION_USE_LANGCHAIN_MEMORY=true`
- Check that conversation_history is passed to `rag_system.query()`
- Ensure Streamlit session state is maintained

### Token Limit Exceeded

If context window overflow occurs:
- Increase `CONVERSATION_MAX_TOKENS`
- Decrease `CONVERSATION_MAX_HISTORY`
- Check token counting accuracy

## Related Documentation

- [Configuration Guide](configuration.md) - Environment variable configuration
- [API Documentation](api.md) - API endpoints for conversation memory
- [Testing Guide](testing.md) - Testing conversation memory

## Implementation Details

### Files

- `app/utils/langchain_memory.py` - LangChain memory components (123 lines, 91% test coverage)
- `app/rag/chain.py` - RAG chain integration with memory
- `app/ui/app.py` - UI integration with memory status display

### Dependencies

- `langchain-core` - LangChain core message types
- `tiktoken` - Token counting
- `streamlit` - Session state management

## Future Enhancements

Potential future improvements:

- **ConversationSummaryMemory**: For very long conversations (summarizes older messages)
- **Memory Persistence**: Save conversation history to database
- **Multiple Sessions**: Support for multiple conversation sessions per user
- **Memory Search**: Search through conversation history
- **Memory Import/Export**: Import/export conversation history
