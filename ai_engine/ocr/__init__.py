"""
OCR Module for extracting text from documents.
Supports PDF, scanned images, and various image formats.
Languages: Uzbek (Latin/Cyrillic), Russian
"""

import os
import io
import logging
from typing import Optional, Tuple, List
from pathlib import Path

import pytesseract
from PIL import Image
from pdf2image import convert_from_path, convert_from_bytes
import pdfplumber

logger = logging.getLogger(__name__)


class OCRProcessor:
    """
    OCR processor for extracting text from documents.
    Uses Tesseract for OCR and pdfplumber for native PDF text.
    """
    
    # Language codes for Tesseract
    LANGUAGE_MAP = {
        'uz-latn': 'uzb_latn',  # Uzbek Latin
        'uz-cyrl': 'uzb',       # Uzbek Cyrillic
        'ru': 'rus',            # Russian
        'eng': 'eng',           # English
    }
    
    def __init__(self, languages: List[str] = None):
        """
        Initialize OCR processor.
        
        Args:
            languages: List of language codes to use for OCR
        """
        self.languages = languages or ['uzb', 'uzb_latn', 'rus']
        self.tesseract_lang = '+'.join(self.languages)
        
        # Verify Tesseract is installed
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            logger.warning(f"Tesseract not properly configured: {e}")
    
    def extract_text_from_file(self, file_path: str) -> Tuple[str, float, bool]:
        """
        Extract text from a file (PDF, image, or Word document).
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (extracted_text, confidence_score, is_scanned)
        """
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        if extension == '.pdf':
            return self._process_pdf(file_path)
        elif extension in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp', '.gif']:
            return self._process_image(file_path)
        elif extension in ['.docx', '.doc']:
            return self._process_word(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    
    def extract_text_from_bytes(self, file_bytes: bytes, file_type: str) -> Tuple[str, float, bool]:
        """
        Extract text from file bytes.
        
        Args:
            file_bytes: File content as bytes
            file_type: File extension (e.g., 'pdf', 'jpg')
            
        Returns:
            Tuple of (extracted_text, confidence_score, is_scanned)
        """
        if file_type == 'pdf':
            return self._process_pdf_bytes(file_bytes)
        elif file_type in ['jpg', 'jpeg', 'png', 'tiff', 'bmp']:
            return self._process_image_bytes(file_bytes)
        else:
            raise ValueError(f"Unsupported file format: {file_type}")
    
    def _process_pdf(self, file_path: Path) -> Tuple[str, float, bool]:
        """Process PDF file."""
        text = ""
        is_scanned = False
        confidence = 1.0
        
        # First try to extract native text
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
        
        # If no text found, try OCR
        if not text.strip():
            is_scanned = True
            text, confidence = self._ocr_pdf(file_path)
        
        return text.strip(), confidence, is_scanned
    
    def _process_pdf_bytes(self, file_bytes: bytes) -> Tuple[str, float, bool]:
        """Process PDF from bytes."""
        text = ""
        is_scanned = False
        confidence = 1.0
        
        # First try to extract native text
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
        
        # If no text found, try OCR
        if not text.strip():
            is_scanned = True
            images = convert_from_bytes(file_bytes)
            text, confidence = self._ocr_images(images)
        
        return text.strip(), confidence, is_scanned
    
    def _ocr_pdf(self, file_path: Path) -> Tuple[str, float]:
        """Perform OCR on PDF pages."""
        images = convert_from_path(str(file_path))
        return self._ocr_images(images)
    
    def _ocr_images(self, images: List[Image.Image]) -> Tuple[str, float]:
        """Perform OCR on a list of images."""
        all_text = []
        confidences = []
        
        for img in images:
            # Get detailed OCR data
            data = pytesseract.image_to_data(
                img,
                lang=self.tesseract_lang,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text
            page_text = pytesseract.image_to_string(
                img,
                lang=self.tesseract_lang
            )
            all_text.append(page_text)
            
            # Calculate confidence
            conf_values = [int(c) for c in data['conf'] if int(c) > 0]
            if conf_values:
                confidences.append(sum(conf_values) / len(conf_values))
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        return "\n".join(all_text), avg_confidence / 100
    
    def _process_image(self, file_path: Path) -> Tuple[str, float, bool]:
        """Process image file."""
        img = Image.open(file_path)
        text, confidence = self._ocr_single_image(img)
        return text, confidence, True
    
    def _process_image_bytes(self, file_bytes: bytes) -> Tuple[str, float, bool]:
        """Process image from bytes."""
        img = Image.open(io.BytesIO(file_bytes))
        text, confidence = self._ocr_single_image(img)
        return text, confidence, True
    
    def _ocr_single_image(self, img: Image.Image) -> Tuple[str, float]:
        """Perform OCR on a single image."""
        # Preprocessing for better OCR
        img = self._preprocess_image(img)
        
        # Get OCR data
        data = pytesseract.image_to_data(
            img,
            lang=self.tesseract_lang,
            output_type=pytesseract.Output.DICT
        )
        
        # Extract text
        text = pytesseract.image_to_string(img, lang=self.tesseract_lang)
        
        # Calculate confidence
        conf_values = [int(c) for c in data['conf'] if int(c) > 0]
        confidence = (sum(conf_values) / len(conf_values) / 100) if conf_values else 0
        
        return text.strip(), confidence
    
    def _preprocess_image(self, img: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results."""
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Increase size if too small
        width, height = img.size
        if width < 1000:
            ratio = 1000 / width
            img = img.resize((int(width * ratio), int(height * ratio)), Image.LANCZOS)
        
        return img
    
    def _process_word(self, file_path: Path) -> Tuple[str, float, bool]:
        """Process Word document."""
        from docx import Document
        
        doc = Document(file_path)
        text = []
        
        for paragraph in doc.paragraphs:
            text.append(paragraph.text)
        
        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text.append(cell.text)
        
        return "\n".join(text), 1.0, False
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the text.
        
        Returns:
            Language code: 'uz-latn', 'uz-cyrl', 'ru', or 'mixed'
        """
        # Cyrillic characters
        cyrillic = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')
        # Latin characters
        latin = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
        # Uzbek-specific Latin
        uzbek_latin = set("o'g'OʻGʻ")
        # Russian-specific (not in Uzbek Cyrillic)
        russian_specific = set('ъыэё')
        
        cyrillic_count = sum(1 for c in text if c in cyrillic)
        latin_count = sum(1 for c in text if c in latin)
        uzbek_latin_count = sum(1 for c in text if c in uzbek_latin)
        russian_count = sum(1 for c in text if c in russian_specific)
        
        total = cyrillic_count + latin_count
        
        if total == 0:
            return 'uz-latn'  # Default
        
        # Determine primary script
        if cyrillic_count > latin_count * 2:
            # Primarily Cyrillic
            if russian_count > 0:
                return 'ru'
            return 'uz-cyrl'
        elif latin_count > cyrillic_count * 2:
            # Primarily Latin
            return 'uz-latn'
        else:
            return 'mixed'


class PaddleOCRProcessor:
    """
    Alternative OCR processor using PaddleOCR.
    Better for complex layouts and Uzbek text.
    """
    
    def __init__(self):
        """Initialize PaddleOCR."""
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='cyrillic',  # Supports Cyrillic-based languages
                use_gpu=False
            )
            self.available = True
        except ImportError:
            logger.warning("PaddleOCR not installed")
            self.available = False
    
    def extract_text(self, image_path: str) -> Tuple[str, float]:
        """Extract text using PaddleOCR."""
        if not self.available:
            raise RuntimeError("PaddleOCR is not available")
        
        result = self.ocr.ocr(image_path)
        
        lines = []
        confidences = []
        
        for line in result[0]:
            text = line[1][0]
            confidence = line[1][1]
            lines.append(text)
            confidences.append(confidence)
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        return "\n".join(lines), avg_confidence
