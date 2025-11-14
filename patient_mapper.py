"""
Patient ID Mapping Strategies for Telegram Bot (Prototype)

Three approaches ranked by simplicity and suitability for prototypes
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


# JSON File Storage (for Prototype)

class JSONPatientMapper:
    """
    JSON file-based mapping: Persistent across restarts
    Perfect for: Prototypes, small-scale deployments, easy debugging
    """
    
    def __init__(self, mapping_file: str = "patient_mappings.json"):
        self.mapping_file = Path(mapping_file)
        self.mappings: Dict[str, str] = {}
        self._load_mappings()
    
    def _load_mappings(self):
        """Load mappings from JSON file"""
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file, 'r') as f:
                    data = json.load(f)
                    # Convert keys back to strings (JSON keys are always strings)
                    self.mappings = {str(k): v for k, v in data.items()}
                logger.info(f"Loaded {len(self.mappings)} patient mappings")
            except Exception as e:
                logger.error(f"Error loading mappings: {e}")
                self.mappings = {}
        else:
            logger.info("No existing mappings file found, starting fresh")
            self.mappings = {}
    
    def _save_mappings(self):
        """Save mappings to JSON file"""
        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(self.mappings, f, indent=2)
            logger.info(f"Saved {len(self.mappings)} patient mappings")
        except Exception as e:
            logger.error(f"Error saving mappings: {e}")
    
    def get_patient_id(self, telegram_user_id: int) -> str:
        """
        Get patient ID for a telegram user
        Auto-generates if not found (good for prototype)
        """
        user_key = str(telegram_user_id)
        
        if user_key in self.mappings:
            patient_id = self.mappings[user_key]
            logger.info(f"Found patient ID for user {telegram_user_id}: {patient_id}")
            return patient_id
        
        # Auto-generate patient ID for new users
        patient_id = f"PATIENT_{telegram_user_id}"
        self.add_mapping(telegram_user_id, patient_id)
        logger.info(f"Auto-generated patient ID for new user {telegram_user_id}: {patient_id}")
        
        return patient_id
    
    def add_mapping(self, telegram_user_id: int, patient_id: str):
        """Add or update a mapping"""
        user_key = str(telegram_user_id)
        self.mappings[user_key] = patient_id
        self._save_mappings()
        logger.info(f"Added mapping: {telegram_user_id} -> {patient_id}")
    
    def remove_mapping(self, telegram_user_id: int) -> bool:
        """Remove a mapping"""
        user_key = str(telegram_user_id)
        if user_key in self.mappings:
            del self.mappings[user_key]
            self._save_mappings()
            logger.info(f"Removed mapping for user {telegram_user_id}")
            return True
        return False
    
    def list_all_mappings(self) -> Dict[int, str]:
        """List all mappings (useful for admin)"""
        return {int(k): v for k, v in self.mappings.items()}


# Phone Number Mapping

class PhonePatientMapper(JSONPatientMapper):
    """
    Phone number-based mapping (if required)
    Uses JSON storage but with phone as intermediate key
    """
    
    def __init__(self, mapping_file: str = "phone_patient_mappings.json"):
        super().__init__(mapping_file)
        self.phone_mappings: Dict[str, str] = {}
        self._load_phone_mappings()
    
    def _load_phone_mappings(self):
        """Load phone number mappings"""
        phone_file = Path("phone_mappings.json")
        if phone_file.exists():
            try:
                with open(phone_file, 'r') as f:
                    self.phone_mappings = json.load(f)
            except Exception as e:
                logger.error(f"Error loading phone mappings: {e}")
    
    def register_phone(self, telegram_user_id: int, phone_number: str, patient_id: str):
        """Register a phone number with patient ID"""
        # Normalize phone number (remove spaces, dashes, etc.)
        clean_phone = ''.join(filter(str.isdigit, phone_number))
        
        # Save both mappings
        self.phone_mappings[clean_phone] = patient_id
        self.add_mapping(telegram_user_id, patient_id)
        
        # Save phone mappings
        with open("phone_mappings.json", 'w') as f:
            json.dump(self.phone_mappings, f, indent=2)
        
        logger.info(f"Registered phone {clean_phone} -> {patient_id} for user {telegram_user_id}")
    
    def get_patient_by_phone(self, phone_number: str) -> Optional[str]:
        """Get patient ID by phone number"""
        clean_phone = ''.join(filter(str.isdigit, phone_number))
        return self.phone_mappings.get(clean_phone)



def get_patient_mapper(mode: str = "json") -> object:
    """
    Factory function to get appropriate mapper
    
    Args:
        mode: 'json' or 'phone'
    
    Returns:
        Appropriate mapper instance
    """
    if mode == "json":
        return JSONPatientMapper()
    elif mode == "phone":
        return PhonePatientMapper()
    else:
        logger.warning(f"Unknown mode {mode}, defaulting to JSON")
        return JSONPatientMapper()


# Testing the mapper
if __name__ == "__main__":
    
    print("\n" + "=" * 60)
    print("OPTION 2: JSON File Storage (RECOMMENDED)")
    print("=" * 60)
    mapper2 = JSONPatientMapper()
    print(f"User 123456789 -> {mapper2.get_patient_id(123456789)}")
    mapper2.add_mapping(123456789, "PATIENT_JOHN_DOE")
    print(f"Updated: User 123456789 -> {mapper2.get_patient_id(123456789)}")
    print(f"All mappings: {mapper2.list_all_mappings()}")