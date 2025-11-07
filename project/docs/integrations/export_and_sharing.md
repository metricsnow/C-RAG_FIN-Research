# Export and Sharing Functionality

## Overview

The Export and Sharing functionality (TASK-043) provides comprehensive capabilities for exporting conversation history to various formats and sharing conversations with others. This feature enables collaboration and documentation of research findings.

## Features

### Export Formats

The system supports exporting conversations to multiple formats:

1. **JSON** - Structured data format for programmatic access
2. **Markdown** - Human-readable format with formatting
3. **Plain Text (TXT)** - Simple text format
4. **PDF** - Professional document format with formatting
5. **Word (DOCX)** - Microsoft Word document format
6. **CSV** - Spreadsheet-compatible format for data analysis

### Sharing Features

- **Shareable Links** - Generate URLs that encode conversation data
- **Link Shortening** - Optional integration with shortening services (TinyURL, Bitly)
- **Batch Export** - Export multiple conversations at once

## Usage

### Exporting Conversations

#### Via Streamlit UI

1. Start a conversation in the chat interface
2. Click the "💾 Export" button
3. Select your desired format from the dropdown:
   - JSON
   - Markdown
   - TXT
   - PDF
   - Word (DOCX)
   - CSV
4. Click "📥 Download Export" to download the file

#### Via Python API

```python
from app.utils.conversation_export import export_conversation

messages = [
    {"role": "user", "content": "What is revenue?"},
    {"role": "assistant", "content": "Revenue is...", "sources": [...]},
]

# Export to JSON
content, filename = export_conversation(messages, "json", model="gpt-4o-mini")

# Export to PDF
pdf_content, pdf_filename = export_conversation(messages, "pdf", model="gpt-4o-mini")

# Export to Word
docx_content, docx_filename = export_conversation(messages, "docx", model="gpt-4o-mini")

# Export to CSV
csv_content, csv_filename = export_conversation(messages, "csv", model="gpt-4o-mini")
```

### Sharing Conversations

#### Via Streamlit UI

1. Start a conversation in the chat interface
2. Click the "🔗 Share" button
3. Copy the generated shareable link
4. Share the link with others

#### Via Python API

```python
from app.utils.sharing import create_shareable_conversation, generate_shareable_link

messages = [
    {"role": "user", "content": "What is revenue?"},
    {"role": "assistant", "content": "Revenue is..."},
]

# Generate shareable link
link = generate_shareable_link(
    messages,
    base_url="https://your-app.com",
    conversation_id="conv-123"
)

# Create shareable conversation with metadata
share_data = create_shareable_conversation(
    messages,
    base_url="https://your-app.com",
    shorten=True,  # Optional: shorten the link
    service="tinyurl"  # or "bitly"
)

print(f"Shareable link: {share_data['link']}")
if 'short_link' in share_data:
    print(f"Short link: {share_data['short_link']}")
```

### Batch Export

Export multiple conversations at once:

```python
from app.utils.conversation_export import batch_export_conversations

conversations = [
    {
        "messages": [...],
        "conversation_id": "conv-1",
        "model": "gpt-4o-mini"
    },
    {
        "messages": [...],
        "conversation_id": "conv-2",
        "model": "gpt-4o-mini"
    },
]

# Export all conversations to JSON
results = batch_export_conversations(conversations, "json")

for content, filename in results:
    # Save each exported conversation
    with open(filename, "w") as f:
        f.write(content)
```

## Export Format Details

### JSON Format

Structured format with metadata:

```json
{
  "conversation_id": "uuid",
  "created_at": "2025-01-27T10:00:00",
  "messages": [
    {
      "role": "user",
      "content": "Question",
      "timestamp": "2025-01-27T10:00:00"
    },
    {
      "role": "assistant",
      "content": "Answer",
      "sources": [...]
    }
  ],
  "metadata": {
    "model": "gpt-4o-mini",
    "total_messages": 2,
    "user_messages": 1,
    "assistant_messages": 1
  }
}
```

### Markdown Format

Human-readable format with headers and formatting:

```markdown
# Conversation Export
**Date:** 2025-01-27 10:00:00
**Model:** gpt-4o-mini
**Conversation ID:** abc12345

## Messages

### User
Question

---

### Assistant
Answer

**Source:** doc1.pdf

---
```

