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

    # TODO: Remove this legacy five-column migration and its migration-specific
    # tests after all deployed sheets are confirmed migrated; retain validation
    # of the six-column layout.
    def ensure_job_location_column(self, sheet_name: str) -> bool:
        """Ensure the jobs sheet uses the six-column layout with Location in E."""
        header_rows = self.read_sheet(f"{sheet_name}!A1:F1")
        header = header_rows[0] if header_rows else []
        normalized_header = [str(value).strip().lower() for value in header]
        old_header = ["date scraped", "company", "title", "url", "status"]
        new_header = [
            "date scraped",
            "company",
            "title",
            "url",
            "location",
            "status",
        ]

        if normalized_header == new_header:
            return False

        if normalized_header != old_header:
            raise ValueError(
                f"Unexpected header layout in {sheet_name}: {header}. "
                "Expected Date Scraped, Company, Title, Url, Status or "
                "Date Scraped, Company, Title, Url, Location, Status."
            )

        metadata = self.sheet.get(
            spreadsheetId=SPREADSHEET_ID,
            fields="sheets.properties(sheetId,title)",
        ).execute()
        worksheet = next(
            (
                item["properties"]
                for item in metadata.get("sheets", [])
                if item.get("properties", {}).get("title") == sheet_name
            ),
            None,
        )
        if worksheet is None:
            raise ValueError(f"Could not find worksheet named {sheet_name}")

        self.sheet.batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={
                "requests": [
                    {
                        "insertDimension": {
                            "range": {
                                "sheetId": worksheet["sheetId"],
                                "dimension": "COLUMNS",
                                "startIndex": 4,
                                "endIndex": 5,
                            },
                            "inheritFromBefore": True,
                        }
                    },
                    {
                        "updateCells": {
                            "range": {
                                "sheetId": worksheet["sheetId"],
                                "startRowIndex": 0,
                                "endRowIndex": 1,
                                "startColumnIndex": 4,
                                "endColumnIndex": 5,
                            },
                            "rows": [
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {
                                                "stringValue": "Location"
                                            }
                                        }
                                    ]
                                }
                            ],
                            "fields": "userEnteredValue",
                        }
                    },
                ]
            },
        ).execute()
        logger.info("Migrated %s to the six-column job layout", sheet_name)
        return True
