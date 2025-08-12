"""
LangExtract + RAG System with Proper Metadata Matching
This version fixes the metadata extraction and matching issues.
"""

import os
import textwrap
import re
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==============================================================================
# SAMPLE DATA
# ==============================================================================


def get_sample_documents():
    """Sample technical documentation"""
    return [
        {
            "id": "auth_v2",
            "title": "Authentication API Reference v2.0",
            "content": """# Authentication API v2.0

The Authentication API provides secure access control for all platform services.

## OAuth 2.0 Implementation
To authenticate using OAuth 2.0, send a POST request to /auth/oauth2/token
with your client credentials. The response includes an access token valid
for 1 hour and a refresh token valid for 30 days.

### Rate Limits
- Standard tier: 100 requests per minute
- Premium tier: 1000 requests per minute

Note: API key authentication is deprecated as of v2.0.
Last updated: March 2024"""
        },
        {
            "id": "auth_v1",
            "title": "Authentication API Reference v1.0 (Legacy)",
            "content": """# Authentication API v1.0 (Legacy)

## API Key Authentication
Generate an API key from the dashboard and include it in the X-API-Key header.

### Rate Limits
- All tiers: 60 requests per minute

Note: This version is deprecated. Please upgrade to v2.0.
Last updated: January 2023"""
        },
        {
            "id": "storage",
            "title": "Storage Service Guide", 
            "content": """# Storage Service Guide

Our distributed storage service provides scalable object storage.

## Pricing Tiers
- Standard storage: $0.023 per GB/month
- Archive: $0.004 per GB/month

Storage service uses the Authentication API v2.0 for access control.

Last updated: April 2024"""
        },
        {
            "id": "troubleshooting",
            "title": "Troubleshooting Guide: Authentication Errors",
            "content": """# Troubleshooting Guide: Authentication Errors

## Problem: 401 Unauthorized Error
**Cause**: Invalid or expired credentials
**Solution**: 
1. Verify that your OAuth token hasn't expired (tokens are valid for 1 hour)
2. Use the refresh token to obtain a new access token

## Problem: Rate Limiting (429 Error)  
**Cause**: Exceeding rate limits
**Solution**:
1. Standard tier allows 100 req/min
2. Consider upgrading to premium tier for 1000 req/min

Last updated: March 2024"""
        }
    ]

# ==============================================================================
# PROCESSING
# ==============================================================================

