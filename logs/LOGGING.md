# Usage logging system

## Overview
Simple logging system to track user interactions and app performance for development insights.

## What gets logged

- **Sessions**: New sessions with unique IDs
- **Searches**: Query text, filters, results count, processing time
- **Navigation**: Page transitions between search and document viewer
- **Document views**: Which documents are accessed and from where
- **Errors**: Application errors with context

## Log files

**Location**: `logs/usage.log`
**Format**: `timestamp | level | json_data`
**Rotation**: 5MB max, keeps 5 backup files

### Log structure
```json
{
  "session_id": "20250729_143025_123",
  "event_type": "search",
  "timestamp": "2025-07-29T14:30:25.123456",
  "details": {
    "query": "Can we use client data for R&D purposes?",
    "result_count": 5,
    "processing_time": 1.23
  }
}
```

## Usage analytics

### Running the analyzer
```bash
# All logs
python log_analyzer.py

# Last 7 days only
python log_analyzer.py --days 7
```

### Sample output
```
📊 Legal RAG usage report
==================================================

📈 Summary
Events: 156
Sessions: 23
Types: {'search': 67, 'navigation': 45, 'document_view': 34}

🔍 Searches
Total: 67
Success rate: 92.5%
Avg results: 4.2
Avg time: 1.45s
Top queries:
  • Can we use client data for development... (12x)
  • Are there AI restrictions in contracts... (8x)
```

## Privacy & security

- Query text truncated to 200 characters max
- No personal information logged
- Session IDs are generated, not linked to users
- Logs stored locally only

## Adding custom logging

```python
from utils.usage_logger import log_search, log_error, log_navigation

# Log a search
log_search(query="test query", result_count=5, processing_time=1.2)

# Log an error
log_error("validation_error", "Invalid query format")

# Log navigation
log_navigation("search", "document_viewer")
```

## File structure
```
ui_legal_rag/
├── utils/usage_logger.py    # Main logging utility
├── log_analyzer.py          # Analytics script
└── logs/                    # Log files (auto-created)
    ├── usage.log            # Current log
    └── usage.log.1          # Backup files
```

## Benefits

- User behavior insights
- Performance monitoring  
- Error tracking
- Feature usage analysis

**Status**: ✅ Fully implemented and integrated
