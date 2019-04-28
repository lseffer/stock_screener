import requests
from requests import Response
import bs4 as bs
from bs4 import BeautifulSoup, Tag
from utils.models import Stock
from utils.etl_base import ETLBase
from utils.models import Base
from typing import List

STOCK_INFO_URLS = [
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/copenhagen',
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/helsinki',
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/stockholm',
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/first-north',
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/norwegian-listed-shares'
]


def get_stock_info_soup_table(response: Response) -> Tag:
    soup: BeautifulSoup = bs.BeautifulSoup(response.text, 'lxml')
    table: Tag = soup.find('table', {'id': 'listedCompanies'})
    return table


def create_data_from_soup(soup: Tag) -> List[Base]:
    data: List[Base] = []
    # Iterate all rows in table (skip header)
    for row in soup.findAll('tr')[1:]:
        values = [cell.string for cell in row.findChildren('td')]
        record = Stock.process_response(values)
        data.append(record)
    return data


class StockInfoETL(ETLBase):

    @staticmethod
    def job() -> None:
        data: List[Base] = []
        for url in STOCK_INFO_URLS:
            response = requests.get(url)
            soup_table = get_stock_info_soup_table(response)
            data = data + create_data_from_soup(soup_table)
        ETLBase.load_data(data)
