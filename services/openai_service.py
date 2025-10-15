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
            "Return a SINGLE JSON object. Do not include explanations. Follow ALL rules strictly.\n"
            "Rules: \n"
            "- Extract ONLY what is explicitly supported by the source content (EMP/ER).\n"
            "- Do NOT infer or invent.\n"
            "- If a field is absent, use the literal string 'MISSING'.\n"
            "- SI units only (t, kg, L).\n"
            "- Keep values verbatim where possible; summarize numbers only if clearly stated.\n"
            "- Keep overall length compact and targeted.\n\n"
            "OUTPUT FORMAT (MUST be a valid JSON object):\n"
            "{\n"
            "  \"metadata\": {\n"
            "    \"document_name\": string,\n"
            "    \"mime_type\": string,\n"
            "    \"extracted_at\": string,\n"
            "    \"generator_version\": string\n"
            "  },\n"
            "  \"bullets\": [\n"
            "    // Array of 18–28 compact bullet strings in EXACT format '- **Label:** value'\n"
            "    // No tables; one line per bullet; keep order below\n"
            "  ],\n"
            "  \"missing_fields\": [\n"
            "    // Labels that are 'MISSING'\n"
            "  ],\n"
            "  \"provenance_index\": [\n"
            "    { \"id\": string, \"location\": string, \"excerpt\": string }\n"
            "  ]\n"
            "}\n\n"
            "CONTENT AND ORDER (emit bullets in this order; use 'MISSING' when absent):\n"
            "1) Operator & Regulatory: Operator name; ICAO designator; AOC ID & authority; State of the operator; parent–subsidiary status.\n"
            "2) Contacts: Name(s), title(s), email(s), phone(s) for accountable manager and CORSIA focal(s).\n"
            "3) Scope & Period: Reporting year; coverage (international only); aggregation level (state-pair / aerodrome-pair).\n"
            "4) Fleet & Fuel: Aircraft types and counts used for reporting; fuel types; fuel suppliers if listed.\n"
            "5) Monitoring Methods (by sub-fleet if applicable): Method A, Method B, Block-off/Block-on, Fuel Uplift, Fuel Allocation (Block Hour); periods of applicability (only 2021–2035); primary data sources (e.g., journey logs/NAVONE, fuel receipts, QAR/ACMS).\n"
            "6) Calculation Inputs: Fuel density values and sources; CERT usage (yes/no); CERT inputs (e.g., GCD vs actual distances); emission factors if stated.\n"
            "7) Data Flow & Controls (QA/QC): How data is captured, validated, reconciled, and approved; key controls; error handling; change control; responsible teams/roles.\n"
            "8) Records & Retention: Where records are stored (systems/locations), retention time, backup/archiving.\n"
            "9) Reporting Setup: List State pairs operated (high-level); note major Aerodrome pairs if included; any exclusions or special cases.\n"
            "10) Data Gaps: Whether gaps occurred; % of data affected; replacement method(s) (e.g., QAR, CERT); justification.\n"
            "11) Emission Reductions / SAF: Any SAF claims, book-and-claim, or emission reductions claimed; documentation required.\n"
            "12) Key Missing Items: Short list of important fields not present in the docs.\n\n"
            "FORMATTING OF 'bullets':\n"
            "- Emit 18–28 bullets total (≈250–350 words).\n"
            "- EXACT string format per bullet: '- **Label:** value' (keep the dashes and bold label).\n"
            "- Keep each bullet short; no prose; no sub-bullets; no tables.\n"
            "- Values must be from the documents; if not found, write 'MISSING'.\n\n"
            "PROVENANCE:\n"
            "- For any non-obvious bullet, add an entry in provenance_index with a simple identifier (e.g., PAGE 3 or SHEET Fleet, ROW 12) and a concise excerpt.\n"
            "- Keep excerpts short.\n\n"
            "Important: Return ONLY the JSON object described above."
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
