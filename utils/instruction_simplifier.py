"""
Medical Instruction Simplifier using LangChain and Open-Source LLMs
"""

import os
from typing import Optional, List, Dict, Any
from langchain.llms import HuggingFacePipeline
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from dotenv import load_dotenv
import re
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicalInstructionSimplifier:
    """
    A class to simplify complex medical instructions into patient-friendly language.
    """
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        """
        Initialize the simplifier with a specified model.
        
        Args:
            model_name (str): HuggingFace model name for text generation
        """
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.chain = None
        self.text_splitter = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the HuggingFace model and LangChain pipeline."""
        try:
            logger.info(f"Loading model: {self.model_name}")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Create HuggingFace pipeline
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_length=512,
                do_sample=True,
                temperature=0.7,
                top_p=0.95,
                repetition_penalty=1.15,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Create LangChain pipeline
            llm = HuggingFacePipeline(pipeline=self.pipeline)
            
            # Define prompt template for instruction simplification
            prompt_template = PromptTemplate(
                input_variables=["medical_instruction", "target_reading_level", "additional_context"],
                template="""
                Simplify the following medical instruction to make it easy for patients to understand.
                
                Medical Instruction:
                {medical_instruction}
                
                Target Reading Level: {target_reading_level}
                Additional Context: {additional_context}
                
                Please rewrite this instruction in simple, clear language that a patient can easily follow.
                Use everyday words instead of medical jargon.
                Break down complex concepts into simple steps.
                Include practical examples when helpful.
                
                Simplified Instruction:
                """
            )
            
            # Create LangChain chain
            self.chain = LLMChain(llm=llm, prompt=prompt_template)
            
            # Initialize text splitter for long instructions
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", ". ", "! ", "? ", " "]
            )
            
            logger.info("Model loaded successfully!")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def simplify_instruction(self, 
                           medical_instruction: str,
                           target_reading_level: str = "8th grade",
                           additional_context: str = "") -> str:
        """
        Simplify a medical instruction into patient-friendly language.
        
        Args:
            medical_instruction (str): Complex medical instruction to simplify
            target_reading_level (str): Target reading level (e.g., "5th grade", "8th grade")
            additional_context (str): Additional context about the patient or situation
            
        Returns:
            str: Simplified instruction
        """
        try:
            if not self.chain:
                raise ValueError("Model not initialized. Please check model loading.")
            
            # Clean and prepare the instruction
            cleaned_instruction = self._clean_instruction(medical_instruction)
            
            # Split long instructions if necessary
            if len(cleaned_instruction) > 1000:
                return self._simplify_long_instruction(cleaned_instruction, target_reading_level, additional_context)
            
            # Prepare input for the chain
            chain_input = {
                "medical_instruction": cleaned_instruction,
                "target_reading_level": target_reading_level,
                "additional_context": additional_context or "General patient"
            }
            
            # Generate simplified instruction
            result = self.chain.run(chain_input)
            
            # Post-process the result
            simplified = self._post_process_simplified_text(result)
            
            return simplified.strip()
            
        except Exception as e:
            logger.error(f"Error simplifying instruction: {e}")
            return f"Error simplifying instruction: {str(e)}"
    
    def simplify_medication_instructions(self, 
                                       medication_name: str,
                                       dosage: str,
                                       frequency: str,
                                       special_instructions: str = "") -> str:
        """
        Simplify medication instructions specifically.
        
        Args:
            medication_name (str): Name of the medication
            dosage (str): Dosage information
            frequency (str): How often to take
            special_instructions (str): Any special instructions
            
        Returns:
            str: Simplified medication instructions
        """
        instruction = f"""
        Medication: {medication_name}
        Dosage: {dosage}
        Frequency: {frequency}
        Special Instructions: {special_instructions}
        """
        
        return self.simplify_instruction(
            instruction,
            target_reading_level="6th grade",
            additional_context="Medication instructions for patient"
        )
    
    def simplify_discharge_instructions(self, 
                                      instructions: str,
                                      patient_age: Optional[int] = None,
                                      patient_education: str = "general") -> str:
        """
        Simplify discharge instructions.
        
        Args:
            instructions (str): Discharge instructions
            patient_age (int, optional): Patient's age
            patient_education (str): Patient's education level
            
        Returns:
            str: Simplified discharge instructions
        """
        # Determine reading level based on patient characteristics
        if patient_age and patient_age > 65:
            reading_level = "6th grade"
        elif patient_education in ["elementary", "middle school"]:
            reading_level = "5th grade"
        else:
            reading_level = "8th grade"
        
        context = f"Discharge instructions for {patient_age}-year-old patient with {patient_education} education"
        
        return self.simplify_instruction(instructions, reading_level, context)
    
    def simplify_medical_terms(self, text: str) -> str:
        """
        Replace complex medical terms with simple explanations.
        
        Args:
            text (str): Text containing medical terms
            
        Returns:
            str: Text with simplified medical terms
        """
        # Common medical term replacements
        medical_replacements = {
            r'\bhypertension\b': 'high blood pressure',
            r'\bdiabetes mellitus\b': 'diabetes',
            r'\bmyocardial infarction\b': 'heart attack',
            r'\bcerebrovascular accident\b': 'stroke',
            r'\bpharmacotherapy\b': 'medication treatment',
            r'\btherapeutic\b': 'healing',
            r'\bprophylactic\b': 'preventive',
            r'\bcontraindicated\b': 'not recommended',
            r'\badverse effects\b': 'side effects',
            r'\badminister\b': 'give',
            r'\boral\b': 'by mouth',
            r'\bintravenous\b': 'through a vein',
            r'\bsubcutaneous\b': 'under the skin',
            r'\bintramuscular\b': 'into the muscle',
            r'\bdiagnosis\b': 'what the doctor found',
            r'\bprognosis\b': 'what to expect',
            r'\bsymptom\b': 'sign of illness',
            r'\bchronic\b': 'long-term',
            r'\bacute\b': 'sudden or short-term',
            r'\bmalignant\b': 'cancerous',
            r'\bbenign\b': 'non-cancerous',
            r'\bpathology\b': 'disease',
            r'\betiology\b': 'cause',
            r'\bepidemiology\b': 'how common it is',
            r'\bpharmacology\b': 'how medicines work',
            r'\bimmunology\b': 'how the body fights disease',
            r'\bcardiology\b': 'heart health',
            r'\bneurology\b': 'brain and nerve health',
            r'\boncology\b': 'cancer treatment',
            r'\bpediatrics\b': 'children\'s health',
            r'\bgeriatrics\b': 'elderly health'
        }
        
        simplified_text = text
        
        for medical_term, simple_explanation in medical_replacements.items():
            simplified_text = re.sub(medical_term, simple_explanation, simplified_text, flags=re.IGNORECASE)
        
        return simplified_text
    
    def _clean_instruction(self, instruction: str) -> str:
        """
        Clean and prepare medical instruction for processing.
        
        Args:
            instruction (str): Raw medical instruction
            
        Returns:
            str: Cleaned instruction
        """
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', instruction.strip())
        
        # Remove common medical abbreviations that might confuse the model
        abbreviations_to_remove = ['PRN', 'BID', 'TID', 'QID', 'QD', 'QOD']
        for abbr in abbreviations_to_remove:
            cleaned = cleaned.replace(abbr, '')
        
        return cleaned
    
    def _simplify_long_instruction(self, 
                                 instruction: str,
                                 target_reading_level: str,
                                 additional_context: str) -> str:
        """
        Handle simplification of long instructions by splitting them.
        
        Args:
            instruction (str): Long medical instruction
            target_reading_level (str): Target reading level
            additional_context (str): Additional context
            
        Returns:
            str: Simplified long instruction
        """
        # Split the instruction into chunks
        chunks = self.text_splitter.split_text(instruction)
        
        simplified_chunks = []
        
        for chunk in chunks:
            simplified_chunk = self.simplify_instruction(
                chunk,
                target_reading_level,
                additional_context
            )
            simplified_chunks.append(simplified_chunk)
        
        # Combine the simplified chunks
        return "\n\n".join(simplified_chunks)
    
    def _post_process_simplified_text(self, text: str) -> str:
        """
        Post-process the simplified text to improve readability.
        
        Args:
            text (str): Raw simplified text
            
        Returns:
            str: Post-processed text
        """
        # Remove any remaining model artifacts
        text = re.sub(r'Simplified Instruction:\s*', '', text)
        text = re.sub(r'Medical Instruction:\s*', '', text)
        
        # Ensure proper sentence structure
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Add bullet points for lists if not present
        if '•' not in text and '-' not in text and any(keyword in text.lower() for keyword in ['step', 'first', 'second', 'then', 'next']):
            # Simple heuristic to add bullet points
            lines = text.split('. ')
            if len(lines) > 2:
                text = '• ' + '\n• '.join(lines)
        
        return text
    
    def batch_simplify(self, instructions: List[str], 
                      target_reading_level: str = "8th grade") -> List[str]:
        """
        Simplify multiple instructions in batch.
        
        Args:
            instructions (List[str]): List of medical instructions
            target_reading_level (str): Target reading level
            
        Returns:
            List[str]: List of simplified instructions
        """
        simplified_instructions = []
        
        for i, instruction in enumerate(instructions):
            try:
                logger.info(f"Simplifying instruction {i+1}/{len(instructions)}")
                simplified = self.simplify_instruction(instruction, target_reading_level)
                simplified_instructions.append(simplified)
            except Exception as e:
                logger.error(f"Error simplifying instruction {i+1}: {e}")
                simplified_instructions.append(f"Error: {str(e)}")
        
        return simplified_instructions


# Convenience function for quick simplification
def simplify_instruction(medical_instruction: str,
                        target_reading_level: str = "8th grade",
                        additional_context: str = "") -> str:
    """
    Convenience function to simplify a medical instruction.
    
    Args:
        medical_instruction (str): Complex medical instruction
        target_reading_level (str): Target reading level
        additional_context (str): Additional context
        
    Returns:
        str: Simplified instruction
    """
    simplifier = MedicalInstructionSimplifier()
    return simplifier.simplify_instruction(medical_instruction, target_reading_level, additional_context)


if __name__ == "__main__":
    # Example usage
    simplifier = MedicalInstructionSimplifier()
    
    # Test with sample medical instructions
    sample_instructions = [
        "Administer 500mg of acetaminophen orally every 6 hours as needed for pain management.",
        "Patient should maintain a low-sodium diet and monitor blood pressure daily.",
        "Avoid strenuous physical activity for 2 weeks post-procedure to prevent complications."
    ]
    
    print("Original Instructions:")
    for i, instruction in enumerate(sample_instructions, 1):
        print(f"{i}. {instruction}")
    
    print("\nSimplified Instructions:")
    for i, instruction in enumerate(sample_instructions, 1):
        simplified = simplifier.simplify_instruction(instruction)
        print(f"{i}. {simplified}")
        print()
    
    # Test medication instructions
    med_instruction = simplifier.simplify_medication_instructions(
        "Lisinopril",
        "10mg",
        "once daily",
        "Take in the morning, avoid if blood pressure is too low"
    )
    print("Medication Instructions:")
    print(med_instruction) 