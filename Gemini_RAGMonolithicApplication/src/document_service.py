import os
import json
import uuid
from typing import List, Optional, Dict, Any
import PyPDF2
from io import BytesIO

from .models import Document, DocumentType, DocumentChunk

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
EMBEDDINGS_DIR = os.getenv("EMBEDDINGS_DIR", "./embeddings")

# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

class DocumentService:
    def __init__(self):
        self.documents_file = os.path.join(UPLOAD_DIR, "documents.json")
        self.chunks_file = os.path.join(EMBEDDINGS_DIR, "chunks.json")
    
    def _load_documents(self) -> Dict[str, Any]:
        """Load documents metadata from JSON file"""
        if os.path.exists(self.documents_file):
            try:
                with open(self.documents_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_documents(self, documents: Dict[str, Any]) -> None:
        """Save documents metadata to JSON file"""
        with open(self.documents_file, 'w') as f:
            json.dump(documents, f, indent=2, default=str)
    
    def _load_chunks(self) -> Dict[str, Any]:
        """Load document chunks from JSON file"""
        if os.path.exists(self.chunks_file):
            try:
                with open(self.chunks_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_chunks(self, chunks: Dict[str, Any]) -> None:
        """Save document chunks to JSON file"""
        with open(self.chunks_file, 'w') as f:
            json.dump(chunks, f, indent=2, default=str)
    
    def _get_document_type(self, filename: str, content_type: str) -> DocumentType:
        """Determine document type from filename and content type"""
        if content_type == "application/pdf" or filename.lower().endswith('.pdf'):
            return DocumentType.PDF
        elif content_type == "application/json" or filename.lower().endswith('.json'):
            return DocumentType.JSON
        else:
            return DocumentType.TEXT
    
    def _extract_text_from_pdf(self, file_data: bytes) -> str:
        """Extract text content from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_data))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def _extract_text_from_json(self, file_data: bytes) -> str:
        """Extract text content from JSON file"""
        try:
            json_data = json.loads(file_data.decode('utf-8'))
            # Convert JSON to readable text format
            return json.dumps(json_data, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"Failed to parse JSON file: {str(e)}")
    
    def _extract_text_from_text(self, file_data: bytes) -> str:
        """Extract text content from text file"""
        try:
            return file_data.decode('utf-8')
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ['latin-1', 'cp1252']:
                try:
                    return file_data.decode(encoding)
                except UnicodeDecodeError:
                    continue
            raise ValueError("Unable to decode text file with supported encodings")
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending punctuation
                sentence_end = max(
                    text.rfind('.', start, end),
                    text.rfind('!', start, end),
                    text.rfind('?', start, end)
                )
                if sentence_end > start:
                    end = sentence_end + 1
                # If no sentence boundary, try to break at word boundary
                elif text[end] != ' ':
                    word_boundary = text.rfind(' ', start, end)
                    if word_boundary > start:
                        end = word_boundary
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + chunk_size - overlap, end)
        
        return chunks

    # PUBLIC_INTERFACE
    def upload_document(self, filename: str, content_type: str, file_data: bytes, user_id: str) -> Document:
        """Upload and process a document"""
        document_id = str(uuid.uuid4())
        doc_type = self._get_document_type(filename, content_type)
        
        # Save file to disk
        file_path = os.path.join(UPLOAD_DIR, f"{document_id}_{filename}")
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Create document metadata
        document = Document(
            id=document_id,
            filename=filename,
            content_type=content_type,
            size=len(file_data),
            document_type=doc_type,
            user_id=user_id
        )
        
        # Save document metadata
        documents = self._load_documents()
        documents[document_id] = document.dict()
        self._save_documents(documents)
        
        return document
    
    # PUBLIC_INTERFACE
    def process_document(self, document_id: str) -> int:
        """Process document for text extraction and chunking"""
        documents = self._load_documents()
        document_data = documents.get(document_id)
        
        if not document_data:
            raise ValueError(f"Document {document_id} not found")
        
        document = Document(**document_data)
        
        # Load file content
        file_path = os.path.join(UPLOAD_DIR, f"{document_id}_{document.filename}")
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Extract text based on document type
        if document.document_type == DocumentType.PDF:
            text = self._extract_text_from_pdf(file_data)
        elif document.document_type == DocumentType.JSON:
            text = self._extract_text_from_json(file_data)
        else:
            text = self._extract_text_from_text(file_data)
        
        # Chunk the text
        text_chunks = self._chunk_text(text)
        
        # Create document chunks
        chunks = self._load_chunks()
        chunk_count = 0
        
        for i, chunk_text in enumerate(text_chunks):
            chunk_id = str(uuid.uuid4())
            chunk = DocumentChunk(
                id=chunk_id,
                document_id=document_id,
                content=chunk_text,
                chunk_index=i,
                start_char=text.find(chunk_text[:50]),  # Approximate start position
                end_char=text.find(chunk_text[:50]) + len(chunk_text)
            )
            chunks[chunk_id] = chunk.dict()
            chunk_count += 1
        
        # Update document as processed
        document_data["processed"] = True
        document_data["chunk_count"] = chunk_count
        documents[document_id] = document_data
        
        # Save updates
        self._save_chunks(chunks)
        self._save_documents(documents)
        
        return chunk_count
    
    # PUBLIC_INTERFACE
    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        documents = self._load_documents()
        document_data = documents.get(document_id)
        
        if document_data:
            return Document(**document_data)
        return None
    
    # PUBLIC_INTERFACE
    def get_user_documents(self, user_id: str) -> List[Document]:
        """Get all documents for a user"""
        documents = self._load_documents()
        user_docs = []
        
        for doc_data in documents.values():
            if doc_data.get("user_id") == user_id:
                user_docs.append(Document(**doc_data))
        
        return sorted(user_docs, key=lambda x: x.upload_date, reverse=True)
    
    # PUBLIC_INTERFACE
    def get_document_chunks(self, document_id: str) -> List[DocumentChunk]:
        """Get all chunks for a document"""
        chunks = self._load_chunks()
        doc_chunks = []
        
        for chunk_data in chunks.values():
            if chunk_data.get("document_id") == document_id:
                doc_chunks.append(DocumentChunk(**chunk_data))
        
        return sorted(doc_chunks, key=lambda x: x.chunk_index)
    
    # PUBLIC_INTERFACE
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its chunks"""
        documents = self._load_documents()
        document_data = documents.get(document_id)
        
        if not document_data:
            return False
        
        # Delete file
        file_path = os.path.join(UPLOAD_DIR, f"{document_id}_{document_data['filename']}")
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete chunks
        chunks = self._load_chunks()
        chunks_to_delete = [chunk_id for chunk_id, chunk_data in chunks.items() 
                           if chunk_data.get("document_id") == document_id]
        
        for chunk_id in chunks_to_delete:
            del chunks[chunk_id]
        
        # Delete document metadata
        del documents[document_id]
        
        # Save updates
        self._save_chunks(chunks)
        self._save_documents(documents)
        
        return True

# Global instance
document_service = DocumentService()