class FixedLangExtractProcessor:
    """Enhanced metadata extraction with better prompts and normalization"""
    
    def __init__(self):
        try:
            import langextract as lx
            self.lx = lx
            self.setup_complete = True
            print("✅ LangExtract initialized")
        except ImportError:
            print("⚠️  LangExtract not installed - using enhanced regex extraction")
            self.setup_complete = False
    
        
    def extract_metadata(self, documents: List[Dict]) -> List[Dict]:
        """Extract and normalize metadata"""
        
        if not self.setup_complete:
            return self._enhanced_regex_extraction(documents)

        # Improved extraction prompt
        prompt = """
        Extract these specific fields from technical documentation:
        
        1. service_name: The MAIN service or API name from the title (e.g., "Authentication API", "Storage Service")
        2. version_number: The version number ONLY (e.g., "2.0", "1.0") - extract just the number
        3. document_category: The document type - MUST be one of: "reference", "guide", "troubleshooting"
        4. rate_limits: Any rate limiting information
        5. deprecated_items: Things marked as deprecated
        
        Be very precise - extract the EXACT main service name from the title.
        For version, extract ONLY the number (like "2.0", not "v2.0" or "version 2.0").
        For category: "Reference" = reference, "Guide" = guide, "Troubleshooting" = troubleshooting."""

        
        # Better examples
        examples = [
            self.lx.data.ExampleData(
                text="# Payment API v3.0 Reference\n\nThe Payment API handles transactions.\n\nRate limit: 500 requests per minute",
                extractions=[
                    self.lx.data.Extraction(
                        extraction_class="service_name",
                        extraction_text="Payment API",
                        attributes={}
                    ),
                    self.lx.data.Extraction(
                        extraction_class="version_number", 
                        extraction_text="3.0",
                        attributes={}
                    ),
                    self.lx.data.Extraction(
                        extraction_class="document_category",
                        extraction_text="reference", 
                        attributes={}
                    ),
                    self.lx.data.Extraction(
                        extraction_class="rate_limits",
                        extraction_text="500 requests per minute",
                        attributes={}
                    )
                ]
            )
        ]

        
        extracted_docs = []
        
        for doc in documents:
            print(f"📄 Processing: {doc['title']}")
            
            try:
                result = self.lx.extract(
                    text_or_documents=doc['content'],
                    prompt_description=prompt,
                    examples=examples,
                    model_id="gemini-2.5-flash",
                    extraction_passes=2
                )
                
                # Process and normalize extractions
                metadata = self._process_and_normalize(result.extractions, doc)
                
            except Exception as e:
                print(f"  ⚠️  LangExtract failed: {e}")
                metadata = self._enhanced_regex_extraction([doc])[0]['metadata']
            
            extracted_docs.append({
                'id': doc['id'],
                'title': doc['title'],
                'content': doc['content'],
                'metadata': metadata
            })
        
        return extracted_docs
   
    
    def _process_and_normalize(self, extractions, doc: Dict) -> Dict:
        """Process LangExtract results and normalize them"""
        
        metadata = {
            'service': 'unknown',
            'version': 'unknown', 
            'doc_type': 'reference',
            'rate_limits': [],
            'deprecated': False
        }
        
        for extraction in extractions:
            if extraction.extraction_class == "service_name":
                metadata['service'] = extraction.extraction_text
            elif extraction.extraction_class == "version_number":
                metadata['version'] = extraction.extraction_text
            elif extraction.extraction_class == "document_category":
                metadata['doc_type'] = extraction.extraction_text.lower()
            elif extraction.extraction_class == "rate_limits":
                metadata['rate_limits'].append(extraction.extraction_text)
            elif extraction.extraction_class == "deprecated_items":
                metadata['deprecated'] = True
        
        # Fallback to regex if LangExtract missed key fields
        if metadata['service'] == 'unknown' or metadata['version'] == 'unknown':
            regex_metadata = self._enhanced_regex_extraction([doc])[0]['metadata']
            if metadata['service'] == 'unknown':
                metadata['service'] = regex_metadata['service']
            if metadata['version'] == 'unknown':
                metadata['version'] = regex_metadata['version']
            if metadata['doc_type'] == 'reference':
                metadata['doc_type'] = regex_metadata['doc_type']
        
        return metadata
    
    def _enhanced_regex_extraction(self, documents: List[Dict]) -> List[Dict]:
        """Enhanced regex-based extraction with better patterns"""
        
        extracted_docs = []
        
        for doc in documents:
            metadata = {
                'service': 'unknown',
                'version': 'unknown',
                'doc_type': 'reference', 
                'rate_limits': [],
                'deprecated': False
            }
            
            title = doc.get('title', '')
            content = doc['content']
            
            # Extract service name from title
            service_match = re.search(r'([\w\s]+(?:API|Service))', title)
            if service_match:
                metadata['service'] = service_match.group(1).strip()
            
            # Extract version number
            version_match = re.search(r'v?([\d.]+)', title)
            if version_match:
                metadata['version'] = version_match.group(1)
            
            # Determine document type
            if 'troubleshooting' in title.lower():
                metadata['doc_type'] = 'troubleshooting'
            elif 'guide' in title.lower():
                metadata['doc_type'] = 'guide'
            else:
                metadata['doc_type'] = 'reference'
            
            # Extract rate limits
            rate_matches = re.findall(r'(\d+)\s*(?:requests?|req)[/\s]*(?:per\s*)?min', content.lower())
            metadata['rate_limits'] = [f"{r} req/min" for r in rate_matches]
            
            # Check for deprecation
            if 'deprecated' in content.lower():
                metadata['deprecated'] = True
            
            extracted_docs.append({
                'id': doc['id'],
                'title': doc['title'], 
                'content': doc['content'],
                'metadata': metadata
            })
        
        return extracted_docs


