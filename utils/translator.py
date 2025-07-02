"""
Text Translation Module using Google Translate
"""

import os
from typing import Optional, List, Dict, Any
from googletrans import Translator, LANGUAGES
import logging
from dotenv import load_dotenv
import time
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextTranslator:
    """
    A class to translate text using Google Translate API.
    """
    
    def __init__(self):
        """
        Initialize the translator.
        """
        self.translator = Translator()
        self.supported_languages = LANGUAGES
        self._initialize_translator()
    
    def _initialize_translator(self):
        """Initialize the translator with error handling."""
        try:
            # Test the translator with a simple translation
            test_result = self.translator.translate("Hello", dest="es")
            logger.info("Google Translate initialized successfully!")
            
        except Exception as e:
            logger.error(f"Error initializing translator: {e}")
            raise
    
    def translate_text(self, text: str, target_lang: str, source_lang: str = "auto") -> str:
        """
        Translate text to the target language.
        
        Args:
            text (str): Text to translate
            target_lang (str): Target language code (e.g., 'es', 'fr', 'de')
            source_lang (str): Source language code (default: 'auto' for auto-detection)
            
        Returns:
            str: Translated text
        """
        try:
            if not text or not text.strip():
                return ""
            
            # Validate target language
            if target_lang not in self.supported_languages:
                raise ValueError(f"Unsupported target language: {target_lang}")
            
            logger.info(f"Translating text to {target_lang} ({self.supported_languages[target_lang]})")
            
            # Perform translation
            result = self.translator.translate(
                text, 
                dest=target_lang, 
                src=source_lang
            )
            
            translated_text = result.text
            
            logger.info(f"Translation completed. Original length: {len(text)}, Translated length: {len(translated_text)}")
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return f"Translation error: {str(e)}"
    
    def translate_medical_text(self, text: str, target_lang: str, source_lang: str = "auto") -> str:
        """
        Translate medical text with special handling for medical terminology.
        
        Args:
            text (str): Medical text to translate
            target_lang (str): Target language code
            source_lang (str): Source language code
            
        Returns:
            str: Translated medical text
        """
        try:
            # Pre-process medical text to preserve important terms
            processed_text = self._preprocess_medical_text(text)
            
            # Translate the processed text
            translated = self.translate_text(processed_text, target_lang, source_lang)
            
            # Post-process to restore medical terms and formatting
            final_text = self._postprocess_medical_text(translated, target_lang)
            
            return final_text
            
        except Exception as e:
            logger.error(f"Error translating medical text: {e}")
            return f"Medical translation error: {str(e)}"
    
    def translate_instructions(self, instructions: str, target_lang: str, 
                             instruction_type: str = "general") -> str:
        """
        Translate medical instructions with context awareness.
        
        Args:
            instructions (str): Medical instructions to translate
            target_lang (str): Target language code
            instruction_type (str): Type of instruction ('medication', 'discharge', 'general')
            
        Returns:
            str: Translated instructions
        """
        try:
            # Add context based on instruction type
            context_prompt = self._get_instruction_context(instruction_type)
            
            # Combine context with instructions
            full_text = f"{context_prompt}\n\n{instructions}"
            
            # Translate
            translated = self.translate_text(full_text, target_lang)
            
            # Remove context from result
            translated_instructions = translated.replace(
                self.translate_text(context_prompt, target_lang), ""
            ).strip()
            
            return translated_instructions
            
        except Exception as e:
            logger.error(f"Error translating instructions: {e}")
            return f"Instruction translation error: {str(e)}"
    
    def batch_translate(self, texts: List[str], target_lang: str, 
                       source_lang: str = "auto", delay: float = 1.0) -> List[str]:
        """
        Translate multiple texts in batch with rate limiting.
        
        Args:
            texts (List[str]): List of texts to translate
            target_lang (str): Target language code
            source_lang (str): Source language code
            delay (float): Delay between requests to avoid rate limiting
            
        Returns:
            List[str]: List of translated texts
        """
        translated_texts = []
        
        for i, text in enumerate(texts):
            try:
                logger.info(f"Translating text {i+1}/{len(texts)}")
                
                translated = self.translate_text(text, target_lang, source_lang)
                translated_texts.append(translated)
                
                # Add delay to avoid rate limiting
                if i < len(texts) - 1:  # Don't delay after the last translation
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error translating text {i+1}: {e}")
                translated_texts.append(f"Translation error: {str(e)}")
        
        return translated_texts
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of the given text.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict containing language information
        """
        try:
            if not text or not text.strip():
                return {"language": "unknown", "confidence": 0.0}
            
            result = self.translator.detect(text)
            
            return {
                "language": result.lang,
                "confidence": result.confidence,
                "language_name": self.supported_languages.get(result.lang, "Unknown")
            }
            
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            return {"language": "unknown", "confidence": 0.0, "error": str(e)}
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get all supported languages.
        
        Returns:
            Dict mapping language codes to language names
        """
        return self.supported_languages.copy()
    
    def _preprocess_medical_text(self, text: str) -> str:
        """
        Pre-process medical text to preserve important terms.
        
        Args:
            text (str): Original medical text
            
        Returns:
            str: Pre-processed text
        """
        # Common medical terms that should be preserved or handled specially
        medical_terms = {
            "BP": "blood pressure",
            "HR": "heart rate",
            "EKG": "electrocardiogram",
            "ECG": "electrocardiogram",
            "CT": "computed tomography",
            "MRI": "magnetic resonance imaging",
            "IV": "intravenous",
            "ICU": "intensive care unit",
            "ER": "emergency room",
            "OR": "operating room"
        }
        
        processed_text = text
        
        # Replace abbreviations with full terms for better translation
        for abbr, full_term in medical_terms.items():
            processed_text = re.sub(rf'\b{abbr}\b', full_term, processed_text, flags=re.IGNORECASE)
        
        return processed_text
    
    def _postprocess_medical_text(self, text: str, target_lang: str) -> str:
        """
        Post-process translated medical text.
        
        Args:
            text (str): Translated text
            target_lang (str): Target language
            
        Returns:
            str: Post-processed text
        """
        # Common medical terms that might need correction after translation
        medical_corrections = {
            "es": {  # Spanish
                "presión arterial": "BP",
                "frecuencia cardíaca": "HR",
                "electrocardiograma": "EKG",
                "tomografía computarizada": "CT",
                "resonancia magnética": "MRI",
                "intravenoso": "IV",
                "unidad de cuidados intensivos": "ICU",
                "sala de emergencias": "ER",
                "quirófano": "OR"
            },
            "fr": {  # French
                "tension artérielle": "BP",
                "fréquence cardiaque": "HR",
                "électrocardiogramme": "EKG",
                "tomodensitométrie": "CT",
                "imagerie par résonance magnétique": "MRI",
                "intraveineux": "IV",
                "unité de soins intensifs": "ICU",
                "salle d'urgence": "ER",
                "salle d'opération": "OR"
            }
        }
        
        processed_text = text
        
        # Apply corrections for the target language
        if target_lang in medical_corrections:
            for translated_term, abbr in medical_corrections[target_lang].items():
                processed_text = re.sub(
                    rf'\b{translated_term}\b', 
                    abbr, 
                    processed_text, 
                    flags=re.IGNORECASE
                )
        
        return processed_text
    
    def _get_instruction_context(self, instruction_type: str) -> str:
        """
        Get context prompt for different types of instructions.
        
        Args:
            instruction_type (str): Type of instruction
            
        Returns:
            str: Context prompt
        """
        contexts = {
            "medication": "The following are medication instructions for a patient:",
            "discharge": "The following are discharge instructions for a patient:",
            "general": "The following are general medical instructions:"
        }
        
        return contexts.get(instruction_type, contexts["general"])
    
    def translate_with_fallback(self, text: str, target_lang: str, 
                              fallback_langs: List[str] = None) -> str:
        """
        Translate text with fallback languages if the primary translation fails.
        
        Args:
            text (str): Text to translate
            target_lang (str): Primary target language
            fallback_langs (List[str]): List of fallback languages
            
        Returns:
            str: Translated text
        """
        if fallback_langs is None:
            fallback_langs = ["en"]  # Default fallback to English
        
        # Try primary language
        try:
            result = self.translate_text(text, target_lang)
            if not result.startswith("Translation error"):
                return result
        except Exception as e:
            logger.warning(f"Primary translation failed: {e}")
        
        # Try fallback languages
        for fallback_lang in fallback_langs:
            try:
                result = self.translate_text(text, fallback_lang)
                if not result.startswith("Translation error"):
                    logger.info(f"Used fallback language: {fallback_lang}")
                    return result
            except Exception as e:
                logger.warning(f"Fallback translation to {fallback_lang} failed: {e}")
        
        return f"Translation failed for all languages: {target_lang}, {fallback_langs}"


