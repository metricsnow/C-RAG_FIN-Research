# TASK-027: Document Source Management UI

## Task Information

| Field | Value |
|-------|-------|
| **Task ID** | TASK-027 |
| **Task Name** | Document Source Management UI |
| **Priority** | Medium |
| **Status** | Waiting |
| **Impact** | Medium |
| **Created** | 2025-01-27 |
| **Related PRD** | Phase 1 - F10: Document Source Management |
| **Dependencies** | TASK-005 (ChromaDB), TASK-008 (Streamlit UI) |

---

## Objective

Implement a user interface for managing document sources in the vector database. This includes listing all indexed documents, viewing document metadata, deleting documents, and searching documents by metadata. Currently, document management is only possible via code/direct ChromaDB access.

---

## Background

**Current State:**
- Documents indexed in ChromaDB
- No UI for document management
- No way to list documents
- No way to delete documents via UI
- No way to view document metadata
- No way to search documents by metadata

**Required State:**
- UI for listing all indexed documents
- View document metadata and statistics
- Delete documents from vector database
- Search documents by metadata (ticker, form type, date, etc.)
- Re-index documents (optional, Phase 2)

---

## Technical Requirements

### Functional Requirements

1. **Document Listing**
   - List all indexed documents in UI
   - Display document metadata (filename, ticker, form type, date, chunk count)
   - Pagination for large document lists
   - Sort/filter options

2. **Document Details View**
   - View detailed metadata for selected document
   - Show chunk count and statistics
   - Display source information
   - Show indexing date/time

3. **Document Deletion**
   - Delete individual documents
   - Delete multiple documents (bulk)
   - Confirmation dialog before deletion
   - Update UI after deletion

4. **Document Search**
   - Search by ticker symbol
   - Search by form type (10-K, 10-Q, 8-K)
   - Search by date range
   - Search by filename
   - Filter by metadata fields

5. **Document Statistics**
   - Total document count
   - Documents by ticker
   - Documents by form type
   - Chunk statistics
   - Storage statistics

### Technical Specifications

**Files to Create:**
- `app/ui/document_management.py` - Document management UI components
- `app/utils/document_manager.py` - Document management utilities

**Files to Modify:**
- `app/ui/app.py` - Add document management section/tab
- `app/vector_db/chroma_store.py` - Add document deletion methods (if needed)

**UI Components:**
- Document list table
- Document details modal/page
- Search/filter sidebar
- Delete confirmation dialog
- Statistics dashboard

**ChromaDB Operations:**
- Query all documents with metadata
- Delete documents by ID or metadata filter
- Count documents by metadata
- Search documents by metadata

---

## Acceptance Criteria

### Must Have

- [ ] List all indexed documents in UI
- [ ] Display document metadata (filename, ticker, form type, date)
- [ ] View document details (metadata, chunk count, statistics)
- [ ] Delete individual documents
- [ ] Confirmation dialog before deletion
- [ ] Search documents by ticker
- [ ] Search documents by form type
- [ ] Filter documents by metadata
- [ ] Document statistics display
- [ ] UI updates after document deletion

### Should Have

- [ ] Bulk delete functionality
- [ ] Pagination for document list
- [ ] Sort options (by date, ticker, form type)
- [ ] Export document list (optional)
- [ ] Document count statistics

### Nice to Have

- [ ] Re-index documents functionality
- [ ] Document preview
- [ ] Advanced search (date range, multiple filters)
- [ ] Document tagging/categorization

---

## Implementation Plan

### Phase 1: Document Listing and Display
1. Create document management UI component
2. Implement document listing from ChromaDB
3. Display documents in table format
4. Add pagination for large lists
5. Add sort/filter functionality

### Phase 2: Document Details and Search
1. Implement document details view
2. Add search functionality (ticker, form type)
3. Add metadata filtering
4. Implement statistics display

### Phase 3: Document Deletion
1. Implement single document deletion
2. Add confirmation dialog
3. Implement bulk deletion (optional)
4. Update UI after deletion
5. Handle deletion errors gracefully

### Phase 4: UI Integration
1. Add document management section to Streamlit UI
2. Add navigation/tabs for document management
3. Integrate with existing UI layout
4. Test UI integration

### Phase 5: Testing
1. Unit tests for document management utilities
2. Integration tests for UI components
3. Test document deletion functionality
4. Test search and filtering
5. Test error handling

---

## Technical Considerations

### ChromaDB Document Operations

**Listing Documents:**
- Use `ChromaStore.get_all()` to retrieve all documents
- Filter by metadata using `where` parameter
- Sort and paginate results in Python

**Deleting Documents:**
- Use `ChromaStore.collection.delete()` with document IDs
- Support metadata-based deletion (delete by ticker, form type)
- Handle deletion errors (missing documents, etc.)

**Document Search:**
- Query ChromaDB with metadata filters
- Support multiple filter criteria
- Efficient search with indexing

### UI Design

**Layout Options:**

1. **Tab-based Navigation**
   - Main tab: Chat interface
   - Documents tab: Document management
   - Simple, clean separation

2. **Sidebar Section**
   - Document management in sidebar
   - Expandable section
   - Always accessible

3. **Modal/Dialog**
   - Document management in modal
   - Opens from main UI
   - Less intrusive

**Recommendation:** Tab-based navigation for better organization

### Document Metadata Display

**Key Metadata Fields:**
- Filename
- Ticker symbol
- Company name
- Form type (10-K, 10-Q, 8-K)
- Filing date
- Chunk count
- Indexing date
- Source path

**Statistics:**
- Total documents
- Documents by ticker
- Documents by form type
- Total chunks
- Storage size (if available)

---

## Risk Assessment

### Technical Risks

1. **Risk:** Performance issues with large document lists
   - **Probability:** Medium
   - **Impact:** Medium
   - **Mitigation:** Pagination, lazy loading, efficient queries

2. **Risk:** Accidental document deletion
   - **Probability:** Medium
   - **Impact:** High
   - **Mitigation:** Confirmation dialog, undo functionality (optional)

3. **Risk:** ChromaDB deletion limitations
   - **Probability:** Low
   - **Impact:** Medium
   - **Mitigation:** Test deletion operations, handle errors gracefully

### User Experience Risks

1. **Risk:** Complex UI for document management
   - **Probability:** Low
   - **Impact:** Low
   - **Mitigation:** Simple, intuitive interface design

---

## Testing Strategy

### Unit Tests
- Document listing functionality
- Document search/filter
- Document deletion
- Metadata extraction

### Integration Tests
- UI component integration
- ChromaDB operations
- Error handling
- UI updates after operations

### User Acceptance Tests
- Document management is intuitive
- Search works as expected
- Deletion is safe and reversible (with confirmation)
- Statistics are accurate

---

## Dependencies

**Internal:**
- TASK-005 (ChromaDB) - ✅ Complete
- TASK-008 (Streamlit UI) - ✅ Complete

**External:**
- ChromaDB deletion operations
- Streamlit UI components

---

## Success Metrics

- ✅ All documents can be listed and viewed
- ✅ Document search and filtering functional
- ✅ Document deletion works safely
- ✅ Statistics are accurate
- ✅ UI is intuitive and responsive
- ✅ No data loss or corruption

---

## Notes

- This is a P1 (Should Have) feature
- Critical for production document management
- Can be implemented incrementally
- Consider Phase 2 for advanced features (re-indexing, preview, tagging)
- Document deletion is permanent - ensure confirmation dialogs

---

**End of Missing Features Tasks**
