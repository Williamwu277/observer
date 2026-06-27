from googleapiclient.discovery import build, Resource
from google.oauth2 import service_account
from const import SERVICE_ACCOUNT_FILE, RANGE_NAME, SPREADSHEET_COLUMN_MAP
from dotenv import load_dotenv
from typing import List, Dict
from models import ScrapeResult
from discord_integration import send_discord_update
import logging
import os

logger = logging.getLogger(__name__)


load_dotenv()
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')


def set_up_sheet() -> Resource:
    """
    Grab the spreadsheet object from the Google Sheets API
    """
    logger.info("Setting up Google API connection ...")
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()
    logger.info("Google API connection set up!")
    return sheet


def read_sheet(sheet: Resource) -> List[List[str]]:
    """
    Read ALL the values from the spreadsheet
    """
    results = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME
    ).execute()
    return results.get('values', [])


def update_spreadsheet(sheet: Resource, rows: List[List[str]]) -> None:
    """
    Update ALL the values in the spreadsheet
    """
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption="USER_ENTERED",
        body={"values": rows}
    ).execute()


def insert_rows_at_top(sheet: Resource, num_rows: int) -> None:
    """
    Insert empty rows at the top of the spreadsheet
    """
    requests = [
        {
            "insertDimension": 
            {
                "range": 
                {
                    "sheetId": 0,
                    "dimension": "ROWS",
                    "startIndex": 2,
                    "endIndex": num_rows + 2
                },
                "inheritFromBefore": False
            }
        }
    ]
    sheet.batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"requests": requests}
    ).execute()


def update_results(scraper_names: List[str], results: Dict[str, ScrapeResult]) -> None:
    """
    Update the spreadsheet with the new results
    """
    sheet = set_up_sheet()
    data = read_sheet(sheet)
    for row in data:
        status = row[SPREADSHEET_COLUMN_MAP["Status"]]
        url = row[SPREADSHEET_COLUMN_MAP["Url"]]
        company_name = row[SPREADSHEET_COLUMN_MAP["Company"]]
        if company_name not in scraper_names or status == "Expired": continue
        elif url not in results: row[SPREADSHEET_COLUMN_MAP["Status"]] = "Expired"
        else: del results[url]
    results_to_update = [
        [
            results[url].timestamp,
            results[url].company_name,
            results[url].title,
            results[url].url,
            "Active"
        ] 
        for url in results
    ]

    logger.info(f"Found a total of {len(results_to_update)} new jobs to update!")

    if len(results_to_update) == 0: return

    insert_rows_at_top(sheet, len(results_to_update))
    update_spreadsheet(sheet, results_to_update + data)

    logger.info("Spreadsheet updated!")

    logger.info("Attempting to send Discord messages ...")

    send_queue = []
    while results_to_update:
        current_result = results_to_update.pop(0)
        send_queue.append({
            "title": current_result[1],
            "url": current_result[3],
            "description": current_result[2]
        })
        if len(send_queue) == 10 or not results_to_update:
            status = send_discord_update(send_queue)
            send_queue = []
            # If the message fails the exponential retries, accept the loss and back off
            if not status: break

    logger.info("Finished sending Discord messages!")