# Convenience function for quick translation
def translate_text(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """
    Convenience function to translate text.
    
    Args:
        text (str): Text to translate
        target_lang (str): Target language code
        source_lang (str): Source language code
        
    Returns:
        str: Translated text
    """
    translator = TextTranslator()
    return translator.translate_text(text, target_lang, source_lang)


def get_supported_languages() -> Dict[str, str]:
    """
    Get all supported languages.
    
    Returns:
        Dict mapping language codes to language names
    """
    translator = TextTranslator()
    return translator.get_supported_languages()


if __name__ == "__main__":
    # Example usage
    translator = TextTranslator()
    
    # Test basic translation
    sample_text = "Take your medication twice daily with food."
    
    print("Original Text:")
    print(sample_text)
    
    # Translate to Spanish
    spanish_translation = translator.translate_text(sample_text, "es")
    print(f"\nSpanish Translation:")
    print(spanish_translation)
    
    # Translate to French
    french_translation = translator.translate_text(sample_text, "fr")
    print(f"\nFrench Translation:")
    print(french_translation)
    
    # Test medical text translation
    medical_text = "Patient has hypertension and diabetes. BP: 140/90, HR: 72 bpm."
    medical_translation = translator.translate_medical_text(medical_text, "es")
    print(f"\nMedical Text Translation (Spanish):")
    print(medical_translation)
    
    # Test language detection
    detected = translator.detect_language(sample_text)
    print(f"\nDetected Language:")
    print(f"Language: {detected['language']} ({detected['language_name']})")
    print(f"Confidence: {detected['confidence']:.2f}")
    
    # Show some supported languages
    print(f"\nSupported Languages (sample):")
    languages = translator.get_supported_languages()
    for code, name in list(languages.items())[:10]:
        print(f"{code}: {name}") 