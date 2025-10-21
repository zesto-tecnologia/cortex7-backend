"""
Service for processing and extracting text from documents.
"""

import io
import json
from typing import Dict, Any, Optional
from pathlib import Path


class DocumentProcessor:
    """Service for processing various document types."""

    SUPPORTED_EXTENSIONS = {
        '.txt', '.pdf', '.docx', '.doc', '.csv', '.json',
        '.md', '.html', '.xml', '.xlsx', '.xls'
    }

    async def extract_text(self, file_content: bytes, filename: str) -> str:
        """
        Extract text from various document formats.

        Args:
            file_content: File content as bytes
            filename: Original filename with extension

        Returns:
            Extracted text content
        """
        extension = Path(filename).suffix.lower()

        if extension == '.txt' or extension == '.md':
            return file_content.decode('utf-8', errors='ignore')

        elif extension == '.json':
            try:
                data = json.loads(file_content.decode('utf-8'))
                return json.dumps(data, indent=2)
            except:
                return file_content.decode('utf-8', errors='ignore')

        elif extension == '.pdf':
            return await self._extract_pdf_text(file_content)

        elif extension in ['.docx', '.doc']:
            return await self._extract_word_text(file_content)

        elif extension in ['.xlsx', '.xls']:
            return await self._extract_excel_text(file_content)

        elif extension == '.csv':
            return await self._extract_csv_text(file_content)

        elif extension in ['.html', '.xml']:
            return await self._extract_markup_text(file_content)

        else:
            # Try to decode as text for unknown formats
            try:
                return file_content.decode('utf-8', errors='ignore')
            except:
                return f"[Binary file: {filename}]"

    async def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF file."""
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except ImportError:
            return "[PDF processing requires PyPDF2 library]"
        except Exception as e:
            return f"[Error extracting PDF text: {str(e)}]"

    async def _extract_word_text(self, file_content: bytes) -> str:
        """Extract text from Word documents."""
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_content))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except ImportError:
            return "[Word processing requires python-docx library]"
        except Exception as e:
            return f"[Error extracting Word text: {str(e)}]"

    async def _extract_excel_text(self, file_content: bytes) -> str:
        """Extract text from Excel files."""
        try:
            import pandas as pd
            df = pd.read_excel(io.BytesIO(file_content))
            return df.to_string()
        except ImportError:
            return "[Excel processing requires pandas and openpyxl libraries]"
        except Exception as e:
            return f"[Error extracting Excel text: {str(e)}]"

    async def _extract_csv_text(self, file_content: bytes) -> str:
        """Extract text from CSV files."""
        try:
            import pandas as pd
            df = pd.read_csv(io.BytesIO(file_content))
            return df.to_string()
        except ImportError:
            try:
                return file_content.decode('utf-8', errors='ignore')
            except:
                return "[Error reading CSV file]"
        except Exception as e:
            return f"[Error extracting CSV text: {str(e)}]"

    async def _extract_markup_text(self, file_content: bytes) -> str:
        """Extract text from HTML/XML files."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(file_content, 'html.parser')
            return soup.get_text()
        except ImportError:
            # Fallback to raw text
            return file_content.decode('utf-8', errors='ignore')
        except Exception as e:
            return f"[Error extracting markup text: {str(e)}]"

    async def extract_metadata(
        self,
        file_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Extract metadata from documents.

        Args:
            file_content: File content as bytes
            filename: Original filename

        Returns:
            Dictionary with metadata
        """
        metadata = {
            "filename": filename,
            "extension": Path(filename).suffix.lower(),
            "size_bytes": len(file_content)
        }

        # Add format-specific metadata extraction here
        extension = metadata["extension"]

        if extension == '.pdf':
            metadata.update(await self._extract_pdf_metadata(file_content))

        return metadata

    async def _extract_pdf_metadata(self, file_content: bytes) -> Dict[str, Any]:
        """Extract metadata from PDF files."""
        try:
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            info = pdf_reader.metadata

            return {
                "pages": len(pdf_reader.pages),
                "title": info.title if info and info.title else None,
                "author": info.author if info and info.author else None,
                "subject": info.subject if info and info.subject else None,
                "creator": info.creator if info and info.creator else None,
            }
        except:
            return {}