# CLAUDE.md - Development Workflow Guide

## 🎯 Project Overview
**SHA Website Crawler** is a Flask-based tender monitoring application that helps organizations quickly discover business opportunities by crawling multiple tender websites simultaneously to search for specific keywords. Currently deployed on Render (https://render.com/), the system enables rapid identification of relevant tenders as they are posted online. The application uses concurrent processing, respects robots.txt, implements rate limiting, and provides real-time progress tracking with a clean, Airbnb-inspired UI.

## 🎯 Mission-Critical Use Case
**Primary Purpose**: Automated tender discovery and monitoring for business development
- **Current State**: Manual operation for immediate tender discovery
- **Future Vision**: Automated scheduled monitoring with email notifications for new opportunities
- **Target**: Zero missed tender opportunities through comprehensive monitoring

## 🎨 Current Design Principles (MUST MAINTAIN)
- **Airbnb-inspired aesthetic**: Clean, modern UI with #ff5a5f primary color
- **Real-time feedback**: Visual progress bars and status indicators
- **Concurrent processing**: Multi-threaded crawling with proper resource management
- **Respectful crawling**: Robots.txt compliance and rate limiting
- **User-friendly results**: Categorized results (found tenders, no matches, errors)
- **Security-first**: CSP headers, input validation, XSS protection
- **Production stability**: Render.com deployment compatibility
- **Zero missed opportunities**: Comprehensive monitoring to catch all relevant tenders

## 🚨 Critical Issues to Address
1. **Memory leaks from global crawler instances** (affects production stability)
2. **Thread pool exhaustion and resource management** (critical for Render deployment)
3. **Inconsistent error handling patterns** (causes missed tender opportunities)
4. **Fake progress simulation vs real-time tracking** (user experience issue)
5. **Thread safety issues with shared caches** (production reliability concern)
6. **Malformed robots.txt URL parsing** (may miss valid tender sites)
7. **Mixed async/threading models** (performance and stability issues)
8. **No access control** (security concern for organizational use)
9. **No automated scheduling** (manual operation limits efficiency)
10. **No email notifications** (delays in tender discovery)

## 📋 Development Workflow

### Phase 1: Code Quality & Architecture (Checkpoints 1-4)
**Goal**: Stabilize the codebase and fix critical issues

### Phase 2: Feature Enhancement (Checkpoints 5-8)
**Goal**: Add new functionality while maintaining design consistency

### Phase 3: Advanced Features (Checkpoints 9-12)
**Goal**: Implement sophisticated features for power users

---

## 🛠️ Claude Code Best Practices

### Before Starting Any Task:
1. **Read the PRODUCT_PLAN.md** for current checkpoint requirements
2. **Review existing code** to understand current implementation
3. **Present action plan** before making changes
4. **Ask for clarification** if requirements are ambiguous

### Development Standards:
```python
# ✅ Good: Clear, documented, type-hinted
def process_url(url: str, buzzwords: List[str]) -> CrawlResult:
    """Process a single URL and return structured results."""
    try:
        # Implementation
        pass
    except SpecificException as e:
        logger.error(f"Failed to process {url}: {e}")
        return CrawlResult(url=url, error=str(e))

# ❌ Bad: Unclear, no types, poor error handling
def do_stuff(url, words):
    # Implementation
    pass
```

### Testing Approach:
- **Unit tests** for core business logic
- **Integration tests** for crawler functionality
- **Manual testing** at each checkpoint before proceeding
- **Error scenario testing** (network failures, invalid URLs, etc.)

### Code Organization:
```
├── app.py                    # Flask app and routes
├── crawler/
│   ├── __init__.py
│   ├── core.py              # Main crawler logic
│   ├── models.py            # Data classes and types
│   ├── utils.py             # Helper functions
│   └── exceptions.py        # Custom exceptions
├── static/
│   ├── css/styles.css
│   └── js/main.js
├── templates/
│   └── index.html
├── tests/
│   ├── test_crawler.py
│   └── test_integration.py
└── requirements.txt
```

---

## 🔄 Checkpoint Protocol

### Before Each Checkpoint:
1. **Status Check**: Confirm previous checkpoint is stable
2. **Plan Presentation**: Outline approach for current checkpoint
3. **Breaking Changes**: Highlight any API or UI changes
4. **Testing Strategy**: Explain how to verify the implementation

### During Development:
- **Incremental commits** with clear messages
- **Preserve existing functionality** unless explicitly changing it
- **Maintain UI consistency** with current design system
- **Add comprehensive logging** for debugging

### After Each Checkpoint:
1. **Demo the feature** working end-to-end
2. **Highlight key changes** and improvements
3. **Document any new dependencies** or configuration
4. **Wait for manual testing approval** before proceeding

---

## 🚨 Critical Rules

### Must NOT Break:
- **Current UI design** (colors, layout, typography)
- **Existing API endpoints** (unless migrating)
- **Core crawling functionality**
- **Security headers and validation**

### Must ALWAYS:
- **Use type hints** for all function signatures
- **Add comprehensive error handling**
- **Include logging** for debugging
- **Write docstrings** for public functions
- **Test edge cases** (empty inputs, network failures)

### Code Style:
```python
# Imports organization
import os
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass

import requests
from flask import Flask, request, jsonify

from crawler.core import SHAWebCrawler
from crawler.models import CrawlResult

# Constants
DEFAULT_TIMEOUT = 30
MAX_WORKERS = 10
RATE_LIMIT_CALLS = 10
```

---

## 🧪 Testing Requirements

### Unit Tests:
```python
def test_url_validation():
    """Test URL validation with various input formats."""
    assert validate_url("https://example.com") == True
    assert validate_url("not-a-url") == False
    assert validate_url("") == False

def test_buzzword_detection():
    """Test buzzword matching with different cases."""
    text = "This is a Test Document"
    buzzwords = ["test", "document"]
    result = find_buzzwords(text, buzzwords)
    assert result == ["test", "document"]
```

### Integration Tests:
```python
def test_end_to_end_crawling():
    """Test complete crawling workflow."""
    urls = ["https://httpbin.org/html"]
    buzzwords = ["html"]
    crawler = SHAWebCrawler()
    results = crawler.crawl_urls(urls, buzzwords)
    assert len(results) == 1
    assert "html" in results[0]["found"]
```

---

## 📊 Progress Reporting Format

### Checkpoint Progress Report:
```markdown
## Checkpoint X Progress Report

### ✅ Completed:
- Feature A implemented and tested
- Bug B fixed with comprehensive solution
- Performance improvement C deployed

### 🧪 Testing Results:
- Unit tests: 15/15 passing
- Integration tests: 5/5 passing
- Manual testing: All scenarios verified

### 🔄 Next Steps:
- Ready for manual testing approval
- Identified dependencies for next checkpoint
- No blocking issues

### 📝 Notes:
- New dependency: redis (for session management)
- Configuration change: Added SESSION_CONFIG
- Migration required: Old cache format deprecated
```

---

## 🚀 Deployment Considerations

### Development:
```bash
python app.py  # Debug mode enabled
```

### Production:
```bash
gunicorn --config gunicorn_config.py app:app
```

### Environment Variables:
```env
FLASK_ENV=production
SECRET_KEY=your-secret-key
REDIS_URL=redis://localhost:6379  # If using Redis for caching
MAX_WORKERS=5
RATE_LIMIT_CALLS=10

# Render.com specific
PORT=10000
PYTHON_VERSION=3.11.0

# Email notifications (future)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your-email@domain.com
EMAIL_PASS=your-app-password
NOTIFICATION_EMAILS=admin@yourorg.com,team@yourorg.com

# Authentication (future)
JWT_SECRET_KEY=your-jwt-secret
SESSION_TIMEOUT=3600
```

---

## 📞 Communication Protocol

### When to Ask for Clarification:
- **Ambiguous requirements** in product plan
- **Conflicting design decisions**
- **Technical approach uncertainty**
- **Breaking change implications**

### How to Present Plans:
```markdown
## Proposed Approach for Checkpoint X

### Overview:
Brief description of what will be implemented

### Technical Approach:
- Step 1: Specific implementation detail
- Step 2: Another specific step
- Step 3: Final integration step

### Impact Assessment:
- Files to be modified: app.py, crawler/core.py
- New dependencies: none/redis/etc
- Breaking changes: none/list specific changes
- Testing strategy: unit tests + integration tests

### Questions:
- Should we maintain backward compatibility for API X?
- Preferred approach for handling edge case Y?
```

Remember: **Quality over speed**. Take time to implement robust, maintainable solutions that align with the existing codebase architecture and design principles.