### CSV Format

Spreadsheet-compatible format with columns:

- Message Number
- Role
- Content
- Sources
- Timestamp
- Model
- Conversation ID

### PDF Format

Professional document with:
- Formatted headers and sections
- Proper page breaks
- Source citations
- Metadata header

### Word (DOCX) Format

Microsoft Word document with:
- Headings and paragraphs
- Source citations
- Metadata header
- Professional formatting

## Shareable Links

Shareable links encode conversation data in the URL using base64 encoding. The format is:

```
http://your-app.com/?share=<encoded_data>&id=<conversation_id>
```

### Link Shortening

The system supports optional link shortening via:

- **TinyURL** - No API key required (default)
- **Bitly** - Requires API key
- **Custom** - Can be extended with custom services

To use Bitly:

```python
from app.utils.sharing import shorten_link

short_url = shorten_link(
    long_url,
    service="bitly",
    api_key="your-bitly-api-key"
)
```

## Dependencies

### Required

- `reportlab>=4.0.0` - For PDF export
- `python-docx>=1.1.0` - For Word export

### Optional

- `requests` - For link shortening services

Install dependencies:

```bash
pip install reportlab python-docx
```

## Error Handling

The export functions handle errors gracefully:

- **Missing Libraries**: Raises `ImportError` with installation instructions
- **Empty Conversations**: Raises `ValueError` with clear message
- **Invalid Formats**: Raises `ValueError` with supported formats list
- **Encoding Errors**: Raises `ValueError` with error details

## Examples

### Export Single Conversation

```python
from app.utils.conversation_export import export_conversation

messages = [
    {"role": "user", "content": "What was Apple's revenue in 2023?"},
    {
        "role": "assistant",
        "content": "Apple's revenue in 2023 was...",
        "sources": [
            {"filename": "AAPL_10-K_2023.pdf"},
            {"filename": "AAPL_earnings_Q4_2023.pdf"}
        ]
    },
]

# Export to PDF
pdf_content, pdf_filename = export_conversation(
    messages,
    format_type="pdf",
    model="gpt-4o-mini",
    conversation_id="apple-revenue-2023"
)

# Save to file
with open(pdf_filename, "wb") as f:
    f.write(pdf_content)
```

### Share Conversation

```python
from app.utils.sharing import create_shareable_conversation

messages = [
    {"role": "user", "content": "What is AI?"},
    {"role": "assistant", "content": "AI is..."},
]

share_data = create_shareable_conversation(
    messages,
    base_url="https://research-assistant.example.com",
    shorten=True
)

print(f"Share this link: {share_data['link']}")
```

## Integration with Streamlit

The export and sharing features are fully integrated into the Streamlit UI:

1. **Export Button**: Located in the conversation management section
2. **Format Selection**: Dropdown to select export format
3. **Download Button**: Appears after export is generated
4. **Share Button**: Generates and displays shareable link
5. **Copy Link**: Button to copy shareable link to clipboard

## Best Practices

1. **Format Selection**:
   - Use JSON for programmatic access
   - Use Markdown for documentation
   - Use PDF for professional reports
   - Use Word for editing
   - Use CSV for data analysis

2. **Sharing**:
   - Shareable links contain full conversation data
   - Links can be long; consider shortening for user experience
   - Links are URL-safe encoded; can be shared via email, chat, etc.

3. **Batch Export**:
   - Use batch export for multiple conversations
   - Handle errors gracefully for individual conversations
   - Consider file size limits for large batches

## Limitations

1. **PDF/DOCX Libraries**: Must be installed separately
2. **Link Length**: Shareable links can be long; shortening recommended
3. **Link Shortening**: Requires network access and may have rate limits
4. **File Size**: Large conversations may result in large export files

## Future Enhancements

Potential future improvements:

- Email export functionality
- Scheduled exports
- Export templates
- Custom formatting options
- Integration with cloud storage (Google Drive, Dropbox)
- Export history tracking
- Share link expiration
- Password-protected shares

## Related Documentation

- [Conversation Memory](./langchain_memory.md) - Conversation history management
- [API Reference](../reference/api.md) - API endpoints for export
- [Configuration](../reference/configuration.md) - Configuration options
