"""
Google Sheets OAuth Service
Handles OAuth flow and Google Sheets creation
"""
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Dict, List, Any

# OAuth 2.0 scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
]

class GoogleSheetsService:
    def __init__(self):
        self.client_id = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
        self.redirect_uri = os.getenv('GOOGLE_OAUTH_REDIRECT_URI')
        
    def get_authorization_url(self, state: str = None) -> str:
        """Generate OAuth authorization URL"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=SCOPES,
            redirect_uri=self.redirect_uri
        )
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'
        )
        
        return authorization_url
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=SCOPES,
            redirect_uri=self.redirect_uri
        )
        
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
    
    def create_spreadsheet(
        self,
        token_data: Dict[str, Any],
        title: str,
        sheets_data: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """
        Create a Google Spreadsheet with multiple sheets
        
        Args:
            token_data: OAuth token information
            title: Spreadsheet title
            sheets_data: Dict with sheet names as keys and data as values
                Example: {
                    'Campaigns': [{'ID': '123', 'Name': 'Campaign 1', ...}],
                    'Ad Groups': [{'ID': '456', 'Name': 'Ad Group 1', ...}]
                }
        
        Returns:
            Spreadsheet URL
        """
        try:
            # Create credentials from token
            credentials = Credentials(
                token=token_data['token'],
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data['token_uri'],
                client_id=token_data['client_id'],
                client_secret=token_data['client_secret'],
                scopes=token_data['scopes']
            )
            
            # Build Sheets API service
            sheets_service = build('sheets', 'v4', credentials=credentials)
            
            # Create spreadsheet
            spreadsheet = {
                'properties': {
                    'title': title
                },
                'sheets': []
            }
            
            # Add sheets
            for sheet_name in sheets_data.keys():
                spreadsheet['sheets'].append({
                    'properties': {
                        'title': sheet_name
                    }
                })
            
            spreadsheet = sheets_service.spreadsheets().create(
                body=spreadsheet
            ).execute()
            
            spreadsheet_id = spreadsheet['spreadsheetId']
            
            # Populate each sheet with data
            for sheet_name, data in sheets_data.items():
                if not data:
                    continue
                    
                # Get headers from first row
                headers = list(data[0].keys())
                
                # Prepare values (headers + data rows)
                values = [headers]
                for row in data:
                    values.append([row.get(h, '') for h in headers])
                
                # Update sheet
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f'{sheet_name}!A1',
                    valueInputOption='RAW',
                    body={'values': values}
                ).execute()
                
                # Format header row (bold)
                requests = [{
                    'repeatCell': {
                        'range': {
                            'sheetId': self._get_sheet_id(sheets_service, spreadsheet_id, sheet_name),
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                },
                                'backgroundColor': {
                                    'red': 0.9,
                                    'green': 0.9,
                                    'blue': 0.9
                                }
                            }
                        },
                        'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                    }
                }]
                
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={'requests': requests}
                ).execute()
            
            # Return spreadsheet URL
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
            
        except HttpError as error:
            raise Exception(f"Error creating spreadsheet: {error}")
    
    def _get_sheet_id(self, service, spreadsheet_id: str, sheet_name: str) -> int:
        """Get sheet ID by name"""
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        for sheet in spreadsheet['sheets']:
            if sheet['properties']['title'] == sheet_name:
                return sheet['properties']['sheetId']
        
        return 0
