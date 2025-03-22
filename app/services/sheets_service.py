import json
import logging
import os.path
from datetime import datetime
from typing import Dict, List, Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models.database import Profile
from app.utils.config import settings

logger = logging.getLogger(__name__)

# Google Sheets API constants
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SHEET_FIELDS = [
    'Full Name',
    'LinkedIn URL',
    'Job Title',
    'Company',
    'Country',
    'Email',
    'Phone',
    'Total Experience',
    'Industry',
    'Education',
    'Skills',
    'Extracted Date'
]


class GoogleSheetsService:
    """Service for exporting data to Google Sheets"""
    
    def __init__(self):
        self.credentials_path = settings.GOOGLE_API_CREDENTIALS
        self.sheet_id = settings.GOOGLE_SHEET_ID
    
    def _get_credentials(self) -> Credentials:
        """
        Get Google API credentials from the credentials file.
        
        Returns:
            Credentials: The Google API credentials
        """
        try:
            credentials = Credentials.from_service_account_file(
                self.credentials_path, scopes=SCOPES
            )
            return credentials
        except Exception as e:
            logger.error(f"Error getting Google API credentials: {str(e)}")
            raise
    
    def _get_service(self):
        """
        Get Google Sheets API service.
        
        Returns:
            Resource: The Google Sheets API service
        """
        try:
            credentials = self._get_credentials()
            service = build('sheets', 'v4', credentials=credentials)
            return service.spreadsheets()
        except Exception as e:
            logger.error(f"Error getting Google Sheets API service: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def create_sheet(self, sheet_name: str) -> str:
        """
        Create a new sheet in the Google Spreadsheet.
        
        Args:
            sheet_name: The name of the new sheet
            
        Returns:
            str: The new sheet ID
        """
        logger.info(f"Creating new sheet: {sheet_name}")
        
        try:
            sheets = self._get_service()
            
            # Add the new sheet
            request = {
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }
            
            result = sheets.batchUpdate(
                spreadsheetId=self.sheet_id,
                body={'requests': [request]}
            ).execute()
            
            # Get the sheet ID
            sheet_id = result['replies'][0]['addSheet']['properties']['sheetId']
            
            # Add header row
            sheets.values().update(
                spreadsheetId=self.sheet_id,
                range=f"{sheet_name}!A1:L1",
                valueInputOption="RAW",
                body={
                    'values': [SHEET_FIELDS]
                }
            ).execute()
            
            # Format header row
            format_request = {
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.7,
                                'green': 0.7,
                                'blue': 0.7
                            },
                            'textFormat': {
                                'bold': True
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                }
            }
            
            sheets.batchUpdate(
                spreadsheetId=self.sheet_id,
                body={'requests': [format_request]}
            ).execute()
            
            logger.info(f"Created sheet: {sheet_name} with ID: {sheet_id}")
            return sheet_id
        
        except HttpError as e:
            if "already exists" in str(e):
                logger.warning(f"Sheet {sheet_name} already exists, using existing sheet")
                # Get the existing sheet ID
                metadata = sheets.get(
                    spreadsheetId=self.sheet_id, 
                    includeGridData=False
                ).execute()
                
                for sheet in metadata['sheets']:
                    if sheet['properties']['title'] == sheet_name:
                        return sheet['properties']['sheetId']
                
                # If sheet not found despite the error, raise
                logger.error(f"Could not find existing sheet: {sheet_name}")
                raise
            else:
                logger.error(f"Error creating sheet: {str(e)}")
                raise
        except Exception as e:
            logger.error(f"Error creating sheet: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def export_profiles(
        self, profiles: List[Profile], sheet_name: str
    ) -> int:
        """
        Export profiles to Google Sheets.
        
        Args:
            profiles: List of profiles to export
            sheet_name: The name of the sheet to export to
            
        Returns:
            int: The number of profiles exported
        """
        logger.info(f"Exporting {len(profiles)} profiles to sheet: {sheet_name}")
        
        try:
            # Create or get sheet
            sheet_id = await self.create_sheet(sheet_name)
            
            # Prepare data for export
            values = []
            
            for profile in profiles:
                # Extract data from profile
                data = profile.profile_data
                
                full_name = data.get("full_name", "")
                linkedin_url = profile.linkedin_url
                job_title = profile.job_title or data.get("headline", "")
                
                # Get company
                company = ""
                if data.get("experiences"):
                    current_exp = next((exp for exp in data["experiences"] 
                                        if not exp.get("ends_at")), None)
                    if current_exp:
                        company = current_exp.get("company", "")
                
                country = data.get("country_full_name", "")
                
                # Get email and phone (if available)
                email = ""
                phone = ""
                if "contact_info" in data:
                    email = data["contact_info"].get("email", "")
                    phone = data["contact_info"].get("phone_number", "")
                
                # Format skills
                skills = ", ".join(skill.get("name", "") for skill in data.get("skills", []))
                
                # Format education
                education = ", ".join(
                    f"{edu.get('school')}: {edu.get('field_of_study', '')}" 
                    for edu in data.get("education", [])
                )
                
                # Add row
                values.append([
                    full_name,
                    linkedin_url,
                    job_title,
                    company,
                    country,
                    email,
                    phone,
                    str(profile.experience_years or ""),
                    data.get("industry", ""),
                    education,
                    skills,
                    datetime.now().strftime("%Y-%m-%d %H:%M")
                ])
            
            # Export data to sheet
            if values:
                sheets = self._get_service()
                
                sheets.values().append(
                    spreadsheetId=self.sheet_id,
                    range=f"{sheet_name}!A2",
                    valueInputOption="RAW",
                    insertDataOption="INSERT_ROWS",
                    body={
                        'values': values
                    }
                ).execute()
            
            logger.info(f"Exported {len(values)} profiles to sheet: {sheet_name}")
            return len(values)
        
        except Exception as e:
            logger.error(f"Error exporting profiles: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_sheet_url(self, sheet_name: str) -> str:
        """
        Get the URL for a specific sheet in the spreadsheet.
        
        Args:
            sheet_name: The name of the sheet
            
        Returns:
            str: The URL for the sheet
        """
        try:
            base_url = f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit#gid="
            
            # Get sheet ID
            sheets = self._get_service()
            metadata = sheets.get(
                spreadsheetId=self.sheet_id, 
                includeGridData=False
            ).execute()
            
            for sheet in metadata['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    return f"{base_url}{sheet['properties']['sheetId']}"
            
            logger.error(f"Sheet not found: {sheet_name}")
            raise ValueError(f"Sheet not found: {sheet_name}")
        
        except Exception as e:
            logger.error(f"Error getting sheet URL: {str(e)}")
            raise
