import json
import aiohttp
from typing import List, Optional
import numpy as np
from utils.pdf_processor import PDFProcessor
from utils.web_search import WebSearcher
from database.db import get_db
from database.models import Document

class AIAgent:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.web_searcher = WebSearcher()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "deepseek-r1:7b"

    async def _query_ollama(self, prompt: str) -> str:
        """Query the Ollama model."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.ollama_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('response', '')
                else:
                    error_text = await response.text()
                    raise Exception(f"Ollama API error: {error_text}")

    def _get_relevant_documents(self, query: str, user_id: int) -> List[str]:
        """Get relevant document chunks for the query."""
        relevant_chunks = []
        
        with get_db() as db:
            documents = db.query(Document).filter(Document.user_id == user_id).all()
            
            for doc in documents:
                embeddings = self.pdf_processor.deserialize_embeddings(doc.embeddings)
                chunks = doc.content.split('\n\n')  # Assuming chunks were joined with double newlines
                
                similar_chunks = self.pdf_processor.find_similar_chunks(
                    query, chunks, embeddings, top_k=3
                )
                
                for chunk, score in similar_chunks:
                    if score > 0.3:  # Similarity threshold
                        relevant_chunks.append(chunk)
        
        return relevant_chunks

    async def process_query(self, query: str, user_id: int) -> str:
        """Process user query using RAG approach with web search and document knowledge."""
        # Get relevant document chunks
        doc_chunks = self._get_relevant_documents(query, user_id)
        
        # Get web search results
        web_results = self.web_searcher.search(query, max_results=3)
        formatted_web_results = self.web_searcher.format_results(web_results)
        
        # Construct prompt with context
        context = []
        
        if doc_chunks:
            context.append("Relevant information from documents:")
            context.extend(doc_chunks)
        
        if web_results:
            context.append("\nRelevant web search results:")
            context.append(formatted_web_results)
        
        if not context:
            context.append("No additional context found.")
        
        prompt = f"""Based on the following context, please answer the user's question.
If you use information from the context, cite the source (document or web link).
If the context doesn't help answer the question directly, use your general knowledge but mention this.

Context:
{" ".join(context)}

User question: {query}

Answer:"""

        # Get response from Ollama
        try:
            response = await self._query_ollama(prompt)
            return response
        except Exception as e:
            return f"Error generating response: {str(e)}"

    async def process_pdf(self, file, filename: str, user_id: int) -> bool:
        """Process and store PDF document."""
        try:
            # Process PDF
            text, chunks, embeddings = self.pdf_processor.process_pdf(file)
            
            # Store in database
            with get_db() as db:
                document = Document(
                    user_id=user_id,
                    filename=filename,
                    content='\n\n'.join(chunks),  # Join chunks with double newlines
                    embeddings=embeddings
                )
                db.add(document)
                db.commit()
            
            return True
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return False
