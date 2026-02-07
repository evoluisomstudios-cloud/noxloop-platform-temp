"""
RAG (Retrieval-Augmented Generation) Client
Connects to external RAG service for knowledge retrieval
"""
import os
import logging
import httpx
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class RAGClient:
    """RAG Service Client with graceful fallback"""
    
    def __init__(self):
        self.enabled = os.environ.get("RAG_ENABLED", "false").lower() == "true"
        self.base_url = os.environ.get("RAG_BASE_URL", "http://localhost:8811").rstrip("/")
        self.top_k = int(os.environ.get("RAG_TOP_K", "5"))
        self.timeout = float(os.environ.get("RAG_TIMEOUT", "10.0"))
        
        if self.enabled:
            logger.info(f"RAG enabled @ {self.base_url}")
        else:
            logger.info("RAG disabled")
    
    async def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from RAG service.
        Returns empty list on failure (graceful degradation).
        """
        if not self.enabled:
            return []
        
        k = top_k or self.top_k
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Adaptable endpoint - configure in .env if different
                endpoint = os.environ.get("RAG_QUERY_ENDPOINT", "/query")
                
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json={
                        "query": query,
                        "top_k": k
                    },
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Handle different response formats
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        return data.get("results", data.get("documents", []))
                    return []
                else:
                    logger.warning(f"RAG query failed with status {response.status_code}")
                    return []
                    
        except httpx.TimeoutException:
            logger.warning(f"RAG query timeout after {self.timeout}s")
            return []
        except Exception as e:
            logger.warning(f"RAG query error: {e}")
            return []
    
    async def is_available(self) -> bool:
        """Check if RAG service is reachable"""
        if not self.enabled:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                health_endpoint = os.environ.get("RAG_HEALTH_ENDPOINT", "/health")
                response = await client.get(f"{self.base_url}{health_endpoint}")
                return response.status_code == 200
        except Exception:
            return False
    
    def format_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents as context for LLM prompt"""
        if not documents:
            return ""
        
        context_parts = ["## Relevant Context\n"]
        for i, doc in enumerate(documents, 1):
            # Handle different document formats
            content = doc.get("content", doc.get("text", doc.get("page_content", str(doc))))
            source = doc.get("source", doc.get("metadata", {}).get("source", f"Document {i}"))
            context_parts.append(f"### Source {i}: {source}\n{content}\n")
        
        return "\n".join(context_parts)
    
    def get_status(self) -> Dict[str, Any]:
        """Get RAG service status"""
        return {
            "enabled": self.enabled,
            "base_url": self.base_url if self.enabled else None,
            "top_k": self.top_k
        }

# Global instance
rag_client = RAGClient()
