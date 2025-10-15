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
            # Build strict JSON Schema for structured outputs
            schema_block = {
                "type": "json_schema",
                "json_schema": self._build_extraction_schema(),
            }

            # Call GPT-5 with strict schema enforcement
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
                reasoning_effort="high",
                response_format=schema_block,
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
            "Read the provided Monitoring Plan (EMP) and Emissions Report (ER). Extract ONLY what is explicitly supported by these documents. Do NOT infer or invent. If a field is unknown or absent, set the value to null and add the key name to missing_fields.\n\n"
            "Return a SINGLE JSON object of flat key:value pairs (values are string|null, or short arrays where necessary), plus standard metadata. No explanations.\n\n"
            "MUST-HAVE KEYS (values MUST be string|null unless noted):\n"
            "{\n"
            "  \"metadata\": { \"document_name\": string, \"mime_type\": string, \"extracted_at\": string, \"generator_version\": string },\n"
            "  \"operator_name\": string|null,\n"
            "  \"icao_designator\": string|null,\n"
            "  \"aoc_id\": string|null,\n"
            "  \"aoc_authority\": string|null,\n"
            "  \"state_of_operator\": string|null,\n"
            "  \"parent_subsidiary_status\": string|null,\n"
            "  \"contacts_accountable_manager_name\": string|null,\n"
            "  \"contacts_accountable_manager_title\": string|null,\n"
            "  \"contacts_accountable_manager_email\": string|null,\n"
            "  \"contacts_accountable_manager_phone\": string|null,\n"
            "  \"contacts_corsia_focal_name\": string|null,\n"
            "  \"contacts_corsia_focal_title\": string|null,\n"
            "  \"contacts_corsia_focal_email\": string|null,\n"
            "  \"contacts_corsia_focal_phone\": string|null,\n"
            "  \"reporting_year\": string|null,\n"
            "  \"coverage\": string|null,\n"
            "  \"aggregation_level\": string|null,\n"
            "  \"aircraft_types_and_counts\": string|null,\n"
            "  \"fuel_types\": string|null,\n"
            "  \"fuel_suppliers\": string|null,\n"
            "  \"monitoring_methods_method_a\": string|null,\n"
            "  \"monitoring_methods_method_b\": string|null,\n"
            "  \"monitoring_methods_block_off_on\": string|null,\n"
            "  \"monitoring_methods_fuel_uplift\": string|null,\n"
            "  \"monitoring_methods_fuel_allocation_block_hour\": string|null,\n"
            "  \"monitoring_methods_periods\": string|null,\n"
            "  \"monitoring_methods_primary_data_sources\": string|null,\n"
            "  \"fuel_density_values_and_sources\": string|null,\n"
            "  \"cert_usage\": string|null,\n"
            "  \"cert_inputs\": string|null,\n"
            "  \"emission_factors\": string|null,\n"
            "  \"data_flow\": string|null,\n"
            "  \"controls\": string|null,\n"
            "  \"error_handling\": string|null,\n"
            "  \"change_control\": string|null,\n"
            "  \"responsible_teams_roles\": string|null,\n"
            "  \"records_storage_locations\": string|null,\n"
            "  \"retention_time\": string|null,\n"
            "  \"backup_archiving\": string|null,\n"
            "  \"reporting_state_pairs\": string|null,\n"
            "  \"major_aerodrome_pairs\": string|null,\n"
            "  \"exclusions_special_cases\": string|null,\n"
            "  \"data_gaps_occurred\": string|null,\n"
            "  \"data_gaps_percent_affected\": string|null,\n"
            "  \"data_gaps_replacement_methods\": string|null,\n"
            "  \"data_gaps_justification\": string|null,\n"
            "  \"emission_reductions_saf\": string|null,\n"
            "  \"saf_book_and_claim\": string|null,\n"
            "  \"documentation_required\": string|null,\n"
            "  \"key_missing_items\": [string],\n"
            "  \"provenance_index\": [{ \"id\": string, \"location\": string, \"excerpt\": string }],\n"
            "  \"missing_fields\": [string]\n"
            "}\n\n"
            "ADDITIONAL RULES:\n"
            "- Use SI units only (t, kg, L).\n"
            "- Values must match the docs verbatim where possible; summarize numbers only if clearly stated. When not present, use null and record the key in missing_fields.\n"
            "- For \"monitoring_methods_periods\", include only years within 2021–2035 if specified.\n"
            "- Keep strings concise; no paragraphs; no tables.\n"
            "- Important: Return ONLY the JSON object described above."
        )

    def _build_extraction_schema(self) -> Dict[str, Any]:
        """Strict JSON Schema for structured outputs (string|null flat keys)."""
        return {
            "name": "corsia_monitoring_plan",
            "schema": {
                "type": "object",
                "properties": {
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "document_name": {"type": "string"},
                            "mime_type": {"type": "string"},
                            "extracted_at": {"type": "string"},
                            "generator_version": {"type": "string"}
                        },
                        "required": ["extracted_at", "generator_version"],
                        "additionalProperties": True
                    },
                    "operator_name": {"type": ["string", "null"]},
                    "icao_designator": {"type": ["string", "null"]},
                    "aoc_id": {"type": ["string", "null"]},
                    "aoc_authority": {"type": ["string", "null"]},
                    "state_of_operator": {"type": ["string", "null"]},
                    "parent_subsidiary_status": {"type": ["string", "null"]},
                    "contacts_accountable_manager_name": {"type": ["string", "null"]},
                    "contacts_accountable_manager_title": {"type": ["string", "null"]},
                    "contacts_accountable_manager_email": {"type": ["string", "null"]},
                    "contacts_accountable_manager_phone": {"type": ["string", "null"]},
                    "contacts_corsia_focal_name": {"type": ["string", "null"]},
                    "contacts_corsia_focal_title": {"type": ["string", "null"]},
                    "contacts_corsia_focal_email": {"type": ["string", "null"]},
                    "contacts_corsia_focal_phone": {"type": ["string", "null"]},
                    "reporting_year": {"type": ["string", "null"]},
                    "coverage": {"type": ["string", "null"]},
                    "aggregation_level": {"type": ["string", "null"]},
                    "aircraft_types_and_counts": {"type": ["string", "null"]},
                    "fuel_types": {"type": ["string", "null"]},
                    "fuel_suppliers": {"type": ["string", "null"]},
                    "monitoring_methods_method_a": {"type": ["string", "null"]},
                    "monitoring_methods_method_b": {"type": ["string", "null"]},
                    "monitoring_methods_block_off_on": {"type": ["string", "null"]},
                    "monitoring_methods_fuel_uplift": {"type": ["string", "null"]},
                    "monitoring_methods_fuel_allocation_block_hour": {"type": ["string", "null"]},
                    "monitoring_methods_periods": {"type": ["string", "null"]},
                    "monitoring_methods_primary_data_sources": {"type": ["string", "null"]},
                    "fuel_density_values_and_sources": {"type": ["string", "null"]},
                    "cert_usage": {"type": ["string", "null"]},
                    "cert_inputs": {"type": ["string", "null"]},
                    "emission_factors": {"type": ["string", "null"]},
                    "data_flow": {"type": ["string", "null"]},
                    "controls": {"type": ["string", "null"]},
                    "error_handling": {"type": ["string", "null"]},
                    "change_control": {"type": ["string", "null"]},
                    "responsible_teams_roles": {"type": ["string", "null"]},
                    "records_storage_locations": {"type": ["string", "null"]},
                    "retention_time": {"type": ["string", "null"]},
                    "backup_archiving": {"type": ["string", "null"]},
                    "reporting_state_pairs": {"type": ["string", "null"]},
                    "major_aerodrome_pairs": {"type": ["string", "null"]},
                    "exclusions_special_cases": {"type": ["string", "null"]},
                    "data_gaps_occurred": {"type": ["string", "null"]},
                    "data_gaps_percent_affected": {"type": ["string", "null"]},
                    "data_gaps_replacement_methods": {"type": ["string", "null"]},
                    "data_gaps_justification": {"type": ["string", "null"]},
                    "emission_reductions_saf": {"type": ["string", "null"]},
                    "saf_book_and_claim": {"type": ["string", "null"]},
                    "documentation_required": {"type": ["string", "null"]},
                    "key_missing_items": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "provenance_index": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "location": {"type": "string"},
                                "excerpt": {"type": "string"}
                            },
                            "required": ["id", "location"],
                            "additionalProperties": False
                        }
                    },
                    "missing_fields": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["metadata", "missing_fields"],
                "additionalProperties": True
            },
            "strict": True
        }

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
