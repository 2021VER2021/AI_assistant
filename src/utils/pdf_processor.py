import PyPDF2
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np
import pickle

class PDFProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def extract_text(self, pdf_file) -> str:
        """Extract text from PDF file."""
        text = ""
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text

    def process_text(self, text: str) -> tuple[List[str], bytes]:
        """Process text into chunks and generate embeddings."""
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Generate embeddings
        embeddings = self.model.encode(chunks)
        
        # Serialize embeddings
        embeddings_bytes = pickle.dumps(embeddings)
        
        return chunks, embeddings_bytes

    def process_pdf(self, pdf_file) -> tuple[str, List[str], bytes]:
        """Process PDF file and return text, chunks, and embeddings."""
        text = self.extract_text(pdf_file)
        chunks, embeddings = self.process_text(text)
        return text, chunks, embeddings

    @staticmethod
    def deserialize_embeddings(embeddings_bytes: bytes) -> np.ndarray:
        """Deserialize embeddings from bytes to numpy array."""
        return pickle.loads(embeddings_bytes)

    def find_similar_chunks(self, query: str, chunks: List[str], embeddings: np.ndarray, top_k: int = 3) -> List[tuple[str, float]]:
        """Find chunks most similar to query."""
        query_embedding = self.model.encode([query])[0]
        
        # Calculate similarities
        similarities = np.dot(embeddings, query_embedding)
        
        # Get top k chunks
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        return [(chunks[i], similarities[i]) for i in top_indices]
