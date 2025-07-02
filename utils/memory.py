"""
ChromaDB Memory Module for Patient Profiles
"""

import os
import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PatientProfile:
    """Data class for patient profile information."""
    patient_id: str
    name: str
    age: int
    gender: str
    diagnosis: str
    discharge_date: str
    medications: List[str]
    follow_up_notes: str
    risk_factors: List[str]
    comorbidities: List[str]
    treatment_plan: str
    created_at: str
    updated_at: str

class ChromaDBMemory:
    """
    ChromaDB-based memory system for storing and searching patient profiles.
    """
    
    def __init__(self, 
                 persist_directory: str = "./chroma_db",
                 collection_name: str = "patient_profiles",
                 model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize ChromaDB memory system.
        
        Args:
            persist_directory (str): Directory to persist ChromaDB data
            collection_name (str): Name of the collection for patient profiles
            model_name (str): Sentence transformer model name
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.model_name = model_name
        
        # Initialize sentence transformer model
        self.embedding_model = SentenceTransformer(model_name)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        
        logger.info(f"ChromaDB Memory initialized with model: {model_name}")
    
    def _get_or_create_collection(self):
        """Get existing collection or create new one."""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Using existing collection: {self.collection_name}")
            return collection
        except Exception:
            # Create new collection if it doesn't exist
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Patient profiles for discharge assistant"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
            return collection
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using sentence transformer."""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
    
    def _create_search_text(self, profile: PatientProfile) -> str:
        """Create searchable text from patient profile."""
        search_parts = [
            profile.name,
            profile.diagnosis,
            profile.follow_up_notes,
            profile.treatment_plan,
            " ".join(profile.medications),
            " ".join(profile.risk_factors),
            " ".join(profile.comorbidities)
        ]
        return " ".join(filter(None, search_parts))
    
    def add_patient_profile(self, profile: PatientProfile) -> bool:
        """
        Add a patient profile to the memory system.
        
        Args:
            profile (PatientProfile): Patient profile to add
            
        Returns:
            bool: True if added successfully
        """
        try:
            # Generate unique ID if not provided
            if not profile.patient_id:
                profile.patient_id = str(uuid.uuid4())
            
            # Update timestamps
            if not profile.created_at:
                profile.created_at = datetime.now().isoformat()
            profile.updated_at = datetime.now().isoformat()
            
            # Create searchable text
            search_text = self._create_search_text(profile)
            
            # Generate embedding
            embedding = self._generate_embedding(search_text)
            
            if not embedding:
                logger.error("Failed to generate embedding for patient profile")
                return False
            
            # Convert profile to metadata, handling lists
            metadata = asdict(profile)
            
            # Convert lists to strings for ChromaDB compatibility
            if isinstance(metadata.get('medications'), list):
                metadata['medications'] = ', '.join(metadata['medications'])
            if isinstance(metadata.get('risk_factors'), list):
                metadata['risk_factors'] = ', '.join(metadata['risk_factors'])
            if isinstance(metadata.get('comorbidities'), list):
                metadata['comorbidities'] = ', '.join(metadata['comorbidities'])
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=[embedding],
                documents=[search_text],
                metadatas=[metadata],
                ids=[profile.patient_id]
            )
            
            logger.info(f"Added patient profile: {profile.name} ({profile.patient_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding patient profile: {e}")
            return False
    
    def search_similar_patients(self, 
                              query: str, 
                              n_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar patients based on query.
        
        Args:
            query (str): Search query (diagnosis, symptoms, etc.)
            n_results (int): Number of results to return
            
        Returns:
            List[Dict]: List of similar patient profiles
        """
        try:
            # Generate embedding for query
            query_embedding = self._generate_embedding(query)
            
            if not query_embedding:
                logger.error("Failed to generate embedding for query")
                return []
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Process results
            similar_patients = []
            if results['ids'] and results['ids'][0]:
                for i, patient_id in enumerate(results['ids'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if results['distances'] else None
                    
                    # Convert metadata back to PatientProfile
                    profile = PatientProfile(**metadata)
                    
                    similar_patients.append({
                        'profile': profile,
                        'similarity_score': 1 - distance if distance else None,
                        'patient_id': patient_id
                    })
            
            logger.info(f"Found {len(similar_patients)} similar patients for query: {query}")
            return similar_patients
            
        except Exception as e:
            logger.error(f"Error searching similar patients: {e}")
            return []
    
    def search_by_diagnosis(self, 
                           diagnosis: str, 
                           n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search patients by specific diagnosis.
        
        Args:
            diagnosis (str): Diagnosis to search for
            n_results (int): Number of results to return
            
        Returns:
            List[Dict]: List of patients with similar diagnosis
        """
        return self.search_similar_patients(
            query=diagnosis,
            n_results=n_results
        )
    
    def search_by_medications(self, 
                            medications: List[str], 
                            n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search patients by medications.
        
        Args:
            medications (List[str]): List of medications to search for
            n_results (int): Number of results to return
            
        Returns:
            List[Dict]: List of patients with similar medications
        """
        query = " ".join(medications)
        return self.search_similar_patients(
            query=query,
            n_results=n_results
        )
    
    def search_by_symptoms(self, 
                          symptoms: List[str], 
                          n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search patients by symptoms.
        
        Args:
            symptoms (List[str]): List of symptoms to search for
            n_results (int): Number of results to return
            
        Returns:
            List[Dict]: List of patients with similar symptoms
        """
        query = " ".join(symptoms)
        return self.search_similar_patients(
            query=query,
            n_results=n_results
        )
    
    def get_patient_by_id(self, patient_id: str) -> Optional[PatientProfile]:
        """
        Get patient profile by ID.
        
        Args:
            patient_id (str): Patient ID to retrieve
            
        Returns:
            PatientProfile: Patient profile if found, None otherwise
        """
        try:
            results = self.collection.get(ids=[patient_id])
            
            if results['metadatas'] and results['metadatas'][0]:
                metadata = results['metadatas'][0]
                
                # Convert string fields back to lists
                if isinstance(metadata.get('medications'), str):
                    metadata['medications'] = [med.strip() for med in metadata['medications'].split(',') if med.strip()]
                if isinstance(metadata.get('risk_factors'), str):
                    metadata['risk_factors'] = [risk.strip() for risk in metadata['risk_factors'].split(',') if risk.strip()]
                if isinstance(metadata.get('comorbidities'), str):
                    metadata['comorbidities'] = [comorbidity.strip() for comorbidity in metadata['comorbidities'].split(',') if comorbidity.strip()]
                
                return PatientProfile(**metadata)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting patient by ID: {e}")
            return None
    
    def update_patient_profile(self, patient_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing patient profile.
        
        Args:
            patient_id (str): Patient ID to update
            updates (Dict): Dictionary of fields to update
            
        Returns:
            bool: True if updated successfully
        """
        try:
            # Get existing profile
            existing_profile = self.get_patient_by_id(patient_id)
            if not existing_profile:
                logger.error(f"Patient profile not found: {patient_id}")
                return False
            
            # Update fields
            for key, value in updates.items():
                if hasattr(existing_profile, key):
                    setattr(existing_profile, key, value)
            
            # Update timestamp
            existing_profile.updated_at = datetime.now().isoformat()
            
            # Remove old entry and add updated one
            self.delete_patient_profile(patient_id)
            return self.add_patient_profile(existing_profile)
            
        except Exception as e:
            logger.error(f"Error updating patient profile: {e}")
            return False
    
    def delete_patient_profile(self, patient_id: str) -> bool:
        """
        Delete a patient profile.
        
        Args:
            patient_id (str): Patient ID to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            self.collection.delete(ids=[patient_id])
            logger.info(f"Deleted patient profile: {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting patient profile: {e}")
            return False
    
    def get_all_patients(self, limit: int = 100) -> List[PatientProfile]:
        """
        Get all patient profiles.
        
        Args:
            limit (int): Maximum number of patients to return
            
        Returns:
            List[PatientProfile]: List of all patient profiles
        """
        try:
            results = self.collection.get(limit=limit)
            
            patients = []
            if results['metadatas']:
                for metadata in results['metadatas']:
                    try:
                        # Convert string fields back to lists
                        if isinstance(metadata.get('medications'), str):
                            metadata['medications'] = [med.strip() for med in metadata['medications'].split(',') if med.strip()]
                        if isinstance(metadata.get('risk_factors'), str):
                            metadata['risk_factors'] = [risk.strip() for risk in metadata['risk_factors'].split(',') if risk.strip()]
                        if isinstance(metadata.get('comorbidities'), str):
                            metadata['comorbidities'] = [comorbidity.strip() for comorbidity in metadata['comorbidities'].split(',') if comorbidity.strip()]
                        
                        profile = PatientProfile(**metadata)
                        patients.append(profile)
                    except Exception as e:
                        logger.warning(f"Error parsing patient metadata: {e}")
                        continue
            
            logger.info(f"Retrieved {len(patients)} patient profiles")
            return patients
            
        except Exception as e:
            logger.error(f"Error getting all patients: {e}")
            return []
    
    def get_patients_by_date_range(self, 
                                 start_date: str, 
                                 end_date: str) -> List[PatientProfile]:
        """
        Get patients within a date range.
        
        Args:
            start_date (str): Start date in ISO format
            end_date (str): End date in ISO format
            
        Returns:
            List[PatientProfile]: List of patients in date range
        """
        try:
            # Get all patients and filter by date
            all_patients = self.get_all_patients(limit=1000)
            
            filtered_patients = []
            for patient in all_patients:
                discharge_date = patient.discharge_date
                if start_date <= discharge_date <= end_date:
                    filtered_patients.append(patient)
            
            logger.info(f"Found {len(filtered_patients)} patients in date range")
            return filtered_patients
            
        except Exception as e:
            logger.error(f"Error getting patients by date range: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored patient profiles.
        
        Returns:
            Dict: Statistics about the patient database
        """
        try:
            all_patients = self.get_all_patients(limit=1000)
            
            if not all_patients:
                return {
                    'total_patients': 0,
                    'diagnoses': {}
                }
            
            # Calculate statistics
            diagnoses = {}
            
            for patient in all_patients:
                # Diagnosis frequency
                diagnoses[patient.diagnosis] = diagnoses.get(patient.diagnosis, 0) + 1
            
            return {
                'total_patients': len(all_patients),
                'diagnoses': diagnoses
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def clear_all_data(self) -> bool:
        """
        Clear all patient data from the collection.
        
        Returns:
            bool: True if cleared successfully
        """
        try:
            self.collection.delete(where={})
            logger.info("Cleared all patient data")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing data: {e}")
            return False
    
    def export_data(self, filepath: str) -> bool:
        """
        Export all patient data to JSON file.
        
        Args:
            filepath (str): Path to export file
            
        Returns:
            bool: True if exported successfully
        """
        try:
            all_patients = self.get_all_patients(limit=1000)
            
            data = {
                'export_date': datetime.now().isoformat(),
                'total_patients': len(all_patients),
                'patients': [asdict(patient) for patient in all_patients]
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported {len(all_patients)} patient profiles to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False
    
    def import_data(self, filepath: str) -> bool:
        """
        Import patient data from JSON file.
        
        Args:
            filepath (str): Path to import file
            
        Returns:
            bool: True if imported successfully
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            imported_count = 0
            for patient_data in data.get('patients', []):
                profile = PatientProfile(**patient_data)
                if self.add_patient_profile(profile):
                    imported_count += 1
            
            logger.info(f"Imported {imported_count} patient profiles from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False


# Convenience functions
def create_patient_profile(name: str, 
                          age: int, 
                          gender: str, 
                          diagnosis: str,
                          medications: List[str] = None,
                          follow_up_notes: str = "",
                          risk_factors: List[str] = None,
                          comorbidities: List[str] = None,
                          treatment_plan: str = "") -> PatientProfile:
    """
    Convenience function to create a patient profile.
    
    Args:
        name (str): Patient name
        age (int): Patient age
        gender (str): Patient gender
        diagnosis (str): Primary diagnosis
        medications (List[str]): List of medications
        follow_up_notes (str): Follow-up notes
        risk_factors (List[str]): Risk factors
        comorbidities (List[str]): Comorbidities
        treatment_plan (str): Treatment plan
        
    Returns:
        PatientProfile: Created patient profile
    """
    return PatientProfile(
        patient_id=str(uuid.uuid4()),
        name=name,
        age=age,
        gender=gender,
        diagnosis=diagnosis,
        discharge_date=datetime.now().isoformat(),
        medications=medications or [],
        follow_up_notes=follow_up_notes,
        risk_factors=risk_factors or [],
        comorbidities=comorbidities or [],
        treatment_plan=treatment_plan,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )


if __name__ == "__main__":
    # Example usage
    memory = ChromaDBMemory()
    
    # Create sample patient profiles
    patient1 = create_patient_profile(
        name="John Doe",
        age=65,
        gender="Male",
        diagnosis="Acute Myocardial Infarction",
        medications=["Aspirin 81mg", "Metoprolol 25mg"],
        follow_up_notes="Patient stable post-MI, needs cardiac rehab",
        risk_factors=["Hypertension", "Diabetes"],
        comorbidities=["Type 2 Diabetes"],
        treatment_plan="Cardiac rehabilitation, medication compliance"
    )
    
    # Add patient to memory
    memory.add_patient_profile(patient1)
    
    # Search for similar patients
    similar_patients = memory.search_by_diagnosis("heart attack")
    print(f"Found {len(similar_patients)} patients with heart attack")
    
    for result in similar_patients:
        profile = result['profile']
        score = result['similarity_score']
        print(f"{profile.name} - {profile.diagnosis} (similarity: {score:.3f})")
    
    # Get statistics
    stats = memory.get_statistics()
    print(f"Total patients: {stats['total_patients']}")
    print(f"Diagnoses: {stats['diagnoses']}") 