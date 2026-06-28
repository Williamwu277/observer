from googleapiclient.discovery import build
from google.oauth2 import service_account
from const import SERVICE_ACCOUNT_FILE
from dotenv import load_dotenv
from typing import List
import logging
import os

logger = logging.getLogger(__name__)


load_dotenv()
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")


class SheetManager:
    """
    Class to manage the Google Sheets API
    """

    def __init__(self):
        self.sheet = None

    def start(self):
        """
        Grab the spreadsheet object from the Google Sheets API
        """
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        service = build("sheets", "v4", credentials=credentials)
        self.sheet = service.spreadsheets()

    def read_sheet(self, range_name: str) -> List[List[str]]:
        """
        Read ALL the values from the given range of the spreadsheet
        """
        results = (
            self.sheet.values()
            .get(spreadsheetId=SPREADSHEET_ID, range=range_name)
            .execute()
        )
        return results.get("values", [])

    def update_spreadsheet(self, rows: List[List[str]], range_name: str) -> None:
        """
        Update ALL the values in the given range of the spreadsheet
        """
        self.sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": rows},
        ).execute()
