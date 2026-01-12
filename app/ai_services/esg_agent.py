"""
ESG Document Summarizer Agent
Lightweight, fast document analysis for Green Loan compliance.
Extracts key ESG metrics and facts from sustainability reports.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ============ DATA CLASSES ============
@dataclass
class ESGAnalysisResult:
    """Result of ESG document analysis."""
    summary: str
    key_metrics: List[Dict[str, str]]
    essential_points: List[Dict[str, Any]]
    extraction_answers: Dict[str, str]
    quantitative_data: List[Dict[str, Any]]
    qualitative_data: List[Dict[str, Any]]
    confidence: float
    pages_analyzed: int
    method: str


class ESGAgent:
    """
    Lightweight ESG document analyzer.
    Uses smaller models for faster inference.
    """
    
    def __init__(self):
        self._summarizer = None
        self._extractor = None
        self.logger = logging.getLogger(f"{__name__}.ESGAgent")
    
    def _ensure_models(self):
        """Lazy load models only when needed."""
        if self._summarizer is not None:
            return
        
        try:
            from transformers import pipeline
            
            # Use smaller, faster model for summarization
            self.logger.info("Loading summarization model...")
            self._summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1,  # CPU
                max_length=150,
                min_length=40,
                do_sample=False
            )
            
            # Use QA model for metric extraction
            self.logger.info("Loading QA model...")
            self._extractor = pipeline(
                "question-answering",
                model="distilbert-base-cased-distilled-squad",
                device=-1
            )
            
            self.logger.info("Models loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load models: {e}")
            raise
    
    def _extract_text_from_pdf(self, filepath: str) -> tuple:
        """Extract text from PDF file."""
        text = ""
        page_count = 0
        
        try:
            from pdfminer.high_level import extract_text
            from pdfminer.pdfpage import PDFPage
            
            text = extract_text(filepath)
            with open(filepath, 'rb') as f:
                page_count = len(list(PDFPage.get_pages(f)))
            
            if text and len(text.strip()) > 100:
                return text.strip(), page_count
        except Exception as e:
            self.logger.warning(f"pdfminer failed: {e}")
        
        # Fallback to PyPDF2
        try:
            import PyPDF2
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                page_count = len(reader.pages)
                pages = [page.extract_text() or "" for page in reader.pages]
                text = "\n".join(pages)
        except Exception as e:
            self.logger.warning(f"PyPDF2 failed: {e}")
        
        return text.strip(), page_count
    
    def _extract_text_from_docx(self, filepath: str) -> tuple:
        """Extract text from DOCX file."""
        try:
            from docx import Document
            doc = Document(filepath)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs)
            page_count = max(1, len(text.split()) // 500)
            return text, page_count
        except Exception as e:
            self.logger.error(f"DOCX extraction failed: {e}")
            return "", 0
    
    def _chunk_text(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into chunks for processing."""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk = ' '.join(words[i:i + chunk_size])
            if len(chunk) > 100:  # Skip tiny chunks
                chunks.append(chunk)
        
        return chunks
    
    def _extract_metrics(self, text: str) -> List[Dict[str, str]]:
        """Extract quantitative metrics from text using pattern matching."""
        import re
        
        metrics = []
        
        # Patterns for common ESG metrics - improved to avoid garbage
        patterns = [
            (r'(?:scope\s*1|scope1)[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:tCO2e?|tonnes?)', 'Scope 1 Emissions', 'tCO2e'),
            (r'(?:scope\s*2|scope2)[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:tCO2e?|tonnes?)', 'Scope 2 Emissions', 'tCO2e'),
            (r'(?:scope\s*3|scope3)[:\s]+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:tCO2e?|tonnes?)', 'Scope 3 Emissions', 'tCO2e'),
            (r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:tCO2e?|tonnes?\s+CO2)', 'Total Emissions', 'tCO2e'),
            (r'(\d{1,2}(?:\.\d+)?)\s*%\s*(?:renewable|clean\s+energy)', 'Renewable Energy', '%'),
            (r'(\d{1,3}(?:,\d{3})*)\s*(?:MW|GW)\s*(?:renewable|solar|wind|capacity)', 'Renewable Capacity', 'MW'),
            (r'(?:revenue|turnover)[:\s]*(?:USD|INR|EUR|\$|₹|€)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|mn|bn|cr|crore)?', 'Revenue', 'USD'),
            (r'(\d{1,2}(?:\.\d+)?)\s*%\s*(?:reduction|decrease|avoided)', 'Emission Reduction', '%'),
            (r'(\d{1,3}(?:,\d{3})*)\s*(?:employees?|workforce|staff)', 'Employees', 'people'),
        ]
        
        for pattern, metric_name, unit in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:2]:  # Limit to 2 per category
                value = match.replace(',', '') if isinstance(match, str) else str(match)
                # Skip garbage values (too long numbers)
                if len(value) < 15:
                    metrics.append({
                        'metric': metric_name,
                        'value': value,
                        'unit': unit,
                        'category': metric_name.lower().replace(' ', '_')
                    })
        
        # Remove duplicates
        seen = set()
        unique_metrics = []
        for m in metrics:
            key = f"{m['metric']}_{m['value']}"
            if key not in seen:
                seen.add(key)
                unique_metrics.append(m)
        
        return unique_metrics[:8]  # Limit total metrics
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and format extracted text for better readability."""
        import re
        
        if not text or "not clearly stated" in text.lower():
            return text
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove page numbers and headers like "Pg 03", "Page 12"
        text = re.sub(r'\bPg\s*\d+\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bPage\s*\d+\b', '', text, flags=re.IGNORECASE)
        
        # Remove standalone numbers that look like page refs
        text = re.sub(r'\s+\d{1,2}\s+(?=\d{1,2}\s+)', ' ', text)
        
        # Remove repeated words/phrases
        words = text.split()
        cleaned_words = []
        prev_word = ""
        for word in words:
            if word.lower() != prev_word.lower():
                cleaned_words.append(word)
            prev_word = word
        text = ' '.join(cleaned_words)
        
        # Ensure proper sentence spacing
        text = re.sub(r'\.(?=[A-Z])', '. ', text)
        
        # Remove garbage characters
        text = re.sub(r'[^\w\s.,;:!?\'\"()\-–—%$€£₹@&/]', '', text)
        
        # Trim to reasonable length and end at sentence boundary
        if len(text) > 800:
            # Find last sentence end before 800 chars
            last_period = text[:800].rfind('.')
            if last_period > 400:
                text = text[:last_period + 1]
            else:
                text = text[:800] + '...'
        
        return text.strip()
    
    def _extract_section(self, text: str, keywords: List[str], max_length: int = 1500) -> str:
        """Extract relevant section from text based on keywords - returns longer, comprehensive responses."""
        import re
        
        # Clean text
        clean_text = re.sub(r'\s+', ' ', text.replace('\n', ' ')).strip()
        sentences = re.split(r'(?<=[.!?])\s+', clean_text)
        
        relevant_sentences = []
        context_buffer = []
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 15:
                continue
            
            sentence_lower = sentence.lower()
            
            # Check if sentence contains any keyword
            if any(kw in sentence_lower for kw in keywords):
                # Add previous sentence for context if available
                if context_buffer and context_buffer[-1] not in relevant_sentences:
                    relevant_sentences.append(context_buffer[-1])
                
                relevant_sentences.append(sentence)
                
                # Add next 2 sentences for more context
                for j in range(1, 3):
                    if i + j < len(sentences) and len(sentences[i + j].strip()) > 15:
                        next_sent = sentences[i + j].strip()
                        if next_sent not in relevant_sentences:
                            relevant_sentences.append(next_sent)
            
            # Keep track of recent sentences for context
            context_buffer.append(sentence)
            if len(context_buffer) > 2:
                context_buffer.pop(0)
            
            # Stop if we have enough content
            if len(' '.join(relevant_sentences)) > max_length:
                break
        
        if relevant_sentences:
            # Remove duplicates while preserving order
            seen = set()
            unique = []
            for s in relevant_sentences:
                if s not in seen:
                    seen.add(s)
                    unique.append(s)
            
            result = ' '.join(unique[:10])  # Max 10 sentences
            # Clean the result for better readability
            return self._clean_extracted_text(result) if result else "Information not clearly stated in the document."
        
        return "Information not clearly stated in the document."
    
    def _extract_answers(self, text: str) -> Dict[str, str]:
        """Extract answers to 5 key ESG questions using keyword-based extraction."""
        
        # 5 questions with comprehensive keywords for better extraction
        questions = {
            "Financial Performance": {
                "keywords": ["revenue", "profit", "financial", "turnover", "income", "earnings", "growth", "fiscal", "fy", "million", "billion", "crore", "sales", "operating", "net income", "gross", "ebitda", "assets", "capital", "investment"],
                "question": "Extract financial statements or financial performance information"
            },
            "Waste Management": {
                "keywords": ["waste", "recycling", "circular", "disposal", "landfill", "reuse", "reduce", "recycle", "hazardous waste", "e-waste", "solid waste", "waste reduction", "zero waste", "waste treatment", "composting", "plastic"],
                "question": "Extract waste management practices"
            },
            "Labor & Employees": {
                "keywords": ["employee", "workforce", "staff", "labor", "workers", "training", "safety", "diversity", "inclusion", "human resources", "hr", "workplace", "occupational", "health and safety", "talent", "hiring", "retention", "benefits", "compensation"],
                "question": "Extract labor and employee practices"
            },
            "Renewable Energy": {
                "keywords": ["renewable", "solar", "wind", "clean energy", "green energy", "hydro", "biomass", "energy efficiency", "carbon neutral", "net zero", "photovoltaic", "pv", "wind power", "geothermal", "energy transition", "decarbonization", "green power"],
                "question": "Extract renewable energy usage or plans"
            },
            "Environmental Protection": {
                "keywords": ["environment", "pollution", "emission", "carbon", "climate", "biodiversity", "conservation", "sustainability", "eco", "green", "ghg", "co2", "greenhouse", "air quality", "water quality", "soil", "ecosystem", "nature", "environmental impact", "mitigation"],
                "question": "Extract environmental protection and pollution control measures"
            }
        }
        
        answers = {}
        
        for title, config in questions.items():
            extracted = self._extract_section(text, config["keywords"], max_length=1500)
            answers[config["question"]] = extracted
        
        return answers
    
    def _generate_summary(self, text: str) -> str:
        """Generate comprehensive summary of the document."""
        self._ensure_models()
        
        # Chunk and summarize
        chunks = self._chunk_text(text, chunk_size=800)
        
        if not chunks:
            return "Document too short to summarize."
        
        summaries = []
        for i, chunk in enumerate(chunks[:6]):  # Process up to 6 chunks for more coverage
            try:
                result = self._summarizer(chunk, max_length=120, min_length=40)
                summaries.append(result[0]['summary_text'])
            except Exception as e:
                self.logger.warning(f"Summarization failed for chunk {i}: {e}")
        
        if not summaries:
            return "Could not generate summary."
        
        # Combine summaries into comprehensive overview
        combined = " ".join(summaries)
        
        # If combined is very long, do a final summarization pass
        if len(combined.split()) > 300:
            try:
                final = self._summarizer(combined, max_length=200, min_length=80)
                return final[0]['summary_text']
            except:
                return combined[:800]
        
        return combined
    
    def _identify_essential_points(self, text: str, metrics: List[Dict]) -> List[Dict[str, Any]]:
        """Identify essential points for loan assessment - returns longer descriptions."""
        import re
        
        points = []
        text_lower = text.lower()
        
        # Clean text for better sentence extraction
        clean_text = re.sub(r'\s+', ' ', text.replace('\n', ' ')).strip()
        sentences = re.split(r'(?<=[.!?])\s+', clean_text)
        
        # Check for key ESG topics
        topics = [
            ("Carbon Emissions", ["emission", "carbon", "co2", "greenhouse", "ghg", "scope 1", "scope 2"], "critical"),
            ("Renewable Energy", ["renewable", "solar", "wind", "clean energy", "green power"], "high"),
            ("Sustainability Targets", ["target", "goal", "commitment", "pledge", "2030", "2050", "net zero"], "high"),
            ("Certifications & Compliance", ["compliance", "regulation", "standard", "certified", "iso", "audit"], "medium"),
            ("Waste Management", ["waste", "recycling", "circular", "disposal", "reduce"], "medium"),
            ("Water Conservation", ["water", "wastewater", "conservation", "effluent"], "medium"),
            ("Social Responsibility", ["employee", "community", "safety", "diversity", "training", "workforce"], "medium"),
            ("Environmental Impact", ["biodiversity", "ecosystem", "pollution", "environmental", "habitat"], "medium"),
        ]
        
        for topic, keywords, importance in topics:
            if any(kw in text_lower for kw in keywords):
                # Find multiple relevant sentences for longer description
                relevant = []
                for sentence in sentences:
                    if any(kw in sentence.lower() for kw in keywords) and len(sentence.strip()) > 20:
                        relevant.append(sentence.strip())
                        if len(' '.join(relevant)) > 400:  # Longer descriptions
                            break
                
                if relevant:
                    description = ' '.join(relevant[:3])  # Up to 3 sentences
                    # Clean the description
                    description = self._clean_extracted_text(description)
                    points.append({
                        "title": topic,
                        "description": description,
                        "importance": importance,
                        "category": "compliance"
                    })
        
        # Add metrics as essential points with context
        for metric in metrics[:4]:
            # Find sentence containing this metric value for context
            metric_context = ""
            for sentence in sentences:
                if metric['value'] in sentence:
                    metric_context = sentence.strip()
                    break
            
            points.append({
                "title": f"{metric['metric']}",
                "description": f"{metric['value']} {metric['unit']}" + (f" - {metric_context}" if metric_context else ""),
                "importance": "high",
                "category": "quantitative"
            })
        
        return points[:10]  # Limit to 10 points
    
    def analyze_loan_documents(self, loan_id: int) -> ESGAnalysisResult:
        """
        Analyze all documents for a loan application.
        
        Args:
            loan_id: The loan application ID
            
        Returns:
            ESGAnalysisResult with extracted data
        """
        from app.ai_services.config import settings
        
        loan_dir = settings.UPLOAD_DIR / f"LOAN_{loan_id}"
        
        if not loan_dir.exists():
            self.logger.warning(f"Loan directory not found: {loan_dir}")
            return self._empty_result("No documents found for this loan.")
        
        # Only use sustainability report
        doc_files = [
            "sustainability_report.pdf",
            "sustainability_report.docx",
        ]
        
        full_text = ""
        total_pages = 0
        
        for doc_name in doc_files:
            doc_path = loan_dir / doc_name
            if doc_path.exists():
                self.logger.info(f"Processing: {doc_path}")
                
                if doc_name.endswith('.pdf'):
                    text, pages = self._extract_text_from_pdf(str(doc_path))
                else:
                    text, pages = self._extract_text_from_docx(str(doc_path))
                
                if text:
                    full_text += f"\n\n{text}"
                    total_pages += pages
        
        if not full_text or len(full_text.strip()) < 100:
            return self._empty_result("No readable content found in documents.")
        
        self.logger.info(f"Extracted {len(full_text)} chars from {total_pages} pages")
        
        # Extract metrics
        metrics = self._extract_metrics(full_text)
        
        # Extract answers to 5 key ESG questions (keyword-based)
        answers = self._extract_answers(full_text)
        
        # Generate summary (longer, more detailed)
        summary = self._generate_summary(full_text)
        
        # Identify essential points
        essential_points = self._identify_essential_points(full_text, metrics)
        
        return ESGAnalysisResult(
            summary=summary,
            key_metrics=metrics,
            essential_points=essential_points,
            extraction_answers=answers,
            quantitative_data=[m for m in metrics if m['category'] in ['emissions', 'scope_emissions', 'energy', 'total_emissions', 'renewable_energy']],
            qualitative_data=[{"topic": k, "description": v, "lma_component": "Use of Proceeds", "source": "sustainability_report"} 
                            for k, v in answers.items() if "not clearly stated" not in v.lower()],
            confidence=0.75 if metrics or any("not clearly stated" not in v.lower() for v in answers.values()) else 0.3,
            pages_analyzed=total_pages,
            method="bart-cnn + keyword-extraction"
        )
    
    def _empty_result(self, message: str) -> ESGAnalysisResult:
        """Return empty result with message."""
        return ESGAnalysisResult(
            summary=message,
            key_metrics=[],
            essential_points=[],
            extraction_answers={},
            quantitative_data=[],
            qualitative_data=[],
            confidence=0.0,
            pages_analyzed=0,
            method="none"
        )


# Singleton instance
esg_agent = ESGAgent()


def analyze_documents(loan_id: int) -> Dict[str, Any]:
    """
    Main entry point for document analysis.
    Called by the API endpoint.
    """
    result = esg_agent.analyze_loan_documents(loan_id)
    
    return {
        "loan_id": loan_id,
        "summary": result.summary,
        "quantitative_data": result.quantitative_data,
        "qualitative_data": result.qualitative_data,
        "essential_points": result.essential_points,
        "extraction_answers": result.extraction_answers,
        "glp_coverage": {},
        "sllp_coverage": {},
        "confidence": result.confidence,
        "pages_analyzed": result.pages_analyzed,
        "method": result.method
    }
