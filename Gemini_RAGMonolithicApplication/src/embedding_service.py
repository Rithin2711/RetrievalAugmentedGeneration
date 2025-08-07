import os
import json
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
import faiss

from .models import DocumentChunk

EMBEDDINGS_DIR = os.getenv("EMBEDDINGS_DIR", "./embeddings")

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding service with sentence transformer model"""
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine similarity)
        self.chunk_ids = []  # Track chunk IDs corresponding to embeddings
        self.embeddings_file = os.path.join(EMBEDDINGS_DIR, "embeddings.json")
        self.index_file = os.path.join(EMBEDDINGS_DIR, "faiss_index.bin")
        
        # Load existing embeddings and index
        self._load_embeddings()
    
    def _load_embeddings(self):
        """Load existing embeddings and FAISS index"""
        if os.path.exists(self.embeddings_file) and os.path.exists(self.index_file):
            try:
                # Load embeddings metadata
                with open(self.embeddings_file, 'r') as f:
                    embeddings_data = json.load(f)
                    self.chunk_ids = embeddings_data.get("chunk_ids", [])
                
                # Load FAISS index
                self.index = faiss.read_index(self.index_file)
                print(f"Loaded {len(self.chunk_ids)} embeddings from disk")
            except Exception as e:
                print(f"Error loading embeddings: {e}")
                self.index = faiss.IndexFlatIP(self.dimension)
                self.chunk_ids = []
    
    def _save_embeddings(self):
        """Save embeddings metadata and FAISS index"""
        try:
            # Save metadata
            embeddings_data = {
                "chunk_ids": self.chunk_ids,
                "dimension": self.dimension,
                "model_name": "all-MiniLM-L6-v2"
            }
            
            with open(self.embeddings_file, 'w') as f:
                json.dump(embeddings_data, f, indent=2)
            
            # Save FAISS index
            faiss.write_index(self.index, self.index_file)
        except Exception as e:
            print(f"Error saving embeddings: {e}")

    # PUBLIC_INTERFACE
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding vector for text"""
        embedding = self.model.encode([text])[0]
        return embedding.tolist()
    
    # PUBLIC_INTERFACE
    def add_chunk_embedding(self, chunk: DocumentChunk) -> bool:
        """Add embedding for a document chunk"""
        try:
            # Check if chunk already has embedding
            if chunk.id in self.chunk_ids:
                return True
            
            # Create embedding
            embedding = self.model.encode([chunk.content])[0]
            
            # Normalize for cosine similarity
            embedding = embedding / np.linalg.norm(embedding)
            
            # Add to FAISS index
            self.index.add(embedding.reshape(1, -1))
            self.chunk_ids.append(chunk.id)
            
            # Save to disk
            self._save_embeddings()
            
            return True
        except Exception as e:
            print(f"Error adding chunk embedding: {e}")
            return False
    
    # PUBLIC_INTERFACE
    def batch_add_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Add embeddings for multiple chunks at once"""
        new_chunks = [chunk for chunk in chunks if chunk.id not in self.chunk_ids]
        
        if not new_chunks:
            return 0
        
        try:
            # Create embeddings for all new chunks
            texts = [chunk.content for chunk in new_chunks]
            embeddings = self.model.encode(texts)
            
            # Normalize embeddings
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Add to FAISS index
            self.index.add(embeddings)
            self.chunk_ids.extend([chunk.id for chunk in new_chunks])
            
            # Save to disk
            self._save_embeddings()
            
            return len(new_chunks)
        except Exception as e:
            print(f"Error batch adding embeddings: {e}")
            return 0
    
    # PUBLIC_INTERFACE
    def search_similar_chunks(self, query: str, k: int = 5, threshold: float = 0.5) -> List[Tuple[str, float]]:
        """Search for similar chunks to the query"""
        if self.index.ntotal == 0:
            return []
        
        try:
            # Create query embedding
            query_embedding = self.model.encode([query])[0]
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            
            # Search in FAISS index
            scores, indices = self.index.search(query_embedding.reshape(1, -1), min(k, self.index.ntotal))
            
            # Filter results by threshold and return chunk IDs with scores
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= threshold and idx < len(self.chunk_ids):
                    results.append((self.chunk_ids[idx], float(score)))
            
            return results
        except Exception as e:
            print(f"Error searching embeddings: {e}")
            return []
    
    # PUBLIC_INTERFACE
    def get_chunk_embedding(self, chunk_id: str) -> Optional[List[float]]:
        """Get embedding for a specific chunk"""
        if chunk_id not in self.chunk_ids:
            return None
        
        try:
            idx = self.chunk_ids.index(chunk_id)
            embedding = self.index.reconstruct(idx)
            return embedding.tolist()
        except Exception as e:
            print(f"Error getting chunk embedding: {e}")
            return None
    
    # PUBLIC_INTERFACE
    def remove_chunk_embeddings(self, chunk_ids: List[str]) -> int:
        """Remove embeddings for specified chunks"""
        # FAISS doesn't support deletion easily, so we rebuild the index without the specified chunks
        remaining_chunk_ids = [cid for cid in self.chunk_ids if cid not in chunk_ids]
        
        if len(remaining_chunk_ids) == len(self.chunk_ids):
            return 0  # Nothing to remove
        
        # Create new index
        new_index = faiss.IndexFlatIP(self.dimension)
        
        # Add remaining embeddings
        if remaining_chunk_ids:
            embeddings_to_keep = []
            for i, chunk_id in enumerate(self.chunk_ids):
                if chunk_id in remaining_chunk_ids:
                    embedding = self.index.reconstruct(i)
                    embeddings_to_keep.append(embedding)
            
            if embeddings_to_keep:
                embeddings_array = np.array(embeddings_to_keep)
                new_index.add(embeddings_array)
        
        # Replace index and chunk IDs
        self.index = new_index
        removed_count = len(self.chunk_ids) - len(remaining_chunk_ids)
        self.chunk_ids = remaining_chunk_ids
        
        # Save to disk
        self._save_embeddings()
        
        return removed_count
    
    # PUBLIC_INTERFACE
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the embedding index"""
        return {
            "total_embeddings": self.index.ntotal,
            "dimension": self.dimension,
            "chunk_ids_count": len(self.chunk_ids),
            "index_size_mb": os.path.getsize(self.index_file) / 1024 / 1024 if os.path.exists(self.index_file) else 0
        }

# Global instance
embedding_service = EmbeddingService()