class SmartVectorStore:
    """Vector store with fuzzy metadata matching"""
    
    def __init__(self):
        self.documents = []
    
    def add_documents(self, docs: List[Dict]):
        """Add documents with metadata"""
        self.documents = docs
        print(f"✅ Indexed {len(docs)} documents")
    
    def search(self, query: str, filters: Dict = None) -> List[Dict]:
        """Search with smart metadata filtering"""
        if not filters:
            # No filters - return all matching documents
            return [doc for doc in self.documents 
                   if any(word.lower() in doc['content'].lower() for word in query.split())]
        
        # Apply smart filters
        filtered_docs = []
        
        for doc in self.documents:
            match = True
            
            # Smart service matching
            if 'service' in filters:
                query_service = filters['service'].lower()
                doc_service = doc['metadata']['service'].lower()
                # Allow partial matches
                if query_service not in doc_service and doc_service not in query_service:
                    # Try keyword matching
                    query_keywords = set(query_service.replace('api', '').replace('service', '').split())
                    doc_keywords = set(doc_service.replace('api', '').replace('service', '').split())
                    if not query_keywords.intersection(doc_keywords):
                        match = False
            
            # Exact version matching
            if 'version' in filters:
                if filters['version'] != doc['metadata']['version']:
                    match = False
            
            # Document type matching
            if 'doc_type' in filters:
                if filters['doc_type'] != doc['metadata']['doc_type']:
                    match = False
            
            if match:
                # Also check if content matches query
                if any(word.lower() in doc['content'].lower() for word in query.split()):
                    filtered_docs.append(doc)
        
        return filtered_docs

def extract_smart_filters(query: str) -> Dict:
    """Extract metadata filters with better service matching"""
    import re
    
    filters = {}
    query_lower = query.lower()
    
    # Extract version
    version_match = re.search(r'v(?:ersion)?\s*([\d.]+)', query_lower)
    if version_match:
        filters['version'] = version_match.group(1)
    
    # Extract service with better matching
    if 'authentication' in query_lower or 'auth' in query_lower:
        filters['service'] = 'Authentication API'  # This will match fuzzy
    elif 'storage' in query_lower:
        filters['service'] = 'Storage Service'
    
    # Extract document type
    if 'troubleshoot' in query_lower or 'error' in query_lower or 'fix' in query_lower:
        filters['doc_type'] = 'troubleshooting'
    elif 'guide' in query_lower or 'how to' in query_lower:
        filters['doc_type'] = 'guide'
    
    return filters


def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║         LangExtract + RAG System Demo                            ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Load documents
    print("📚 Loading documents...")
    documents = get_sample_documents()
    
    # Step 2: Extract metadata
    print("\n🔍 Extracting metadata with improved system...")
    extractor = FixedLangExtractProcessor()
    extracted_docs = extractor.extract_metadata(documents)
    
    # Display extracted metadata
    print("\n📊 Extracted & Normalized Metadata:")
    for doc in extracted_docs:
        print(f"\n  {doc['id']} ({doc['title']}):")
        print(f"    Service: '{doc['metadata']['service']}'")
        print(f"    Version: '{doc['metadata']['version']}'")
        print(f"    Type: '{doc['metadata']['doc_type']}'")
        if doc['metadata']['rate_limits']:
            print(f"    Rate limits: {doc['metadata']['rate_limits']}")
    
    # Step 3: Index documents
    print("\n💾 Indexing documents...")
    vector_store = SmartVectorStore()
    vector_store.add_documents(extracted_docs)
    
    # Step 4: Test queries with real results
    test_queries = [
        "How do I authenticate with OAuth in version 2.0?",
        "What are the rate limits for authentication?", 
        "How do I troubleshoot 401 errors?",
        "Tell me about storage pricing",
    ]
    
    print("\n🔬 Testing Smart Retrieval:")
    print("=" * 70)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        
        # Extract filters
        filters = extract_smart_filters(query)
        if filters:
            print(f"   🎯 Smart filters: {filters}")
        
        # Search WITH metadata
        with_results = vector_store.search(query, filters)
        print(f"   ✅ With smart filtering: Found {len(with_results)} documents")
        if with_results:
            for r in with_results:
                print(f"      - {r['id']}: {r['metadata']['service']} v{r['metadata']['version']} ({r['metadata']['doc_type']})")
        print("\nActual documents retrieved: ", with_results)

        # Search WITHOUT metadata
        without_results = vector_store.search(query, None)
        print(f"\n ❌ Without filtering: Found {len(without_results)} documents")
        print("\n: Actual documents retrieved: ", without_results)
        

if __name__ == "__main__":
    main()
