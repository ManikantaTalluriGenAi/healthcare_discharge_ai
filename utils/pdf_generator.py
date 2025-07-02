"""
PDF Generator Module for Discharge Summaries
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fpdf import FPDF
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DischargeSummaryPDF(FPDF):
    """
    Custom PDF class for generating discharge summaries.
    """
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.set_font("Arial", size=12)
    
    def header(self):
        """Add header to each page."""
        # Logo (if available)
        # self.image('logo.png', 10, 6, 30)
        
        # Hospital name and title
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'DISCHARGE SUMMARY', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'Healthcare Discharge Assistant', 0, 1, 'C')
        self.ln(10)
    
    def footer(self):
        """Add footer to each page."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')
        self.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'R')

class PDFGenerator:
    """
    PDF generator for discharge summaries and medical documents.
    """
    
    def __init__(self):
        """Initialize the PDF generator."""
        self.pdf = None
    
    def create_discharge_summary(self, 
                               patient_data: Dict[str, Any],
                               discharge_summary: str,
                               medications: List[str] = None,
                               follow_up_instructions: str = "",
                               output_path: str = None) -> str:
        """
        Create a discharge summary PDF.
        
        Args:
            patient_data (Dict): Patient information
            discharge_summary (str): Discharge summary text
            medications (List[str]): List of medications
            follow_up_instructions (str): Follow-up instructions
            output_path (str): Output file path
            
        Returns:
            str: Path to generated PDF file
        """
        try:
            # Initialize PDF
            self.pdf = DischargeSummaryPDF()
            self.pdf.alias_nb_pages()
            
            # Generate filename if not provided
            if not output_path:
                patient_name = patient_data.get('name', 'Unknown').replace(' ', '_')
                date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"discharge_summary_{patient_name}_{date_str}.pdf"
            
            # Add content to PDF
            self._add_patient_info(patient_data)
            self._add_discharge_summary(discharge_summary)
            
            if medications:
                self._add_medications(medications)
            
            if follow_up_instructions:
                self._add_follow_up_instructions(follow_up_instructions)
            
            self._add_signature_section()
            
            # Save PDF
            self.pdf.output(output_path)
            logger.info(f"Generated discharge summary PDF: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating discharge summary PDF: {e}")
            raise
    
    def _add_patient_info(self, patient_data: Dict[str, Any]):
        """Add patient information section."""
        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 10, 'PATIENT INFORMATION', 0, 1, 'L')
        self.pdf.ln(5)
        
        fields = [
            ('Name:', 'name'),
            ('Date of Birth:', 'date_of_birth'),
            ('Age:', 'age'),
            ('Gender:', 'gender'),
            ('Admission Date:', 'admission_date'),
            ('Discharge Date:', 'discharge_date'),
            ('Primary Diagnosis:', 'diagnosis')
        ]
        
        for label, key in fields:
            self.pdf.set_font('Arial', 'B', 12)
            self.pdf.cell(40, 8, label, 0, 0)
            self.pdf.set_font('Arial', '', 12)
            value = patient_data.get(key, 'N/A')
            if key == 'discharge_date' and value == 'N/A':
                value = datetime.now().strftime("%Y-%m-%d")
            self.pdf.cell(0, 8, str(value), 0, 1)
        
        self.pdf.ln(10)
    
    def _add_discharge_summary(self, summary: str):
        """Add discharge summary section."""
        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 10, 'DISCHARGE SUMMARY', 0, 1, 'L')
        self.pdf.ln(5)
        
        self.pdf.set_font('Arial', '', 12)
        paragraphs = summary.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                self.pdf.multi_cell(0, 6, paragraph.strip(), 0, 'L')
                self.pdf.ln(3)
        
        self.pdf.ln(10)
    
    def _add_medications(self, medications: List[str]):
        """Add medications section."""
        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 10, 'DISCHARGE MEDICATIONS', 0, 1, 'L')
        self.pdf.ln(5)
        
        self.pdf.set_font('Arial', '', 12)
        for i, medication in enumerate(medications, 1):
            self.pdf.cell(10, 6, f'{i}.', 0, 0)
            self.pdf.cell(0, 6, medication, 0, 1)
        
        self.pdf.ln(10)
    
    def _add_follow_up_instructions(self, instructions: str):
        """Add follow-up instructions section."""
        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 10, 'FOLLOW-UP INSTRUCTIONS', 0, 1, 'L')
        self.pdf.ln(5)
        
        self.pdf.set_font('Arial', '', 12)
        paragraphs = instructions.split('\n\n')
        for paragraph in paragraphs:
            if paragraph.strip():
                self.pdf.multi_cell(0, 6, paragraph.strip(), 0, 'L')
                self.pdf.ln(3)
        
        self.pdf.ln(10)
    
    def _add_signature_section(self):
        """Add signature section."""
        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 10, 'SIGNATURES', 0, 1, 'L')
        self.pdf.ln(5)
        
        # Physician signature
        self.pdf.set_font('Arial', 'B', 12)
        self.pdf.cell(0, 8, 'Attending Physician:', 0, 1, 'L')
        self.pdf.ln(15)
        self.pdf.line(20, self.pdf.get_y(), 80, self.pdf.get_y())
        self.pdf.set_font('Arial', '', 10)
        self.pdf.cell(0, 5, 'Signature', 0, 1, 'L')
        self.pdf.ln(5)
        
        # Date
        self.pdf.set_font('Arial', 'B', 12)
        self.pdf.cell(0, 8, 'Date:', 0, 1, 'L')
        self.pdf.ln(15)
        self.pdf.line(20, self.pdf.get_y(), 80, self.pdf.get_y())
        self.pdf.set_font('Arial', '', 10)
        self.pdf.cell(0, 5, 'Date', 0, 1, 'L')
        self.pdf.ln(10)
        
        # Patient acknowledgment
        self.pdf.set_font('Arial', 'B', 12)
        self.pdf.cell(0, 8, 'Patient/Family Acknowledgment:', 0, 1, 'L')
        self.pdf.ln(15)
        self.pdf.line(20, self.pdf.get_y(), 80, self.pdf.get_y())
        self.pdf.set_font('Arial', '', 10)
        self.pdf.cell(0, 5, 'Signature', 0, 1, 'L')
    
    def create_medication_list(self, 
                             patient_data: Dict[str, Any],
                             medications: List[Dict[str, Any]],
                             output_path: str = None) -> str:
        """
        Create a medication list PDF.
        
        Args:
            patient_data (Dict): Patient information
            medications (List[Dict]): List of medication dictionaries
            output_path (str): Output file path
            
        Returns:
            str: Path to generated PDF file
        """
        try:
            self.pdf = DischargeSummaryPDF()
            self.pdf.alias_nb_pages()
            
            if not output_path:
                patient_name = patient_data.get('name', 'Unknown').replace(' ', '_')
                date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"medication_list_{patient_name}_{date_str}.pdf"
            
            # Add patient info
            self._add_patient_info(patient_data)
            
            # Add medication list
            self.pdf.set_font('Arial', 'B', 14)
            self.pdf.cell(0, 10, 'MEDICATION LIST', 0, 1, 'L')
            self.pdf.ln(5)
            
            # Table headers
            self.pdf.set_font('Arial', 'B', 10)
            self.pdf.cell(50, 8, 'Medication', 1, 0, 'C')
            self.pdf.cell(30, 8, 'Dosage', 1, 0, 'C')
            self.pdf.cell(30, 8, 'Frequency', 1, 0, 'C')
            self.pdf.cell(40, 8, 'Instructions', 1, 0, 'C')
            self.pdf.cell(40, 8, 'Duration', 1, 1, 'C')
            
            # Medication rows
            self.pdf.set_font('Arial', '', 9)
            for med in medications:
                self.pdf.cell(50, 8, med.get('name', ''), 1, 0)
                self.pdf.cell(30, 8, med.get('dosage', ''), 1, 0)
                self.pdf.cell(30, 8, med.get('frequency', ''), 1, 0)
                self.pdf.cell(40, 8, med.get('instructions', ''), 1, 0)
                self.pdf.cell(40, 8, med.get('duration', ''), 1, 1)
            
            self.pdf.output(output_path)
            logger.info(f"Generated medication list PDF: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating medication list PDF: {e}")
            raise
    
    def create_follow_up_plan(self, 
                            patient_data: Dict[str, Any],
                            follow_up_plan: Dict[str, Any],
                            output_path: str = None) -> str:
        """
        Create a follow-up plan PDF.
        
        Args:
            patient_data (Dict): Patient information
            follow_up_plan (Dict): Follow-up plan details
            output_path (str): Output file path
            
        Returns:
            str: Path to generated PDF file
        """
        try:
            self.pdf = DischargeSummaryPDF()
            self.pdf.alias_nb_pages()
            
            if not output_path:
                patient_name = patient_data.get('name', 'Unknown').replace(' ', '_')
                date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"follow_up_plan_{patient_name}_{date_str}.pdf"
            
            # Add patient info
            self._add_patient_info(patient_data)
            
            # Add follow-up plan
            self.pdf.set_font('Arial', 'B', 14)
            self.pdf.cell(0, 10, 'FOLLOW-UP PLAN', 0, 1, 'L')
            self.pdf.ln(5)
            
            # Follow-up appointments
            if 'appointments' in follow_up_plan:
                self.pdf.set_font('Arial', 'B', 12)
                self.pdf.cell(0, 8, 'Scheduled Appointments:', 0, 1, 'L')
                self.pdf.ln(3)
                
                self.pdf.set_font('Arial', '', 12)
                for appointment in follow_up_plan['appointments']:
                    self.pdf.cell(0, 6, f"• {appointment.get('date', '')} - {appointment.get('type', '')} with {appointment.get('provider', '')}", 0, 1)
                self.pdf.ln(5)
            
            # Instructions
            if 'instructions' in follow_up_plan:
                self.pdf.set_font('Arial', 'B', 12)
                self.pdf.cell(0, 8, 'Instructions:', 0, 1, 'L')
                self.pdf.ln(3)
                
                self.pdf.set_font('Arial', '', 12)
                instructions = follow_up_plan['instructions']
                if isinstance(instructions, list):
                    for instruction in instructions:
                        self.pdf.cell(0, 6, f"• {instruction}", 0, 1)
                else:
                    self.pdf.multi_cell(0, 6, instructions, 0, 'L')
                self.pdf.ln(5)
            
            # Warning signs
            if 'warning_signs' in follow_up_plan:
                self.pdf.set_font('Arial', 'B', 12)
                self.pdf.cell(0, 8, 'Warning Signs (Seek Immediate Care):', 0, 1, 'L')
                self.pdf.ln(3)
                
                self.pdf.set_font('Arial', '', 12)
                for sign in follow_up_plan['warning_signs']:
                    self.pdf.cell(0, 6, f"• {sign}", 0, 1)
                self.pdf.ln(5)
            
            self.pdf.output(output_path)
            logger.info(f"Generated follow-up plan PDF: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating follow-up plan PDF: {e}")
            raise
    
    def create_comprehensive_report(self, 
                                  patient_data: Dict[str, Any],
                                  discharge_summary: str,
                                  medications: List[str] = None,
                                  follow_up_instructions: str = "",
                                  lab_results: List[Dict] = None,
                                  vital_signs: Dict[str, Any] = None,
                                  output_path: str = None) -> str:
        """
        Create a comprehensive discharge report PDF.
        
        Args:
            patient_data (Dict): Patient information
            discharge_summary (str): Discharge summary
            medications (List[str]): Medications
            follow_up_instructions (str): Follow-up instructions
            lab_results (List[Dict]): Laboratory results
            vital_signs (Dict): Vital signs
            output_path (str): Output file path
            
        Returns:
            str: Path to generated PDF file
        """
        try:
            self.pdf = DischargeSummaryPDF()
            self.pdf.alias_nb_pages()
            
            if not output_path:
                patient_name = patient_data.get('name', 'Unknown').replace(' ', '_')
                date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"comprehensive_report_{patient_name}_{date_str}.pdf"
            
            # Add all sections
            self._add_patient_info(patient_data)
            self._add_discharge_summary(discharge_summary)
            
            if medications:
                self._add_medications(medications)
            
            if vital_signs:
                self._add_vital_signs(vital_signs)
            
            if lab_results:
                self._add_lab_results(lab_results)
            
            if follow_up_instructions:
                self._add_follow_up_instructions(follow_up_instructions)
            
            self._add_signature_section()
            
            self.pdf.output(output_path)
            logger.info(f"Generated comprehensive report PDF: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating comprehensive report PDF: {e}")
            raise
    
    def _add_vital_signs(self, vital_signs: Dict[str, Any]):
        """Add vital signs section."""
        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 10, 'VITAL SIGNS', 0, 1, 'L')
        self.pdf.ln(5)
        
        self.pdf.set_font('Arial', 'B', 12)
        self.pdf.cell(40, 8, 'Blood Pressure:', 0, 0)
        self.pdf.set_font('Arial', '', 12)
        self.pdf.cell(0, 8, vital_signs.get('blood_pressure', 'N/A'), 0, 1)
        
        self.pdf.set_font('Arial', 'B', 12)
        self.pdf.cell(40, 8, 'Heart Rate:', 0, 0)
        self.pdf.set_font('Arial', '', 12)
        self.pdf.cell(0, 8, str(vital_signs.get('heart_rate', 'N/A')), 0, 1)
        
        self.pdf.set_font('Arial', 'B', 12)
        self.pdf.cell(40, 8, 'Temperature:', 0, 0)
        self.pdf.set_font('Arial', '', 12)
        self.pdf.cell(0, 8, str(vital_signs.get('temperature', 'N/A')), 0, 1)
        
        self.pdf.set_font('Arial', 'B', 12)
        self.pdf.cell(40, 8, 'Oxygen Saturation:', 0, 0)
        self.pdf.set_font('Arial', '', 12)
        self.pdf.cell(0, 8, str(vital_signs.get('oxygen_saturation', 'N/A')), 0, 1)
        
        self.pdf.ln(10)
    
    def _add_lab_results(self, lab_results: List[Dict]):
        """Add laboratory results section."""
        self.pdf.set_font('Arial', 'B', 14)
        self.pdf.cell(0, 10, 'LABORATORY RESULTS', 0, 1, 'L')
        self.pdf.ln(5)
        
        # Table headers
        self.pdf.set_font('Arial', 'B', 10)
        self.pdf.cell(60, 8, 'Test', 1, 0, 'C')
        self.pdf.cell(40, 8, 'Result', 1, 0, 'C')
        self.pdf.cell(40, 8, 'Reference Range', 1, 0, 'C')
        self.pdf.cell(50, 8, 'Status', 1, 1, 'C')
        
        # Lab results rows
        self.pdf.set_font('Arial', '', 9)
        for result in lab_results:
            self.pdf.cell(60, 8, result.get('test', ''), 1, 0)
            self.pdf.cell(40, 8, str(result.get('result', '')), 1, 0)
            self.pdf.cell(40, 8, result.get('reference_range', ''), 1, 0)
            self.pdf.cell(50, 8, result.get('status', ''), 1, 1)
        
        self.pdf.ln(10)


