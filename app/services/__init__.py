from app.services.db_service import DatabaseService
from app.services.gpt_service import GPTService
from app.services.proxycurl_service import ProxyCurlService
from app.services.search_service import SearchService
from app.services.sheets_service import GoogleSheetsService

# Create service instances
db_service = DatabaseService()
gpt_service = GPTService()
search_service = SearchService()
proxycurl_service = ProxyCurlService()
sheets_service = GoogleSheetsService()

__all__ = [
    'db_service',
    'gpt_service',
    'search_service',
    'proxycurl_service',
    'sheets_service',
    'DatabaseService',
    'GPTService',
    'ProxyCurlService',
    'SearchService',
    'GoogleSheetsService'
]
