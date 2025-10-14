"""
OpenAI Service
Handles OpenAI API interactions for monitoring plan extraction

Enhancements:
- Flexible, hallucination-safe prompt tailored to CORSIA EMP
- Multi-format ingestion (.xlsx/.xls, .csv, .pdf, .docx, images)
- Sheet/page-aware content formatting to support simple provenance
"""

import os
import base64
from typing import Dict, Any, Optional, List
from openai import OpenAI
import json
import PyPDF2
import pandas as pd
from PIL import Image
import io
import pdfplumber
from docx import Document


class OpenAIService:
    """Service for OpenAI API operations"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-5"  # Using GPT-5 as specified

    def extract_monitoring_plan_info(self, file_path: str, file_extension: str) -> Dict[str, Any]:
        """
        Extract monitoring plan information from uploaded file using GPT-5

        Args:
            file_path: Path to the uploaded file
            file_extension: File extension (pdf, xlsx, csv, png, etc.)

        Returns:
            Extracted monitoring plan information
        """
        print(f"[OPENAI SERVICE] Extracting info from {file_path} ({file_extension})")

        # Extract text/content based on file type
        content = self._extract_content_from_file(file_path, file_extension)

        # Prepare the extraction prompt
        prompt = self._build_extraction_prompt()

        try:
            # Call GPT-5 with high reasoning effort
            # Note: GPT-5 only supports default temperature (1), so we don't set it
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert in ICAO CORSIA Emissions Monitoring Plans (Annex 16, Vol IV). "
                            "Extract only what is explicitly present. Do not infer or fabricate. If a field is unknown, set it to null and list it in missing_fields. "
                            "Provide concise evidence excerpts and simple provenance identifiers where possible."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nSOURCE CONTENT (with markers for simple provenance):\n{content}"
                    }
                ],
                reasoning_effort="high",  # High reasoning as requested
                response_format={"type": "json_object"}
            )

            # Parse the response
            result = json.loads(response.choices[0].message.content)
            print(f"[OPENAI SERVICE] Extraction successful")

            return self._process_extracted_data(result)

        except Exception as e:
            print(f"[OPENAI SERVICE ERROR] Extraction failed: {str(e)}")
            raise Exception(f"Failed to extract monitoring plan information: {str(e)}")

    def _extract_content_from_file(self, file_path: str, file_extension: str) -> str:
        """Extract text content from various file formats and add lightweight provenance markers."""

        try:
            ext = (file_extension or '').lower()
            if ext == 'pdf':
                return self._extract_from_pdf(file_path)
            if ext in ['xlsx', 'xls']:
                return self._extract_from_excel(file_path)
            if ext == 'csv':
                return self._extract_from_csv(file_path)
            if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp']:
                return self._extract_from_image(file_path)
            if ext in ['docx']:
                return self._extract_from_docx(file_path)
            if ext in ['txt', 'text']:
                return self._extract_from_txt(file_path)
                raise ValueError(f"Unsupported file format: {file_extension}")

        except Exception as e:
            print(f"[OPENAI SERVICE ERROR] Content extraction failed: {str(e)}")
            raise

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF. Prefer pdfplumber (layout-aware), fallback to PyPDF2."""
        chunks: List[str] = []
        try:
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    # Add a page marker for simple provenance
                    chunks.append(f"\n=== PAGE {i} START ===\n{page_text}\n=== PAGE {i} END ===")
        except Exception:
            # Fallback to PyPDF2
        with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for i, page in enumerate(reader.pages, start=1):
                    page_text = page.extract_text() or ""
                    chunks.append(f"\n=== PAGE {i} START ===\n{page_text}\n=== PAGE {i} END ===")
        return "\n".join(chunks).strip()

    def _extract_from_excel(self, file_path: str) -> str:
        """Extract content from all sheets, preserving sheet names for provenance."""
        sheets = pd.read_excel(file_path, sheet_name=None)  # All sheets
        parts: List[str] = []
        for sheet_name, sheet_df in sheets.items():
            try:
                sheet_df = sheet_df.copy()
                sheet_df.columns = [str(c).strip() for c in sheet_df.columns]
            except Exception:
                pass
            parts.append(f"\n=== SHEET {sheet_name} START ===")
            parts.append(sheet_df.to_string(index=False))
            parts.append(f"=== SHEET {sheet_name} END ===")
        return "\n".join(parts).strip()

    def _extract_from_csv(self, file_path: str) -> str:
        """Extract text from CSV with robust encoding and include a single-sheet marker."""
        try:
            df = pd.read_csv(file_path, encoding='utf-8', encoding_errors='replace')
        except Exception:
        df = pd.read_csv(file_path)
        try:
            df.columns = df.columns.str.strip()
        except Exception:
            pass
        return f"=== SHEET CSV START ===\n{df.to_string(index=False)}\n=== SHEET CSV END ==="

    def _extract_from_image(self, file_path: str) -> str:
        """Extract text from image using GPT-5 Vision"""
        # Read and encode image
        with open(file_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        # Determine image format
        file_ext = file_path.split('.')[-1].lower()
        mime_type = f"image/{file_ext if file_ext != 'jpg' else 'jpeg'}"

        # Use GPT-5 with vision to extract text
        # Note: GPT-5 only supports default temperature (1)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text content from this image. Preserve the structure and formatting as much as possible."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
        )

        return response.choices[0].message.content

    def _extract_from_docx(self, file_path: str) -> str:
        """Extract paragraphs and tables from DOCX with simple section markers."""
        doc = Document(file_path)
        parts: List[str] = []
        parts.append("=== DOCX PARAGRAPHS START ===")
        for para in doc.paragraphs:
            text = (para.text or "").strip()
            if text:
                parts.append(text)
        parts.append("=== DOCX PARAGRAPHS END ===")

        # Tables
        if getattr(doc, 'tables', None):
            for t_idx, table in enumerate(doc.tables, start=1):
                parts.append(f"=== DOCX TABLE {t_idx} START ===")
                for row in table.rows:
                    cells = [cell.text.replace('\n', ' ').strip() for cell in row.cells]
                    parts.append(" | ".join(cells))
                parts.append(f"=== DOCX TABLE {t_idx} END ===")
        return "\n".join(parts).strip()

    def _extract_from_txt(self, file_path: str) -> str:
        """Extract plain text with a top-level marker."""
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            data = f.read()
        return f"=== TEXT START ===\n{data}\n=== TEXT END ==="

    def _build_extraction_prompt(self) -> str:
        """Build a flexible, hallucination-safe extraction prompt for GPT-5."""
        return (
            "Extract all relevant information from the CORSIA Emissions Monitoring Plan (EMP). "
            "Return a SINGLE JSON object. Do not include explanations. Rules: "
            "1) Only extract what is explicitly present in the source. 2) If a field is unknown, set null and add a string to missing_fields. 3) Provide concise evidence excerpts and simple provenance identifiers (e.g., 'PAGE 2', 'SHEET Fleet'). 4) Normalize dates to YYYY-MM-DD when explicit; also include original if different. 5) Preserve table content verbatim as arrays of objects when clearly structured.\n\n"
            "JSON shape (keys optional; include only if content exists or explicitly null):\n"
            "{\n"
            "  \"metadata\": { \"document_name\": string, \"mime_type\": string, \"extracted_at\": string, \"generator_version\": string },\n"
            "  \"operator\": { \"name\": {\"value\": string|null, \"__meta\": {\"provenance\": string, \"confidence\": number}}, \"address\": {\"lines\": [string], \"city\": string|null, \"region\": string|null, \"postal_code\": string|null, \"country\": string|null}, \"legal_representative\": {\"title\": string|null, \"first_name\": string|null, \"last_name\": string|null, \"email\": string|null}, \"contacts\": [object], \"aoc\": {\"code\": string|null, \"issued_at\": string|null, \"expires_at\": string|null, \"authority\": {\"name\": string|null, \"address\": object}, \"scope\": [string]} , \"group_structure\": {\"parent_subsidiary_single_entity\": boolean|null, \"subsidiaries\": [{\"name\": string, \"aircraft_identification_method\": string}] } },\n"
            "  \"flight_attribution\": { \"icao_designator\": string|null, \"registration_marks\": [string], \"responsibility_under_corsia\": string|null, \"additional_info\": string|null },\n"
            "  \"activities\": { \"description\": string|null, \"main_state_pairs\": [string], \"leasing_arrangements\": [string], \"operation_types\": [string], \"geographic_scope\": [string] },\n"
            "  \"fleet\": { \"aircraft_list\": [{\"registration_mark\": string, \"type\": string|null, \"notes\": string|null}] },\n"
            "  \"methods\": { \"fuel_use_method_a\": object, \"method_b\": object, \"block_off_on\": object, \"fuel_uplift\": object, \"allocation_block_hour\": object, \"cert_usage\": {\"used\": boolean|null, \"details\": string|null} },\n"
            "  \"data_management\": { \"data_flow\": string|null, \"controls\": string|null, \"risk_analysis\": string|null, \"data_gaps\": string|null },\n"
            "  \"tables\": { string: [object] },\n"
            "  \"provenance_index\": [{ \"id\": string, \"location\": string, \"excerpt\": string }],\n"
            "  \"missing_fields\": [string]\n"
            "}\n"
        )

    def _process_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Attach extraction metadata and ensure minimal structure without enforcing rigid keys."""
        if not isinstance(data, dict):
            data = {"raw": data}

        meta = data.get('metadata', {}) if isinstance(data.get('metadata'), dict) else {}
        meta.setdefault('extracted_at', pd.Timestamp.now().isoformat())
        meta.setdefault('generator_version', 'v1-flex')
        data['metadata'] = meta

        data['extraction_metadata'] = {
            'model': self.model,
            'reasoning_effort': 'high'
        }

        # Ensure missing_fields exists
        if 'missing_fields' not in data or not isinstance(data.get('missing_fields'), list):
            data['missing_fields'] = []

        return data