# Convenience functions
def generate_discharge_summary_pdf(patient_data: Dict[str, Any],
                                 discharge_summary: str,
                                 medications: List[str] = None,
                                 follow_up_instructions: str = "",
                                 output_path: str = None) -> str:
    """
    Convenience function to generate discharge summary PDF.
    
    Args:
        patient_data (Dict): Patient information
        discharge_summary (str): Discharge summary text
        medications (List[str]): List of medications
        follow_up_instructions (str): Follow-up instructions
        output_path (str): Output file path
        
    Returns:
        str: Path to generated PDF file
    """
    generator = PDFGenerator()
    return generator.create_discharge_summary(
        patient_data, discharge_summary, medications, 
        follow_up_instructions, output_path
    )


def generate_medication_list_pdf(patient_data: Dict[str, Any],
                               medications: List[Dict[str, Any]],
                               output_path: str = None) -> str:
    """
    Convenience function to generate medication list PDF.
    
    Args:
        patient_data (Dict): Patient information
        medications (List[Dict]): List of medication dictionaries
        output_path (str): Output file path
        
    Returns:
        str: Path to generated PDF file
    """
    generator = PDFGenerator()
    return generator.create_medication_list(patient_data, medications, output_path)


if __name__ == "__main__":
    # Example usage
    generator = PDFGenerator()
    
    # Sample patient data
    patient_data = {
        "name": "John Doe",
        "date_of_birth": "1958-03-15",
        "age": 65,
        "gender": "Male",
        "admission_date": "2024-01-15",
        "discharge_date": "2024-01-20",
        "diagnosis": "Acute Myocardial Infarction"
    }
    
    # Sample discharge summary
    discharge_summary = """
    Mr. John Doe was admitted on January 15, 2024, with chest pain and shortness of breath. 
    Initial evaluation revealed elevated cardiac enzymes and ST-segment elevation on ECG, 
    consistent with acute myocardial infarction.
    
    The patient underwent emergency cardiac catheterization with successful placement of 
    two drug-eluting stents in the left anterior descending artery. Post-procedure course 
    was uncomplicated with resolution of symptoms and stable vital signs.
    
    Patient was educated on cardiac rehabilitation, medication compliance, and lifestyle 
    modifications including smoking cessation, diet modification, and regular exercise.
    """
    
    # Sample medications
    medications = [
        "Aspirin 81mg daily",
        "Metoprolol 25mg twice daily",
        "Lisinopril 10mg daily",
        "Atorvastatin 40mg daily"
    ]
    
    # Sample follow-up instructions
    follow_up_instructions = """
    1. Follow up with cardiologist in 1 week
    2. Begin cardiac rehabilitation program
    3. Monitor blood pressure daily
    4. Report any chest pain, shortness of breath, or swelling immediately
    5. Maintain low-sodium, heart-healthy diet
    """
    
    # Generate PDF
    pdf_path = generator.create_discharge_summary(
        patient_data=patient_data,
        discharge_summary=discharge_summary,
        medications=medications,
        follow_up_instructions=follow_up_instructions
    )
    
    print(f"✅ Generated discharge summary PDF: {pdf_path}")
    
    # Test medication list generation
    medication_data = [
        {"name": "Aspirin", "dosage": "81mg", "frequency": "Daily", "instructions": "Take with food", "duration": "Lifetime"},
        {"name": "Metoprolol", "dosage": "25mg", "frequency": "Twice daily", "instructions": "Take with meals", "duration": "3 months"}
    ]
    
    med_pdf_path = generator.create_medication_list(patient_data, medication_data)
    print(f"✅ Generated medication list PDF: {med_pdf_path}") 