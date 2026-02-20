# Path: memory/memory_manager.py
import json
import os
import logging
import chromadb
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from .vector_store import VectorStore

class MemoryManager:
    """
    LUNA-ULTRA Memory System: 3-day rolling memory with Infinite Long-Term Memory via ChromaDB.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rolling_days = config.get("rolling_days", 3)
        self.memory_file = "memory/short_term_memory.json"
        self.vector_store = VectorStore(config)
        self.memory_data = self.load_memory()
        
        # Infinite Memory Setup
        self.db_path = "memory/vector_db"
        if not os.path.exists(self.db_path):
            os.makedirs(self.db_path)
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.client.get_or_create_collection(name="infinite_memory")
            logging.info("MemoryManager: Infinite Memory (ChromaDB) initialized.")
        except Exception as e:
            logging.error(f"MemoryManager: Failed to initialize ChromaDB: {e}")
            self.collection = None

        self.cleanup_old_memory()
        logging.info("MemoryManager initialized.")

    def load_memory(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logging.warning(f"Short-term memory file {self.memory_file} is corrupted. Starting fresh.")
                return []
        return []

    def save_memory(self):
        if not os.path.exists("memory"):
            os.makedirs("memory")
        with open(self.memory_file, "w") as f:
            json.dump(self.memory_data, f, indent=4)

    def store_interaction(self, user_input: str, response: str, tags: List[str] = []):
        timestamp = datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "user": user_input,
            "luna": response,
            "tags": tags
        }
        # Rolling Memory
        self.memory_data.append(entry)
        self.save_memory()
        
        # Original Vector Store (RAG)
        self.vector_store.add_entry(entry)
        
        # Infinite Memory (ChromaDB)
        if self.collection:
            try:
                content = f"User: {user_input}\nLUNA: {response}"
                self.collection.add(
                    documents=[content],
                    metadatas=[{"timestamp": timestamp, "tags": ",".join(tags)}],
                    ids=[f"mem_{int(datetime.now().timestamp())}"]
                )
            except Exception as e:
                logging.error(f"MemoryManager: ChromaDB storage error: {e}")

    def get_context(self, current_input: str, limit: int = 5) -> str:
        context_parts = []
        
        # Recent interactions
        recent = self.memory_data[-limit:]
        for entry in recent:
            context_parts.append("User: {}\nLUNA: {}".format(entry.get("user", ""), entry.get("luna", "")))
        
        # Infinite Memory Recall (ChromaDB)
        if self.collection:
            try:
                results = self.collection.query(query_texts=[current_input], n_results=2)
                if results['documents'] and results['documents'][0]:
                    for doc in results['documents'][0]:
                        context_parts.append(f"Past Memory Recall: {doc}")
            except Exception as e:
                logging.error(f"MemoryManager: Infinite recall failed: {e}")

        return "\n".join(context_parts)

    def add_memory(self, role: str, content: str):
        """FIXED BUG-007: Alias for store_interaction() for compatibility with external code.
        
        Args:
            role: 'user' or 'assistant'/'luna'
            content: The message content
        """
        if role in ('user', 'human'):
            self.store_interaction(content, "")
        else:
            # For assistant messages, update the last entry's luna field
            if self.memory_data:
                self.memory_data[-1]["luna"] = content
                self.save_memory()
            else:
                self.store_interaction("", content)

    def cleanup_old_memory(self):
        cutoff_date = datetime.now() - timedelta(days=self.rolling_days)
        self.memory_data = [
            entry for entry in self.memory_data 
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
        ]
        self.save_memory()
        logging.info(f"Cleaned up old memory. Remaining: {len(self.memory_data)}")
