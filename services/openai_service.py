"""
OpenAI Service
Handles OpenAI API interactions for monitoring plan extraction
"""

import os
import base64
from typing import Dict, Any, Optional
from openai import OpenAI
import json
import PyPDF2
import pandas as pd
from PIL import Image
import io


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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert aviation compliance analyst specializing in monitoring plans for emissions trading schemes (CORSIA, EU ETS, UK ETS, CH ETS, ReFuelEU)."
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nMonitoring Plan Document:\n{content}"
                    }
                ],
                temperature=0.1,
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
        """Extract text content from various file formats"""

        try:
            if file_extension == 'pdf':
                return self._extract_from_pdf(file_path)
            elif file_extension in ['xlsx', 'xls']:
                return self._extract_from_excel(file_path)
            elif file_extension == 'csv':
                return self._extract_from_csv(file_path)
            elif file_extension in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp']:
                return self._extract_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_extension}")

        except Exception as e:
            print(f"[OPENAI SERVICE ERROR] Content extraction failed: {str(e)}")
            raise

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text.append(page.extract_text())
        return "\n".join(text)

    def _extract_from_excel(self, file_path: str) -> str:
        """Extract text from Excel file"""
        df = pd.read_excel(file_path, sheet_name=None)  # Read all sheets
        text = []
        for sheet_name, sheet_df in df.items():
            text.append(f"Sheet: {sheet_name}\n")
            text.append(sheet_df.to_string())
        return "\n".join(text)

    def _extract_from_csv(self, file_path: str) -> str:
        """Extract text from CSV"""
        df = pd.read_csv(file_path)
        return df.to_string()

    def _extract_from_image(self, file_path: str) -> str:
        """Extract text from image using GPT-5 Vision"""
        # Read and encode image
        with open(file_path, 'rb') as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')

        # Determine image format
        file_ext = file_path.split('.')[-1].lower()
        mime_type = f"image/{file_ext if file_ext != 'jpg' else 'jpeg'}"

        # Use GPT-5 with vision to extract text
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
            ],
            temperature=0.1
        )

        return response.choices[0].message.content

    def _build_extraction_prompt(self) -> str:
        """Build the extraction prompt for GPT-5"""
        return """
Please extract and structure the following information from the monitoring plan document:

1. **Monitoring Plan Processes (per scheme)**:
   - List all monitoring processes mentioned for each scheme (CORSIA, EU ETS, UK ETS, CH ETS, ReFuelEU)
   - Include details about data collection, verification, and reporting procedures

2. **Basic Information**:
   - Airline/operator name
   - Registration details
   - Contact information
   - Version and date of monitoring plan

3. **Method**:
   - Fuel monitoring methodology
   - Calculation methods used
   - Standards and references

4. **How Fuel Data is Collected from Aircraft**:
   - Automatic collection systems (specify system names/types)
   - Manual collection using paper logs
   - Hybrid approaches

5. **Primary Data Source**:
   - Is the primary source automatic? (yes/no)
   - System/technology used
   - Data frequency and accuracy

6. **Secondary Source**:
   - Are paper logs used as secondary source? (yes/no)
   - Backup procedures
   - Validation methods

7. **Geographical Presence**:
   - EU-based operations (yes/no)
   - Non-EU based operations (yes/no)
   - Primary operational region
   - Based on this, determine scheme priority:
     * If EU-based: EU ETS should be HIGH priority, CORSIA standard priority
     * If Non-EU based: CORSIA should be HIGH priority, EU ETS lower priority

Return the information as a structured JSON object with these exact keys:
{
    "monitoring_plan_processes": {
        "CORSIA": "...",
        "EU_ETS": "...",
        "UK_ETS": "...",
        "CH_ETS": "...",
        "ReFuelEU": "..."
    },
    "basic_info": {
        "airline_name": "...",
        "registration_details": "...",
        "contact_info": "...",
        "version": "...",
        "date": "..."
    },
    "method": {
        "fuel_monitoring_methodology": "...",
        "calculation_methods": "...",
        "standards_references": "..."
    },
    "fuel_data_collection": {
        "collection_method": "automatic|manual|hybrid",
        "details": "..."
    },
    "primary_data_source": {
        "is_automatic": true|false,
        "system_used": "...",
        "frequency": "...",
        "accuracy": "..."
    },
    "secondary_source": {
        "uses_paper_logs": true|false,
        "backup_procedures": "...",
        "validation_methods": "..."
    },
    "geographical_presence": {
        "is_eu_based": true|false,
        "is_non_eu_based": true|false,
        "primary_region": "...",
        "scheme_priority": {
            "CORSIA": "high|standard|low",
            "EU_ETS": "high|standard|low",
            "UK_ETS": "high|standard|low",
            "CH_ETS": "high|standard|low",
            "ReFuelEU": "high|standard|low"
        }
    }
}

If any information is not found in the document, use null or "Not specified" for that field.
"""

    def _process_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate extracted data"""

        # Ensure all required fields are present
        required_fields = [
            'monitoring_plan_processes',
            'basic_info',
            'method',
            'fuel_data_collection',
            'primary_data_source',
            'secondary_source',
            'geographical_presence'
        ]

        for field in required_fields:
            if field not in data:
                data[field] = {}

        # Add extraction metadata
        data['extraction_metadata'] = {
            'model': self.model,
            'reasoning_effort': 'high',
            'extracted_at': pd.Timestamp.now().isoformat()
        }

        return data
