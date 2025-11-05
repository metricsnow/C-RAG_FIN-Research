# TASK-024: Conversation Memory - Context Usage in Queries

## Task Information

| Field | Value |
|-------|-------|
| **Task ID** | TASK-024 |
| **Task Name** | Conversation Memory - Context Usage in Queries |
| **Priority** | Medium |
| **Status** | Waiting |
| **Impact** | Medium |
| **Created** | 2025-01-27 |
| **Related PRD** | Phase 1 - F8: Conversation Memory (Partial) |
| **Dependencies** | TASK-007 (RAG Query System), TASK-008 (Streamlit UI) |

---

## Objective

Complete the conversation memory implementation by integrating conversation context into RAG queries. Currently, chat history is stored in Streamlit session state but not used when processing queries. This task will add conversation context to the RAG query system so follow-up questions can reference previous conversation.

---

## Background

**Current State:**
- Chat history is stored in `st.session_state.messages` in Streamlit UI
- Conversation history is displayed in the UI
- Messages persist across interactions in the same session
- **Gap:** RAG system processes each query independently without using conversation history

**Required State:**
- Conversation context included in subsequent queries
- Follow-up questions maintain context from previous messages
- Context window management to prevent token overflow
- Backward compatible with existing single-query functionality

---

## Technical Requirements

### Functional Requirements

1. **Conversation Context Integration**
   - Modify `RAGQuerySystem.query()` to accept optional conversation history
   - Include recent conversation messages in prompt context
   - Maintain conversation context across multiple queries in same session

2. **Context Window Management**
   - Implement token counting for conversation context
   - Limit conversation history to prevent exceeding LLM context window
   - Prioritize recent messages over older ones
   - Configurable context window size

3. **Prompt Enhancement**
   - Update prompt template to include conversation history
   - Format conversation history appropriately for LLM
   - Maintain financial domain optimization in prompts

4. **UI Integration**
   - Pass conversation history from Streamlit UI to RAG system
   - Maintain existing single-query functionality as fallback
   - No breaking changes to existing API

### Technical Specifications

**Files to Modify:**
- `app/rag/chain.py` - Add conversation context to query method
- `app/ui/app.py` - Pass conversation history to RAG system
- `app/utils/config.py` - Add context window configuration

**LangChain Components:**
- Use `ConversationBufferMemory` or `ConversationSummaryMemory` from LangChain
- Implement token counting using `tiktoken` or LangChain token counter
- Integrate with existing RAG chain structure

**Configuration:**
- `CONVERSATION_MAX_TOKENS`: Maximum tokens for conversation context (default: 2000)
- `CONVERSATION_MAX_HISTORY`: Maximum number of previous messages to include (default: 10)
- `CONVERSATION_ENABLED`: Enable/disable conversation memory (default: true)

---

## Acceptance Criteria

### Must Have

- [ ] `RAGQuerySystem.query()` accepts optional `conversation_history` parameter
- [ ] Conversation history included in prompt when provided
- [ ] Follow-up questions maintain context from previous messages
- [ ] Token counting implemented to prevent context window overflow
- [ ] Recent messages prioritized over older ones
- [ ] Backward compatible: single queries work without conversation history
- [ ] Streamlit UI passes conversation history to RAG system
- [ ] Existing tests pass without modification
- [ ] New tests added for conversation context functionality

### Should Have

- [ ] Configurable context window size via environment variables
- [ ] Conversation summary option for long conversations
- [ ] Performance impact < 10% compared to single-query mode

### Nice to Have

- [ ] Conversation history persistence across sessions (optional)
- [ ] Context compression for very long conversations

---

## Implementation Plan

### Phase 1: Core Context Integration
1. Add conversation history parameter to `RAGQuerySystem.query()`
2. Implement token counting utility
3. Update prompt template to include conversation context
4. Modify RAG chain to accept conversation history

### Phase 2: Context Window Management
1. Implement token limit checking
2. Add message prioritization (recent first)
3. Add conversation summary option for long histories
4. Add configuration options

### Phase 3: UI Integration
1. Update Streamlit UI to pass conversation history
2. Maintain backward compatibility
3. Add conversation context toggle (optional)

### Phase 4: Testing
1. Unit tests for conversation context integration
2. Integration tests for multi-turn conversations
3. Performance tests for context window management
4. Regression tests for single-query functionality

---

## Technical Considerations

### LangChain Memory Components

**Option 1: ConversationBufferMemory**
- Stores all messages in buffer
- Simple implementation
- May exceed context window with long conversations

**Option 2: ConversationSummaryMemory**
- Summarizes older messages
- Better for long conversations
- Requires additional LLM call for summarization

**Recommendation:** Start with `ConversationBufferMemory`, add `ConversationSummaryMemory` as enhancement if needed.

### Token Counting

**Approach:**
- Use `tiktoken` for accurate token counting (OpenAI models)
- Use LangChain token counter for Ollama models
- Count tokens before including in prompt
- Truncate or summarize if exceeding limit

### Prompt Engineering

**Format:**
```
Previous conversation:
- User: [previous question]
- Assistant: [previous answer]

Current question: {question}
```

**Considerations:**
- Maintain financial domain optimization
- Keep prompt concise to preserve context for retrieved documents
- Balance conversation context vs. document context

---

## Risk Assessment

### Technical Risks

1. **Risk:** Context window overflow
   - **Probability:** Medium
   - **Impact:** High
   - **Mitigation:** Implement token counting and limits

2. **Risk:** Performance degradation
   - **Probability:** Low
   - **Impact:** Medium
   - **Mitigation:** Efficient context formatting, caching

3. **Risk:** Breaking existing functionality
   - **Probability:** Low
   - **Impact:** High
   - **Mitigation:** Maintain backward compatibility, comprehensive testing

### Dependency Risks

1. **Risk:** LangChain memory components compatibility
   - **Probability:** Low
   - **Impact:** Medium
   - **Mitigation:** Test with current LangChain version, check compatibility

---

## Testing Strategy

### Unit Tests
- Conversation context formatting
- Token counting accuracy
- Context window limit enforcement
- Message prioritization logic

### Integration Tests
- Multi-turn conversation flows
- Context preservation across queries
- Backward compatibility with single queries
- Error handling for context overflow

### Performance Tests
- Response time with conversation context
- Memory usage with conversation history
- Token counting performance

---

## Dependencies

**Internal:**
- TASK-007 (RAG Query System) - ✅ Complete
- TASK-008 (Streamlit UI) - ✅ Complete

**External:**
- LangChain memory components
- `tiktoken` for token counting (OpenAI)
- LangChain token counter utilities

---

## Success Metrics

- ✅ Conversation context included in queries
- ✅ Follow-up questions maintain context
- ✅ Token limits enforced
- ✅ No performance degradation (< 10% overhead)
- ✅ All existing tests pass
- ✅ New tests achieve >80% coverage for conversation features

---

## Notes

- This task completes the partial F8 implementation
- Maintains backward compatibility as critical requirement
- Can be enhanced with conversation summarization in future task
- Consider Phase 2 for persistent conversation history

---

**Next Task:** TASK-025 (Conversation History Management UI)
