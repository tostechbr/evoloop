# EvoLoop Documentation — Stage 1

Welcome to EvoLoop's Stage 1 documentation. This folder contains the core conceptual and practical guides for understanding and using the framework.

## 📚 Files

### **`concepts.md`**
Understand **why** you should use EvoLoop. Perfect for:
- Understanding the problem EvoLoop solves
- Learning the core philosophy
- Deciding if EvoLoop is right for your use case
- Seeing how EvoLoop differs from alternatives

**Start here if:** You want to understand the "why" before diving into code.

### **`guide.md`**
**How to** use EvoLoop. A practical, hands-on guide with:
- Installation
- 3 ways to integrate (`@monitor`, `wrap()`, `log()`)
- Examples and code snippets
- API reference
- Troubleshooting

**Start here if:** You're ready to instrument your agent and capture traces.

---

## Quick Navigation

| Need | Go To |
|------|-------|
| Why should I use EvoLoop? | [concepts.md](concepts.md) |
| How do I use EvoLoop? | [guide.md](guide.md) |
| What's the philosophy? | [concepts.md](concepts.md) — Section "The Solution" |
| Show me code examples | [guide.md](guide.md) — Section "3 Ways to Use" |
| Troubleshooting | [guide.md](guide.md) — Section "Troubleshooting" |

---

## The EvoLoop Mission

EvoLoop is a framework for **evaluating and improving AI agents**.

**Stage 1 (Current):** Capture traces — record what every agent execution does.

**Stage 2 (Next):** Evaluate traces — automatically score outputs against criteria.

**Stage 3+:** Optimize — learn from failures and evolve prompts/logic.

---

## Learn by Example

### Minimal Example (30 seconds)

```python
from evoloop import monitor, get_storage

@monitor
def my_agent(question: str) -> str:
    return "answer"

# Use it
result = my_agent("What's 2+2?")

# Analyze
storage = get_storage()
print(f"Saved {storage.count()} traces")
```

### Complete Example
See [guide.md](guide.md#complete-example-qa-agent) for a full Q&A agent using OpenAI.

---

## For Website Integration

These documents are designed to be:
- **Framework-agnostic:** Work with any static site generator (Hugo, Next.js, Jekyll, etc.)
- **Clean Markdown:** No special syntax, just standard GitHub-flavored Markdown
- **Standalone:** Can be rendered independently or combined

### Suggested Website Structure

```
website/
├── docs/
│   ├── stage1/
│   │   ├── concepts.html    (from concepts.md)
│   │   ├── guide.html       (from guide.md)
│   │   └── index.html       (from this file)
│   ├── stage2/
│   │   └── (coming soon)
│   └── api/
│       └── (coming soon)
```

### Metadata for Site Generators

If you need frontmatter for Hugo/Next.js, add to each file:

```yaml
---
title: "EvoLoop Stage 1 — Concepts"
description: "Understanding why you should use EvoLoop"
weight: 1
---
```

---

## Next Steps

1. **Understand the why:** Read [concepts.md](concepts.md) (5 min)
2. **Learn the how:** Read [guide.md](guide.md) (10 min)
3. **Try it:** Run the minimal example above
4. **Deep dive:** See `examples/` in the main repo for real-world usage

---

## Roadmap

- ✅ Stage 1: Trace capture documentation
- 🔜 Stage 2: Evaluation and Judge documentation
- 🔜 Stage 3: Optimization and evolution documentation
- 🔜 API Reference
- 🔜 Video tutorials

---

## Questions?

- **GitHub Issues:** https://github.com/tostechbr/evoloop/issues
- **Main Repo:** https://github.com/tostechbr/evoloop
- **Version:** Stage 1 (2025-12-18)
