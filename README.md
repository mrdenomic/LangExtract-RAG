# LangExtract-Enhanced RAG System

## 🚀 Overview

Here is a [video](https://youtu.be/RPpGIxmdZYs) to get you started

This project demonstrates how Google's **LangExtract** transforms traditional RAG (Retrieval-Augmented Generation) systems by adding intelligent metadata extraction.
### The Problem with Traditional RAG

Traditional RAG systems treat all documents equally, leading to:
- **Mixed contexts** from different versions
- **Conflicting information** in responses
- **Generic "it depends" answers**
- **No version or service awareness**

### The LangExtract Solution

LangExtract adds a metadata intelligence layer that:
- **Extracts structured metadata** (versions, services, document types)
- **Filters documents BEFORE retrieval**
- **Provides precise, version-specific answers**
- **Eliminates context confusion**

## 🏗️ Architecture

### Traditional RAG Flow
```
Documents → Chunks → Embeddings → Vector DB → Search ALL
```

### LangExtract-Enhanced RAG Flow
```
Documents → LangExtract → Metadata + Chunks → Vector DB → Filter → Search Subset
```

## 🔧 Installation

### Prerequisites
- Python 3.8+
- Google Cloud API key (for LangExtract/Gemini)
- OpenAI API key (optional, for embeddings)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/PromtEngineer/langextract_rag.git
cd langextract_rag
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file:
```env
GOOGLE_API_KEY="your-google-api-key"
OPENAI_API_KEY="your-openai-api-key"  # Optional
```

## 🎯 Quick Start

### Run the Demo
```bash
# Run the working demo with real LangExtract
python langextract_rag.py
```

### Query: "How do I authenticate with OAuth in version 2.0?"

**Traditional RAG Response:**
```
"The platform supports multiple authentication methods:
- Version 2.0 uses OAuth 2.0...
- Version 1.0 uses API keys (deprecated)...
Note: Different versions handle auth differently."
```

**LangExtract RAG Response:**
```
"To authenticate with OAuth in version 2.0:
1. Send POST to https://api.platform.com/auth/oauth2/token
2. Include client_id, client_secret, grant_type, scope
3. Receive access token (1 hour) and refresh token (30 days)"
```

## 🎓 How It Works

### 1. Metadata Extraction
LangExtract analyzes documents and extracts:
- **Service names** (e.g., "Authentication API", "Storage Service")
- **Version numbers** (e.g., "2.0", "1.0")
- **Document types** (reference, guide, troubleshooting)
- **Key features** (rate limits, deprecation notices)

### 2. Smart Filtering
Query parser extracts filters from natural language:
- "version 2.0" → `filter: {version: "2.0"}`
- "authentication" → `filter: {service: "Authentication API"}`
- "troubleshoot" → `filter: {doc_type: "troubleshooting"}`

### 3. Precise Retrieval
Instead of searching all documents:
- Apply metadata filters first
- Search only within relevant subset
- Return focused, accurate results

## 🙏 Acknowledgments

- [Google LangExtract](https://github.com/google/langextract) - Structured extraction library
- [LangChain](https://langchain.com/) - RAG orchestration
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [OpenAI](https://openai.com/) - LLM and embeddings
