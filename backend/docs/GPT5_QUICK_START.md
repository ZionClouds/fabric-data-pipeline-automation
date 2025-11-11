# GPT-5 + Bing Search - Quick Start Guide

⚡ Get up and running in 5 minutes!

---

## 🚀 Quick Start

### 1. Install Dependencies (30 seconds)

```bash
cd backend
pip install openai>=1.12.0
```

### 2. Configuration (Already Done! ✅)

Your Azure OpenAI credentials are already configured in `config.py`:
- ✅ Endpoint: `https://jayr-mgs8va5p-eastus2.cognitiveservices.azure.com/`
- ✅ Deployment: `gpt-5-chat`
- ✅ API Key: Configured

### 3. Optional: Add Bing Search (2 minutes)

**Without Bing Search:**
- GPT-5 works fine
- Answers from training data only
- No access to latest docs

**With Bing Search:**
- GPT-5 can search for latest Fabric documentation
- Always up-to-date information
- Automatic search when needed

**To enable:**
1. Get Bing Search API key: https://portal.azure.com/#create/microsoft.bingsearch
2. Add to `.env` file:
   ```bash
   BING_SEARCH_API_KEY=your-key-here
   ```

### 4. Test It! (1 minute)

```bash
python3 test_gpt5_integration.py
```

Expected output:
```
✅ Basic Connection: PASSED
✅ Bing Search: PASSED (or SKIPPED if no key)
✅ Function Calling: PASSED
✅ Fabric Query: PASSED
```

### 5. Start Using It!

```bash
python3 main.py
```

---

## 📡 API Endpoints

### Endpoint 1: GPT-5 with Bing Search (Recommended)

```bash
POST http://localhost:8080/api/ai/gpt5-chat
```

**Use for:**
- Questions about latest Fabric features
- API troubleshooting
- "How do I..." questions

**Example:**
```bash
curl -X POST http://localhost:8080/api/ai/gpt5-chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test" \
  -d '{
    "workspace_id": "test",
    "messages": [
      {
        "role": "user",
        "content": "What are the latest authentication methods for OneLake shortcuts?"
      }
    ]
  }'
```

### Endpoint 2: GPT-5 Simple (Faster)

```bash
POST http://localhost:8080/api/ai/gpt5-simple-chat
```

**Use for:**
- Code generation
- General questions
- When speed matters

---

## 🎯 Quick Examples

### Example 1: Check if Feature Exists

**Question:**
> "Can I use managed identity for Azure Blob connections in Fabric?"

**GPT-5 will:**
1. Search latest Fabric documentation
2. Tell you if it's supported (yes/no)
3. Provide setup instructions
4. Give you the official doc link

### Example 2: Fix API Error

**Question:**
> "I'm getting error 'enableSkipIncompatibleRow not supported'. What should I do?"

**GPT-5 will:**
1. Search for latest pipeline API docs
2. Find the correct parameter name
3. Provide working code example
4. Explain the change

### Example 3: Learn New Feature

**Question:**
> "What's new in Fabric pipelines in 2025?"

**GPT-5 will:**
1. Search for latest feature announcements
2. List new capabilities
3. Provide examples
4. Link to documentation

---

## ⚡ Quick Tips

### When to Use Bing Search

**✅ Use WITH search (`/api/ai/gpt5-chat`):**
- "What are the LATEST..."
- "How do I configure..." (might have changed)
- Error troubleshooting
- Authentication questions
- Feature availability

**✅ Use WITHOUT search (`/api/ai/gpt5-simple-chat`):**
- Generate PySpark code
- Explain a concept
- Design discussions
- General chat

### Performance Tips

1. **Use simple chat when possible** - It's faster (no search calls)
2. **Set reasonable token limits** - Default is 16,384 (very generous)
3. **Cache common queries** - If asking same question repeatedly

### Cost Tips

- **GPT-5**: ~$0.01-0.03 per query
- **Bing Search**: Free tier = 1,000 searches/month
- **Total**: Very affordable for most use cases

---

## 🐛 Troubleshooting

### Problem: "Connection failed"

**Check:**
```bash
# Test Azure OpenAI connection
python3 test_gpt5_integration.py
```

**Common causes:**
- Wrong endpoint URL
- Invalid API key
- Deployment name mismatch

### Problem: "Bing Search not working"

**Check:**
```python
# In config.py, verify:
BING_SEARCH_API_KEY = "your-key-here"  # Not empty!
```

**Note:** GPT-5 still works without Bing, just no search capability

### Problem: "Model not searching"

**Try this:**
Ask explicitly: "What are the LATEST features in Fabric 2025?"

The word "latest" triggers search.

---

## 📚 Next Steps

### Learn More
- Read full docs: `docs/GPT5_BING_SEARCH_INTEGRATION.md`
- Test different queries: `test_gpt5_integration.py`
- Monitor logs: Check console output

### Production Checklist
- [ ] Get Bing Search API key
- [ ] Set up monitoring
- [ ] Configure rate limits
- [ ] Test with real Fabric queries
- [ ] Update frontend to use new endpoint

---

## 🎉 You're Ready!

Your backend now has:
- ✅ Azure OpenAI GPT-5 integration
- ✅ Bing Search capability (optional)
- ✅ Function calling
- ✅ Two new API endpoints
- ✅ Comprehensive tests

**Start chatting with GPT-5 about Microsoft Fabric!**

---

**Questions?** See `docs/GPT5_BING_SEARCH_INTEGRATION.md` for detailed documentation.
