# TASK-025: Conversation History Management UI

## Task Information

| Field | Value |
|-------|-------|
| **Task ID** | TASK-025 |
| **Task Name** | Conversation History Management UI |
| **Priority** | Low |
| **Status** | Done |
| **Impact** | Low |
| **Created** | 2025-01-27 |
| **Related PRD** | Phase 1 - F8: Conversation Memory |
| **Dependencies** | TASK-024 (Conversation Memory Context Usage) |

---

## Objective

Add user interface features for managing conversation history in the Streamlit UI. This includes a clear conversation button, export functionality, and improved conversation history display. This complements TASK-024 by providing users control over conversation state.

---

## Background

**Current State:**
- Conversation history stored in `st.session_state.messages`
- History displayed in UI automatically
- No way to clear conversation
- No way to export conversation

**Required State:**
- Clear conversation button in UI
- Export conversation to file (JSON, Markdown, or TXT)
- Improved conversation history display
- Optional: Conversation history sidebar

---

## Technical Requirements

### Functional Requirements

1. **Clear Conversation Button**
   - Button in Streamlit UI to clear conversation history
   - Confirmation dialog before clearing (optional)
   - Reset `st.session_state.messages` to empty list
   - Maintain other session state (RAG system, tickers, etc.)

2. **Export Conversation**
   - Export conversation history to file
   - Support multiple formats:
     - JSON (structured data)
     - Markdown (readable format)
     - TXT (plain text)
   - Include metadata (timestamp, sources, model used)
   - Download via Streamlit download button

3. **Improved Conversation Display**
   - Better formatting for conversation history
   - Show timestamps for messages (optional)
   - Collapsible conversation sections (optional)
   - Better citation display

4. **Optional Features**
   - Conversation history sidebar
   - Conversation search/filter
   - Multiple conversation sessions

### Technical Specifications

**Files to Modify:**
- `app/ui/app.py` - Add clear button and export functionality
- `app/utils/` - Add conversation export utilities (new file)

**New Components:**
- `app/utils/conversation_export.py` - Export utilities
- Export functions for JSON, Markdown, TXT formats

**UI Components:**
- Clear conversation button (top of chat area)
- Export button (with format selector)
- Optional: Conversation history sidebar

---

## Acceptance Criteria

### Must Have

- [x] Clear conversation button in UI
- [x] Clear button resets conversation history
- [x] Export conversation to JSON format
- [x] Export conversation to Markdown format
- [x] Export conversation to TXT format
- [x] Export includes message content and sources
- [x] Export includes metadata (timestamps, model)
- [x] Download functionality via Streamlit
- [x] Existing functionality unaffected

### Should Have

- [x] Confirmation dialog before clearing
- [x] Export includes full conversation context
- [x] Export file naming includes date/time

### Nice to Have

- [ ] Conversation history sidebar
- [ ] Conversation search/filter
- [ ] Multiple conversation sessions
- [ ] Export formatting options

---

## Implementation Plan

### Phase 1: Clear Conversation Functionality
1. Add clear button to Streamlit UI
2. Implement clear function
3. Add confirmation dialog (optional)
4. Test clearing functionality

### Phase 2: Export Functionality
1. Create conversation export utility module
2. Implement JSON export
3. Implement Markdown export
4. Implement TXT export
5. Add export button to UI
6. Add format selector
7. Test export functionality

### Phase 3: UI Enhancements
1. Improve conversation display formatting
2. Add optional timestamps
3. Add optional conversation sidebar
4. Test UI improvements

### Phase 4: Testing
1. Unit tests for export functions
2. Integration tests for UI components
3. Test export file formats
4. Test clear functionality

---

## Technical Considerations

### Export Formats

**JSON Format:**
```json
{
  "conversation_id": "uuid",
  "created_at": "timestamp",
  "messages": [
    {
      "role": "user",
      "content": "...",
      "timestamp": "..."
    },
    {
      "role": "assistant",
      "content": "...",
      "sources": [...],
      "timestamp": "..."
    }
  ],
  "metadata": {
    "model": "gpt-4o-mini",
    "total_messages": 10
  }
}
```

**Markdown Format:**
```markdown
# Conversation Export
**Date:** 2025-01-27
**Model:** gpt-4o-mini

## Messages

### User
What is revenue?

### Assistant
Revenue is...

**Sources:** document1.txt, document2.txt
```

**TXT Format:**
```
Conversation Export
Date: 2025-01-27
Model: gpt-4o-mini

User: What is revenue?

Assistant: Revenue is...

Sources: document1.txt, document2.txt
```

### Streamlit Components

**Clear Button:**
- Use `st.button()` in sidebar or top of chat
- Confirmation with `st.dialog()` or simple checkbox

**Export Button:**
- Use `st.download_button()` for file download
- Format selector with `st.selectbox()`
- Generate file content on-demand

---

## Risk Assessment

### Technical Risks

1. **Risk:** Export file size for long conversations
   - **Probability:** Low
   - **Impact:** Low
   - **Mitigation:** Stream to file, limit export size

2. **Risk:** Breaking existing UI
   - **Probability:** Low
   - **Impact:** Medium
   - **Mitigation:** Careful UI placement, comprehensive testing

### User Experience Risks

1. **Risk:** Accidental conversation clearing
   - **Probability:** Medium
   - **Impact:** Medium
   - **Mitigation:** Confirmation dialog

---

## Testing Strategy

### Unit Tests
- Export function for each format
- Export file content validation
- Clear function testing

### Integration Tests
- UI button functionality
- Export download flow
- Clear conversation flow
- Session state preservation

### User Acceptance Tests
- Export formats are readable
- Clear functionality works as expected
- UI is intuitive

---

## Dependencies

**Internal:**
- TASK-024 (Conversation Memory Context Usage) - Required for full functionality

**External:**
- Streamlit download functionality
- JSON, Markdown, text file handling

---

## Success Metrics

- ✅ Clear conversation button functional
- ✅ Export to all three formats working
- ✅ Export files are readable and complete
- ✅ No breaking changes to existing UI
- ✅ User-friendly interface

---

## Notes

- This is a UX enhancement task
- Can be implemented independently of TASK-024 (basic clear/export)
- Full conversation context export requires TASK-024
- Consider Phase 2 for advanced features (multiple sessions, search)

---

**Next Task:** TASK-026 (Financial Domain Custom Embeddings)
