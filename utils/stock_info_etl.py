import requests
from requests import Response
import bs4 as bs
from bs4 import BeautifulSoup, Tag
from utils.models import Stock
from utils.etl_base import ETLBase
from utils.models import Base
from utils.config import logger
from typing import List, Optional

STOCK_INFO_URLS = [
    'https://www.nasdaqomxnordic.com/aktier/listed-companies/copenhagen',
    'https://www.nasdaqomxnordic.com/aktier/listed-companies/helsinki',
    'https://www.nasdaqomxnordic.com/aktier/listed-companies/stockholm',
    'https://www.nasdaqomxnordic.com/aktier/listed-companies/first-north',
    'https://www.nasdaqomxnordic.com/aktier/listed-companies/norwegian-listed-shares'
]

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def get_stock_info_soup_table(response: Response) -> Optional[Tag]:
    soup: BeautifulSoup = bs.BeautifulSoup(response.text, 'lxml')
    table: Optional[Tag] = soup.find('table', {'id': 'listedCompanies'})
    return table


def create_data_from_soup(soup: Tag) -> List[Base]:
    data: List[Base] = []
    for row in soup.findAll('tr')[1:]:
        values = [cell.string for cell in row.findChildren('td')]
        if len(values) >= 5 and values[3]:  # need at least 5 columns and ISIN
            try:
                record = Stock.from_scraped_row(values)
                data.append(record)
            except Exception as e:
                logger.warning('Failed to parse row %s: %s' % (values, e))
    return data


class StockInfoETL(ETLBase):

    @staticmethod
    def job() -> None:
        data: List[Base] = []
        for url in STOCK_INFO_URLS:
            try:
                logger.info('Fetching stock list from %s' % url)
                response = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
                response.raise_for_status()
                soup_table = get_stock_info_soup_table(response)
                if soup_table:
                    new_data = create_data_from_soup(soup_table)
                    logger.info('Found %s stocks from %s' % (len(new_data), url))
                    data = data + new_data
                else:
                    logger.warning('No table found at %s' % url)
            except Exception as e:
                logger.error('Failed to fetch %s: %s' % (url, e))
        logger.info('Total stocks scraped: %s' % len(data))
        ETLBase.load_data(data)
