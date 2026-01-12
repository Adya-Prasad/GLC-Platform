"""
ESG Document Summarizer Agent - v2
Smart, meaningful document analysis for Green Loan compliance.
Extracts clean, readable ESG insights from sustainability reports.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


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
    Smart ESG document analyzer.
    Focuses on extracting meaningful, readable insights.
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
            
            self.logger.info("Loading summarization model...")
            self._summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1,
                max_length=150,
                min_length=40,
                do_sample=False
            )
            
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
    
    def _clean_text(self, text: str) -> str:
        """Clean raw text for better processing."""
        # Remove excessive whitespace and newlines
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page numbers and headers
        text = re.sub(r'\bPage\s*\d+\b', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\bPg\s*\d+\b', '', text, flags=re.IGNORECASE)
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove standalone numbers (likely from tables/charts)
        text = re.sub(r'(?<!\w)\d{4,}(?!\w)', '', text)
        
        return text.strip()
    
    def _get_clean_sentences(self, text: str) -> List[str]:
        """Split text into clean, meaningful sentences."""
        text = self._clean_text(text)
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        clean_sentences = []
        for s in sentences:
            s = s.strip()
            # Filter out garbage sentences
            if len(s) < 30:  # Too short
                continue
            if len(s) > 500:  # Too long, likely merged
                continue
            if re.match(r'^[\d\s,.\-]+$', s):  # Only numbers
                continue
            if s.count(' ') < 3:  # Not enough words
                continue
            # Check for too many numbers (likely table data)
            num_count = len(re.findall(r'\d+', s))
            word_count = len(s.split())
            if num_count > word_count * 0.5:  # More than 50% numbers
                continue
            
            clean_sentences.append(s)
        
        return clean_sentences
    
    def _extract_meaningful_content(self, sentences: List[str], keywords: List[str], max_sentences: int = 3) -> str:
        """Extract meaningful sentences based on keywords."""
        relevant = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence contains keywords
            if any(kw in sentence_lower for kw in keywords):
                # Additional quality checks
                if self._is_quality_sentence(sentence):
                    relevant.append(sentence)
                    if len(relevant) >= max_sentences:
                        break
        
        if not relevant:
            return "Information not found in the document."
        
        # Join with proper spacing
        result = ' '.join(relevant)
        
        # Ensure it ends properly
        if not result.endswith('.'):
            result += '.'
        
        return result
    
    def _is_quality_sentence(self, sentence: str) -> bool:
        """Check if a sentence is meaningful and readable."""
        # Must have reasonable length
        if len(sentence) < 40 or len(sentence) > 400:
            return False
        
        # Must have enough words
        words = sentence.split()
        if len(words) < 6:
            return False
        
        # Should not be mostly numbers
        num_count = len(re.findall(r'\d+', sentence))
        if num_count > len(words) * 0.4:
            return False
        
        # Should have proper sentence structure (starts with capital, has verb-like words)
        if not sentence[0].isupper():
            return False
        
        # Check for common garbage patterns
        garbage_patterns = [
            r'^\d+\s*$',  # Just numbers
            r'^[A-Z]{2,}\s*$',  # Just acronyms
            r'Figure\s*\d+',  # Figure references
            r'Table\s*\d+',  # Table references
            r'See\s+annexure',  # References
            r'^\s*[-–—]\s*',  # Bullet points without content
        ]
        for pattern in garbage_patterns:
            if re.search(pattern, sentence, re.IGNORECASE):
                return False
        
        return True
    
    def _extract_metrics_smart(self, text: str) -> List[Dict[str, str]]:
        """Extract meaningful quantitative metrics."""
        metrics = []
        sentences = self._get_clean_sentences(text)
        
        # Define metric patterns with context requirements
        metric_patterns = [
            {
                'name': 'Total Emissions',
                'pattern': r'(?:total|overall)\s+(?:emissions?|carbon)\s*(?:of|:)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:tCO2e?|tonnes?)',
                'unit': 'tCO2e',
                'category': 'emissions'
            },
            {
                'name': 'Scope 1 Emissions',
                'pattern': r'scope\s*1\s*(?:emissions?)?\s*(?:of|:)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:tCO2e?|tonnes?)',
                'unit': 'tCO2e',
                'category': 'emissions'
            },
            {
                'name': 'Scope 2 Emissions',
                'pattern': r'scope\s*2\s*(?:emissions?)?\s*(?:of|:)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(?:tCO2e?|tonnes?)',
                'unit': 'tCO2e',
                'category': 'emissions'
            },
            {
                'name': 'Renewable Energy',
                'pattern': r'(\d{1,3}(?:\.\d+)?)\s*%\s*(?:of\s+)?(?:energy|electricity|power)\s+(?:from\s+)?renewable',
                'unit': '%',
                'category': 'energy'
            },
            {
                'name': 'Emission Reduction Target',
                'pattern': r'(?:reduce|reduction|cut)\s+(?:emissions?\s+)?(?:by\s+)?(\d{1,3}(?:\.\d+)?)\s*%',
                'unit': '%',
                'category': 'target'
            },
            {
                'name': 'Employees',
                'pattern': r'(\d{1,3}(?:,\d{3})*)\s+(?:employees?|staff|workforce)',
                'unit': 'people',
                'category': 'social'
            },
        ]
        
        for mp in metric_patterns:
            match = re.search(mp['pattern'], text, re.IGNORECASE)
            if match:
                value = match.group(1).replace(',', '')
                # Validate the value is reasonable
                try:
                    num_val = float(value)
                    if num_val > 0 and num_val < 1000000000:  # Reasonable range
                        metrics.append({
                            'metric': mp['name'],
                            'value': value,
                            'unit': mp['unit'],
                            'category': mp['category']
                        })
                except:
                    pass
        
        return metrics[:6]  # Limit to 6 metrics
    
    def _extract_answers(self, text: str) -> Dict[str, str]:
        """Extract answers to 5 key ESG questions with meaningful content."""
        sentences = self._get_clean_sentences(text)
        
        questions = {
            "Extract financial statements or financial performance information": {
                "keywords": ["revenue", "profit", "financial performance", "turnover", "income", "earnings", "growth rate", "fiscal year", "annual report"],
                "max_sentences": 2
            },
            "Extract waste management practices": {
                "keywords": ["waste management", "recycling", "waste reduction", "circular economy", "zero waste", "waste disposal", "hazardous waste"],
                "max_sentences": 2
            },
            "Extract labor and employee practices": {
                "keywords": ["employee", "workforce", "training program", "safety", "diversity", "inclusion", "workplace", "human resources", "staff development"],
                "max_sentences": 2
            },
            "Extract renewable energy usage or plans": {
                "keywords": ["renewable energy", "solar", "wind power", "clean energy", "green energy", "energy efficiency", "carbon neutral", "net zero"],
                "max_sentences": 2
            },
            "Extract environmental protection and pollution control measures": {
                "keywords": ["environmental protection", "pollution control", "emission reduction", "climate action", "biodiversity", "conservation", "sustainability initiative"],
                "max_sentences": 2
            }
        }
        
        answers = {}
        for question, config in questions.items():
            answer = self._extract_meaningful_content(
                sentences, 
                config["keywords"], 
                config["max_sentences"]
            )
            answers[question] = answer
        
        return answers
    
    def _identify_essential_points(self, sentences: List[str], metrics: List[Dict]) -> List[Dict[str, Any]]:
        """Identify key essential points with clean descriptions."""
        points = []
        
        topics = [
            ("Climate Commitment", ["climate action", "net zero", "carbon neutral", "emission reduction", "climate target"], "critical"),
            ("Renewable Energy", ["renewable energy", "solar power", "wind energy", "clean energy", "green power"], "high"),
            ("Sustainability Goals", ["sustainability target", "2030 goal", "2050 target", "sdg", "sustainable development"], "high"),
            ("Environmental Management", ["environmental management", "iso 14001", "environmental policy", "eco-friendly"], "medium"),
            ("Social Responsibility", ["employee welfare", "community engagement", "diversity inclusion", "safety program"], "medium"),
        ]
        
        for title, keywords, importance in topics:
            content = self._extract_meaningful_content(sentences, keywords, max_sentences=2)
            if "not found" not in content.lower():
                points.append({
                    "title": title,
                    "description": content,
                    "importance": importance,
                    "category": "compliance"
                })
        
        # Add top metrics as points
        for metric in metrics[:2]:
            points.append({
                "title": metric['metric'],
                "description": f"Reported value: {metric['value']} {metric['unit']}",
                "importance": "high",
                "category": "quantitative"
            })
        
        return points[:6]  # Limit to 6 points
    
    def _generate_summary(self, text: str) -> str:
        """Generate a clean summary."""
        self._ensure_models()
        
        # Get clean text for summarization
        clean_text = self._clean_text(text)
        
        # Take first ~3000 chars for summarization
        chunk = clean_text[:3000]
        
        if len(chunk) < 200:
            return "Document content insufficient for summary generation."
        
        try:
            result = self._summarizer(chunk, max_length=150, min_length=50)
            summary = result[0]['summary_text']
            
            # Clean up the summary
            summary = re.sub(r'\s+', ' ', summary).strip()
            if not summary.endswith('.'):
                summary += '.'
            
            return summary
        except Exception as e:
            self.logger.warning(f"Summarization failed: {e}")
            return "Summary generation failed."
    
    def analyze_loan_documents(self, loan_id: int) -> ESGAnalysisResult:
        """Analyze documents for a loan application."""
        from app.ai_services.config import settings
        
        loan_dir = settings.UPLOAD_DIR / f"LOAN_{loan_id}"
        
        if not loan_dir.exists():
            self.logger.warning(f"Loan directory not found: {loan_dir}")
            return self._empty_result("No documents found for this loan.")
        
        # Only use sustainability report
        doc_files = ["sustainability_report.pdf", "sustainability_report.docx"]
        
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
        
        # Get clean sentences for analysis
        sentences = self._get_clean_sentences(full_text)
        self.logger.info(f"Found {len(sentences)} quality sentences")
        
        # Extract metrics
        metrics = self._extract_metrics_smart(full_text)
        
        # Extract answers
        answers = self._extract_answers(full_text)
        
        # Generate summary
        summary = self._generate_summary(full_text)
        
        # Identify essential points
        essential_points = self._identify_essential_points(sentences, metrics)
        
        # Build qualitative data from answers
        qualitative = []
        for q, a in answers.items():
            if "not found" not in a.lower():
                short_topic = q.replace("Extract ", "").replace(" information", "").title()
                qualitative.append({
                    "topic": short_topic[:50],
                    "description": a,
                    "lma_component": "ESG Disclosure",
                    "source": "sustainability_report"
                })
        
        confidence = 0.8 if (metrics or qualitative) else 0.4
        
        return ESGAnalysisResult(
            summary=summary,
            key_metrics=metrics,
            essential_points=essential_points,
            extraction_answers=answers,
            quantitative_data=metrics,
            qualitative_data=qualitative,
            confidence=confidence,
            pages_analyzed=total_pages,
            method="smart-extraction-v2"
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
    """Main entry point for document analysis."""
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
