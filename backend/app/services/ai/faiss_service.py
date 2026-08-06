"""
FAISS Vector Store Service.
Handles fast similarity search for high-dimensional embeddings using FAISS CPU.
"""
import os
import numpy as np
from typing import List, Dict, Any, Optional
from app.core.logger import get_logger
from app.services.interfaces import IVectorStoreService
from .models import Embedding, RecognitionCandidate

try:
    import faiss
except ImportError:
    faiss = None

logger = get_logger(__name__)

class FAISSService(IVectorStoreService):
    def __init__(self, dimension: int = 512, index_path: str = "faiss_index.bin"):
        self.dimension = dimension
        self.index_path = index_path
        self.index = None
        self.identity_mapping: Dict[int, str] = {}
        self._current_id = 0
        
    def load_model(self) -> None:
        """Loads FAISS index from disk if it exists, else creates a new one."""
        if faiss is None:
            raise ImportError("faiss-cpu is required for FAISSService.")
            
        logger.info(f"Loading FAISS index from {self.index_path}...")
        
                      
        map_path = self.index_path + ".map.json"
        if os.path.exists(map_path):
            try:
                import json
                with open(map_path, 'r') as f:
                    self.identity_mapping = {int(k): v for k, v in json.load(f).items()}
            except Exception as e:
                logger.error(f"Failed to load FAISS mapping: {e}")
                self.identity_mapping = {}
        
                                                                                             
                                                       
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors.")
                self._current_id = max(self.identity_mapping.keys()) + 1 if self.identity_mapping else self.index.ntotal
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}. Building a new one.")
                self.index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dimension))
                self.identity_mapping = {}
                self._current_id = 0
        else:
            self.index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dimension))
            logger.info("Initialized new empty FAISS IndexFlatIP.")
            
    def unload_model(self) -> None:
        if self.index is not None:
            self._save_index()
            self.index = None
            logger.info("FAISS index unloaded.")
            
    def save_index(self) -> None:
        """Saves FAISS index to disk."""
        self._save_index()
        
    def _save_index(self) -> None:
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            
            map_path = self.index_path + ".map.json"
            try:
                import json
                with open(map_path, 'w') as f:
                    json.dump(self.identity_mapping, f)
            except Exception as e:
                logger.error(f"Failed to save FAISS mapping: {e}")
                
            logger.info(f"FAISS index saved to {self.index_path}.")
            
    def add_embedding(self, identity_id: str, embedding: Embedding) -> None:
        if self.index is None:
            raise RuntimeError("FAISS index not loaded.")
            
        vector = embedding.vector.astype(np.float32).reshape(1, -1)
        faiss_id = np.array([self._current_id], dtype=np.int64)
        
        self.index.add_with_ids(vector, faiss_id)
        self.identity_mapping[self._current_id] = identity_id
        self._current_id += 1
        
                                            
                            

    def delete_embedding(self, identity_id: str) -> None:
        """Removes all vectors mapping to this identity."""
        if self.index is None:
            raise RuntimeError("FAISS index not loaded.")
            
        ids_to_remove = [fid for fid, uid in self.identity_mapping.items() if uid == identity_id]
        if not ids_to_remove:
            return
            
        self.index.remove_ids(np.array(ids_to_remove, dtype=np.int64))
        for fid in ids_to_remove:
            del self.identity_mapping[fid]

    def search(self, embedding: Embedding, k: int = 1) -> List[RecognitionCandidate]:
        if self.index is None or self.index.ntotal == 0:
            return []
            
        vector = embedding.vector.astype(np.float32).reshape(1, -1)
        distances, indices = self.index.search(vector, k)
        
        candidates = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
                
            internal_id = int(idx)
            identity_id = self.identity_mapping.get(internal_id, "UNKNOWN_ID")
            
            candidates.append(RecognitionCandidate(
                identity_id=identity_id,
                similarity_score=float(dist),
                name=None,                                                         
                department=None
            ))
            
        return candidates
