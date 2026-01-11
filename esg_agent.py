#!/usr/bin/env python3
"""
ESG RAG Analyzer for LMA (Loan Management Association)
Automated document analysis for ESG compliance and reporting
"""

import os
import sys
import json
import logging
import argparse
import time
from pathlib import Path
from typing import List, Dict, Tuple

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_community.document_loaders import (
    UnstructuredPDFLoader, 
    CSVLoader, 
    TextLoader,
    Docx2txtLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from esg_helpers import (
    validate_document_path,
    format_json_response,
    get_esg_questions,
    log_processing_start,
    log_processing_end,
    save_results_to_file
)

# Model Configuration
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# RAG Configuration
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 400
RETRIEVAL_K = 7  # Retrieve more chunks for ESG documents


class ESGRAGAnalyzer:
    """ESG Document Analyzer using RAG"""
    
    def __init__(self, model_name=MODEL_NAME, embedding_model=EMBEDDING_MODEL):
        self.model_name = model_name
        self.embedding_model = embedding_model
        self.llm = None
        self.embeddings = None
        self.vector_db = None
        
        logging.info(f"Initializing ESG RAG Analyzer on device: {DEVICE}")
    
    def load_embeddings(self):
        """Load embedding model"""
        logging.info(f"Loading embedding model: {self.embedding_model}")
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={'device': DEVICE},
                encode_kwargs={'normalize_embeddings': True}
            )
            logging.info("Embedding model loaded successfully")
        except Exception as e:
            logging.error(f"Failed to load embedding model: {e}")
            raise
    
    def load_llm(self):
        """Load language model"""
        logging.info(f"Loading language model: {self.model_name}")
        try:
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if DEVICE == "cuda" else torch.float32,
                device_map="auto" if DEVICE == "cuda" else None,
                low_cpu_mem_usage=True,
            )
            
            text_gen_pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512,
                temperature=0.1,
                top_p=0.95,
                repetition_penalty=1.15,
                do_sample=True,
            )
            
            self.llm = HuggingFacePipeline(pipeline=text_gen_pipeline)
            logging.info("Language model loaded successfully")
            
        except Exception as e:
            logging.error(f"Failed to load language model: {e}")
            raise
    
    def load_document(self, doc_path: str) -> List:
        """Load document based on file type"""
        logging.info(f"Loading document: {doc_path}")
        
        path = Path(doc_path)
        ext = path.suffix.lower()
        
        try:
            if ext == ".pdf":
                loader = UnstructuredPDFLoader(file_path=doc_path)
            elif ext in [".docx", ".doc"]:
                loader = Docx2txtLoader(doc_path)
            elif ext == ".csv":
                loader = CSVLoader(file_path=doc_path, encoding="utf-8")
            elif ext in [".json", ".txt"]:
                loader = TextLoader(doc_path, encoding="utf-8")
            else:
                # Fallback to text loader
                loader = TextLoader(doc_path, encoding="utf-8")
            
            docs = loader.load()
            logging.info(f"Loaded {len(docs)} document(s)")
            return docs
            
        except Exception as e:
            logging.error(f"Error loading document: {e}")
            raise
    
    def split_documents(self, documents: List) -> List:
        """Split documents into chunks"""
        logging.info("Splitting documents into chunks...")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        
        chunks = text_splitter.split_documents(documents)
        logging.info(f"Created {len(chunks)} chunks")
        return chunks
    
    def create_vector_db(self, chunks: List):
        """Create vector database from chunks"""
        logging.info("Creating vector database...")
        
        try:
            self.vector_db = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                collection_name="esg_docs"
            )
            logging.info("Vector database created successfully")
        except Exception as e:
            logging.error(f"Error creating vector database: {e}")
            raise
    
    def create_rag_chain(self):
        """Create RAG chain for question answering"""
        template = """<s>[INST] You are an ESG (Environmental, Social, Governance) analysis expert working for LMA (Loan Management Association). 
Your task is to extract precise information from ESG reports and loan documentation.

Instructions:
- Answer based ONLY on the provided context
- Be specific and provide exact values, numbers, and metrics when available
- If the information is not in the context, respond with "NOT FOUND"
- For financial data (CapEx, OpEx), include currency and time period if mentioned
- For emissions data, include units (e.g., tCO2e, mtCO2e)
- For KPIs, list each one with its baseline value clearly
- Be concise but complete

Context from ESG Document:
{context}

Question: {question}

Provide a direct, factual answer: [/INST]
"""
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | StrOutputParser()
        return chain
    
    def answer_question(self, question: str) -> str:
        """Answer a single question using RAG"""
        try:
            # Retrieve relevant documents
            retriever = self.vector_db.as_retriever(
                search_type="similarity",
                search_kwargs={"k": RETRIEVAL_K}
            )
            
            relevant_docs = retriever.get_relevant_documents(question)
            
            if not relevant_docs:
                return "NOT FOUND"
            
            # Format context
            context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Generate answer
            rag_chain = self.create_rag_chain()
            answer = rag_chain.invoke({"context": context, "question": question})
            
            # Clean up answer
            answer = answer.strip()
            
            # Check if answer indicates not found
            if not answer or len(answer) < 5 or "not found" in answer.lower() or "not mentioned" in answer.lower():
                return "NOT FOUND"
            
            return answer
            
        except Exception as e:
            logging.error(f"Error answering question '{question}': {e}")
            return "NOT FOUND"
    
    def analyze_document(self, doc_path: str, questions: List[str] = None) -> Dict:
        """
        Main analysis function
        
        Args:
            doc_path: Path to the ESG document
            questions: List of questions to answer (uses default ESG questions if None)
        
        Returns:
            Dictionary with analysis results
        """
        start_time = time.time()
        
        # Validate document
        if not validate_document_path(doc_path):
            raise ValueError(f"Invalid document path: {doc_path}")
        
        log_processing_start(doc_path)
        
        # Use default ESG questions if none provided
        if questions is None:
            questions = get_esg_questions()
        
        logging.info(f"Total questions to analyze: {len(questions)}")
        
        try:
            # Load models
            if self.embeddings is None:
                self.load_embeddings()
            if self.llm is None:
                self.load_llm()
            
            # Process document
            docs = self.load_document(doc_path)
            chunks = self.split_documents(docs)
            self.create_vector_db(chunks)
            
            # Answer all questions
            answers = []
            for i, question in enumerate(questions, 1):
                logging.info(f"Processing question {i}/{len(questions)}: {question[:50]}...")
                answer = self.answer_question(question)
                answers.append(answer)
                logging.info(f"Answer: {answer[:100]}...")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Format results
            metadata = {
                "document_path": doc_path,
                "processing_time": f"{processing_time:.2f}s",
                "chunks_processed": len(chunks),
                "model_used": self.model_name
            }
            
            result = format_json_response(questions, answers, metadata)
            
            log_processing_end(success=True)
            
            return result
            
        except Exception as e:
            logging.error(f"Analysis failed: {e}")
            log_processing_end(success=False)
            raise


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description='ESG RAG Analyzer for LMA - Automated ESG Document Analysis'
    )
    parser.add_argument(
        'document_path',
        type=str,
        help='Path to the ESG document (PDF, DOCX, TXT, CSV, JSON)'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='Output JSON file path (default: auto-generated)'
    )
    parser.add_argument(
        '-q', '--questions',
        type=str,
        default=None,
        help='Path to custom questions JSON file (default: uses built-in ESG questions)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=MODEL_NAME,
        help=f'LLM model to use (default: {MODEL_NAME})'
    )
    parser.add_argument(
        '--embedding-model',
        type=str,
        default=EMBEDDING_MODEL,
        help=f'Embedding model to use (default: {EMBEDDING_MODEL})'
    )
    
    args = parser.parse_args()
    
    # Load custom questions if provided
    questions = None
    if args.questions:
        try:
            with open(args.questions, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
                questions = questions_data.get('questions', questions_data)
        except Exception as e:
            logging.error(f"Failed to load custom questions: {e}")
            sys.exit(1)
    
    # Initialize analyzer
    analyzer = ESGRAGAnalyzer(
        model_name=args.model,
        embedding_model=args.embedding_model
    )
    
    try:
        # Run analysis
        results = analyzer.analyze_document(args.document_path, questions)
        
        # Output to console (JSON)
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
        # Save to file
        output_file = save_results_to_file(results, args.output)
        
        if output_file:
            logging.info(f"\n✓ Analysis complete! Results saved to: {output_file}")
        
        sys.exit(0)
        
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        error_response = {
            "error": str(e),
            "status": "failed",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        print(json.dumps(error_response, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()