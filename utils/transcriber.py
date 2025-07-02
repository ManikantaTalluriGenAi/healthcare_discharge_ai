"""
Audio Transcription Module using OpenAI Whisper
"""

import os
import whisper
import torch
from typing import Optional, Dict, Any
from pathlib import Path
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioTranscriber:
    """
    A class to transcribe audio files using OpenAI Whisper.
    """
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize the transcriber with a specified Whisper model.
        
        Args:
            model_name (str): Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            logger.info(f"Loading Whisper model: {self.model_name}")
            
            # Check if CUDA is available for GPU acceleration
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            # Load the model
            self.model = whisper.load_model(self.model_name, device=device)
            logger.info("Whisper model loaded successfully!")
            
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            raise
    
    def transcribe_audio(self, audio_path: str, 
                        language: Optional[str] = None,
                        task: str = "transcribe",
                        verbose: bool = False) -> str:
        """
        Transcribe an audio file to text.
        
        Args:
            audio_path (str): Path to the audio file
            language (str, optional): Language code (e.g., 'en', 'es', 'fr'). If None, auto-detect
            task (str): Either 'transcribe' or 'translate' (translate to English)
            verbose (bool): Whether to print verbose output
            
        Returns:
            str: Transcribed text
        """
        try:
            # Validate audio file path
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Check if model is loaded
            if self.model is None:
                raise ValueError("Whisper model not loaded. Please initialize the transcriber.")
            
            logger.info(f"Transcribing audio file: {audio_path}")
            
            # Prepare transcription options
            options = {
                "task": task,
                "verbose": verbose
            }
            
            # Add language if specified
            if language:
                options["language"] = language
                logger.info(f"Using specified language: {language}")
            
            # Perform transcription
            result = self.model.transcribe(audio_path, **options)
            
            # Extract transcribed text
            transcribed_text = result["text"].strip()
            
            logger.info(f"Transcription completed. Length: {len(transcribed_text)} characters")
            
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise
    
    def transcribe_with_metadata(self, audio_path: str, 
                                language: Optional[str] = None,
                                task: str = "transcribe") -> Dict[str, Any]:
        """
        Transcribe audio and return detailed metadata.
        
        Args:
            audio_path (str): Path to the audio file
            language (str, optional): Language code
            task (str): Either 'transcribe' or 'translate'
            
        Returns:
            Dict containing transcription and metadata
        """
        try:
            if not os.path.exists(audio_path):
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            if self.model is None:
                raise ValueError("Whisper model not loaded.")
            
            logger.info(f"Transcribing audio with metadata: {audio_path}")
            
            # Prepare options
            options = {
                "task": task,
                "verbose": False
            }
            
            if language:
                options["language"] = language
            
            # Perform transcription
            result = self.model.transcribe(audio_path, **options)
            
            # Extract metadata
            metadata = {
                "text": result["text"].strip(),
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "audio_path": audio_path,
                "model_used": self.model_name
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error transcribing audio with metadata: {e}")
            raise
    
    def transcribe_medical_audio(self, audio_path: str, 
                                language: Optional[str] = None) -> str:
        """
        Specialized transcription for medical audio with medical terminology handling.
        
        Args:
            audio_path (str): Path to the audio file
            language (str, optional): Language code
            
        Returns:
            str: Transcribed medical text
        """
        try:
            logger.info(f"Transcribing medical audio: {audio_path}")
            
            # Use larger model for better medical terminology recognition
            if self.model_name in ["tiny", "base"]:
                logger.warning("Consider using 'small' or larger model for better medical terminology recognition")
            
            # Transcribe with medical context
            transcribed_text = self.transcribe_audio(
                audio_path=audio_path,
                language=language,
                task="transcribe"
            )
            
            # Post-process for medical terminology
            processed_text = self._post_process_medical_text(transcribed_text)
            
            return processed_text
            
        except Exception as e:
            logger.error(f"Error transcribing medical audio: {e}")
            raise
    
    def _post_process_medical_text(self, text: str) -> str:
        """
        Post-process transcribed text for medical terminology.
        
        Args:
            text (str): Raw transcribed text
            
        Returns:
            str: Processed medical text
        """
        # Common medical abbreviations and corrections
        medical_corrections = {
            "b p": "BP",
            "h r": "HR",
            "o2": "O2",
            "e k g": "EKG",
            "e c g": "ECG",
            "c t": "CT",
            "m r i": "MRI",
            "x ray": "X-ray",
            "i v": "IV",
            "i c u": "ICU",
            "e r": "ER",
            "o r": "OR"
        }
        
        processed_text = text
        
        # Apply corrections
        for incorrect, correct in medical_corrections.items():
            processed_text = processed_text.replace(incorrect, correct)
        
        return processed_text
    
    def batch_transcribe(self, audio_files: list, 
                        output_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Transcribe multiple audio files in batch.
        
        Args:
            audio_files (list): List of audio file paths
            output_dir (str, optional): Directory to save transcriptions
            
        Returns:
            Dict mapping file paths to transcriptions
        """
        results = {}
        
        for audio_file in audio_files:
            try:
                logger.info(f"Processing: {audio_file}")
                
                # Transcribe the file
                transcription = self.transcribe_audio(audio_file)
                results[audio_file] = transcription
                
                # Save to file if output directory specified
                if output_dir:
                    self._save_transcription(audio_file, transcription, output_dir)
                
            except Exception as e:
                logger.error(f"Error processing {audio_file}: {e}")
                results[audio_file] = f"Error: {str(e)}"
        
        return results
    
    def _save_transcription(self, audio_file: str, transcription: str, output_dir: str):
        """
        Save transcription to a text file.
        
        Args:
            audio_file (str): Original audio file path
            transcription (str): Transcribed text
            output_dir (str): Output directory
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output filename
            audio_filename = Path(audio_file).stem
            output_file = os.path.join(output_dir, f"{audio_filename}_transcription.txt")
            
            # Save transcription
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"Transcription of: {audio_file}\n")
                f.write("=" * 50 + "\n\n")
                f.write(transcription)
            
            logger.info(f"Transcription saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving transcription: {e}")


# Convenience function for quick transcription
def transcribe_audio(audio_path: str, 
                    model_name: str = "base",
                    language: Optional[str] = None) -> str:
    """
    Convenience function to transcribe an audio file.
    
    Args:
        audio_path (str): Path to the audio file
        model_name (str): Whisper model size
        language (str, optional): Language code
        
    Returns:
        str: Transcribed text
    """
    transcriber = AudioTranscriber(model_name=model_name)
    return transcriber.transcribe_audio(audio_path, language=language)


def get_available_models() -> list:
    """
    Get list of available Whisper models.
    
    Returns:
        list: Available model names
    """
    return ["tiny", "base", "small", "medium", "large"]


if __name__ == "__main__":
    # Example usage
    transcriber = AudioTranscriber(model_name="base")
    
    # Example audio file path (replace with actual path)
    sample_audio = "sample_audio.wav"
    
    if os.path.exists(sample_audio):
        try:
            # Basic transcription
            text = transcriber.transcribe_audio(sample_audio)
            print("Transcribed Text:")
            print(text)
            
            # Transcription with metadata
            metadata = transcriber.transcribe_with_metadata(sample_audio)
            print("\nMetadata:")
            print(f"Language: {metadata['language']}")
            print(f"Model used: {metadata['model_used']}")
            
        except Exception as e:
            print(f"Error: {e}")
    else:
        print(f"Sample audio file not found: {sample_audio}")
        print("Please provide a valid audio file path for testing.") 