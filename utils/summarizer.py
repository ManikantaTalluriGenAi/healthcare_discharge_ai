"""
Discharge Summary Generator using LangChain and HuggingFace Models
"""

import os
import logging
from typing import Dict, Any, Optional
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from langchain_huggingface import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
import torch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DischargeSummarizer:
    """
    A class to generate discharge summaries using HuggingFace models.
    """
    
    def __init__(self, model_name: str = "google/flan-t5-small"):
        """
        Initialize the summarizer with a specific model.
        
        Args:
            model_name (str): The HuggingFace model name to use
        """
        self.model_name = model_name
        self.pipeline = None
        self.chain = None
        self._load_model()
    
    def _load_model(self):
        """Load the model and create the pipeline."""
        try:
            logger.info(f"Loading model: {self.model_name}")
            
            # Force CPU usage to avoid MPS memory issues on Mac
            device = -1  # Always use CPU for now
            logger.info("Forcing CPU usage to avoid MPS memory issues")
            
            logger.info(f"Device set to use {device}")
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Determine model loading parameters based on device
            if device != -1:
                # Use accelerate for GPU/MPS
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16,
                    device_map="auto"
                )
                # Don't specify device in pipeline when using accelerate
                pipeline_device = None
            else:
                # Use CPU
                model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32,
                    device_map=None
                )
                pipeline_device = device
            
            # Create pipeline
            self.pipeline = pipeline(
                "text2text-generation",
                model=model,
                tokenizer=tokenizer,
                max_length=512,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                device=pipeline_device
            )
            
            # Create LangChain pipeline
            llm = HuggingFacePipeline(pipeline=self.pipeline)
            
            # Create prompt template
            prompt_template = PromptTemplate(
                input_variables=["transcription", "patient_info"],
                template="""
                Based on the following medical transcription and patient information, 
                generate a comprehensive discharge summary:
                
                Transcription: {transcription}
                Patient Information: {patient_info}
                
                Please provide a detailed discharge summary including:
                1. Primary diagnosis and secondary conditions
                2. Procedures performed
                3. Medications prescribed
                4. Discharge instructions
                5. Follow-up recommendations
                6. Any special instructions or precautions
                
                Discharge Summary:
                """
            )
            
            # Create chain using the new syntax
            self.chain = prompt_template | llm
            
            logger.info("Model loaded successfully!")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def generate_summary(self, transcription: str, patient_info: Dict[str, Any]) -> str:
        """
        Generate a discharge summary from transcription and patient info.
        
        Args:
            transcription (str): The transcribed medical notes
            patient_info (dict): Patient demographic and medical information
            
        Returns:
            str: Generated discharge summary
        """
        try:
            # Format patient info
            patient_info_str = f"""
            Name: {patient_info.get('name', 'N/A')}
            Age: {patient_info.get('age', 'N/A')}
            Gender: {patient_info.get('gender', 'N/A')}
            Medical History: {patient_info.get('medical_history', 'N/A')}
            Current Medications: {patient_info.get('current_medications', 'N/A')}
            Allergies: {patient_info.get('allergies', 'None')}
            """
            
            # Create input for the chain
            chain_input = {
                "transcription": transcription,
                "patient_info": patient_info_str
            }
            
            # Generate summary using the new invoke method
            result = self.chain.invoke(chain_input)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    def generate_structured_summary(self, transcription: str, patient_info: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a structured discharge summary with separate sections.
        
        Args:
            transcription (str): The transcribed medical notes
            patient_info (dict): Patient demographic and medical information
            
        Returns:
            dict: Structured summary with different sections
        """
        try:
            # Generate main summary
            main_summary = self.generate_summary(transcription, patient_info)
            
            # Create structured sections
            structured_summary = {
                "main_summary": main_summary,
                "diagnosis": self._extract_section(main_summary, "diagnosis"),
                "medications": self._extract_section(main_summary, "medications"),
                "instructions": self._extract_section(main_summary, "instructions"),
                "follow_up": self._extract_section(main_summary, "follow-up")
            }
            
            return structured_summary
            
        except Exception as e:
            logger.error(f"Error generating structured summary: {e}")
            return {"error": str(e)}
    
    def generate_patient_friendly_summary(self, transcription: str, patient_info: Dict[str, Any]) -> str:
        """
        Generate a patient-friendly version of the discharge summary.
        
        Args:
            transcription (str): The transcribed medical notes
            patient_info (dict): Patient demographic and medical information
            
        Returns:
            str: Patient-friendly discharge summary
        """
        try:
            # Create a patient-friendly prompt
            patient_friendly_prompt = PromptTemplate(
                input_variables=["transcription", "patient_info"],
                template="""
                Based on the following medical transcription and patient information, 
                generate a patient-friendly discharge summary in simple, easy-to-understand language:
                
                Transcription: {transcription}
                Patient Information: {patient_info}
                
                Please provide a clear, simple discharge summary that includes:
                1. What happened during the hospital stay (in simple terms)
                2. What medications to take and why
                3. What to do at home
                4. When to follow up with the doctor
                5. Warning signs to watch for
                6. Any lifestyle changes needed
                
                Use simple language that a patient can easily understand.
                
                Patient-Friendly Discharge Summary:
                """
            )
            
            # Create chain for patient-friendly summary
            llm = HuggingFacePipeline(pipeline=self.pipeline)
            patient_chain = patient_friendly_prompt | llm
            
            # Format patient info
            patient_info_str = f"""
            Name: {patient_info.get('name', 'N/A')}
            Age: {patient_info.get('age', 'N/A')}
            Gender: {patient_info.get('gender', 'N/A')}
            Medical History: {patient_info.get('medical_history', 'N/A')}
            Current Medications: {patient_info.get('current_medications', 'N/A')}
            Allergies: {patient_info.get('allergies', 'None')}
            """
            
            # Generate patient-friendly summary
            chain_input = {
                "transcription": transcription,
                "patient_info": patient_info_str
            }
            
            result = patient_chain.invoke(chain_input)
            return result
            
        except Exception as e:
            logger.error(f"Error generating patient-friendly summary: {e}")
            return f"Error generating patient-friendly summary: {str(e)}"
    
    def _extract_section(self, summary: str, section_name: str) -> str:
        """
        Extract a specific section from the summary.
        
        Args:
            summary (str): The full summary text
            section_name (str): The section to extract
            
        Returns:
            str: The extracted section or a default message
        """
        # Simple extraction logic - can be improved with more sophisticated parsing
        lines = summary.split('\n')
        section_content = []
        in_section = False
        
        for line in lines:
            if section_name.lower() in line.lower():
                in_section = True
                section_content.append(line)
            elif in_section and line.strip() and not line.startswith(('1.', '2.', '3.', '4.', '5.', '6.')):
                section_content.append(line)
            elif in_section and line.strip() and line.startswith(('1.', '2.', '3.', '4.', '5.', '6.')):
                break
        
        return '\n'.join(section_content) if section_content else f"No {section_name} information available."


# Convenience function for quick summary generation
def generate_summary(prompt: str, patient_info: str = "", medical_notes: str = "") -> str:
    """
    Convenience function to generate a discharge summary.
    
    Args:
        prompt (str): Custom prompt or additional instructions
        patient_info (str): Patient demographic and basic information
        medical_notes (str): Medical notes, diagnoses, and treatment details
        
    Returns:
        str: Generated discharge summary
    """
    summarizer = DischargeSummarizer()
    return summarizer.generate_summary(prompt, patient_info)


if __name__ == "__main__":
    # Example usage
    summarizer = DischargeSummarizer()
    
    # Test with sample data
    sample_patient_info = {
        "name": "John Doe",
        "age": "45-year-old male",
        "gender": "male",
        "medical_history": "chest pain",
        "current_medications": "stent placement",
        "allergies": "None"
    }
    sample_medical_notes = """
    Patient presented with chest pain and shortness of breath. 
    EKG showed ST elevation. Cardiac catheterization revealed 90% blockage in LAD. 
    Successfully treated with stent placement. Patient stable for discharge.
    """
    
    summary = summarizer.generate_summary(
        sample_medical_notes,
        sample_patient_info
    )
    
    print("Generated Discharge Summary:")
    print(summary) 