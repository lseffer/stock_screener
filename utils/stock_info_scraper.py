import requests
import bs4 as bs
from utils.config import Session, logger
from utils.models import Stock
from traceback import format_exc

STOCK_INFO_URLS = [
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/copenhagen',
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/helsinki',
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/stockholm',
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/first-north',
    'http://www.nasdaqomxnordic.com/aktier/listed-companies/norwegian-listed-shares'
]

def get_stock_info_page(url):
    return requests.get(url)

def get_stock_info_soup_table(response):
    soup = bs.BeautifulSoup(response.text, 'lxml')
    table = soup.find('table', {'id': 'listedCompanies'})
    return table

def get_yahoo_ticker(record):
    symbol = record.get('symbol', '')
    symbol = symbol.replace(' ', '-')
    isin_country = record.get('isin', '')[:2]
    currency = record.get('currency', '')
    if isin_country == 'DK':
        return symbol + '.CO'
    elif isin_country == 'SE':
        return symbol + '.ST'
    elif isin_country == 'FI':
        return symbol + '.HE'
    elif isin_country == 'NO':
        return symbol.replace('o', '') + '.OL'
    elif currency == 'DKK':
        return symbol + '.CO'
    elif currency == 'ISK':
        return symbol + '.CO'
    elif currency == 'SEK':
        return symbol + '.ST'
    elif currency == 'EUR':
        return symbol + '.HE'
    elif currency == 'NOK':
        return symbol.replace('o', '') + '.OL'
    else:
        return None

def create_data_from_soup(soup):
    data = []
    # Iterate all rows in table (skip header)
    for row in soup.findAll('tr')[1:]:
        values = [cell.string for cell in row.findChildren('td')]
        record = {
            'isin': values[3],
            'name': values[0],
            'symbol': values[1],
            'currency': values[2],
            'sector': values[4]
        }
        record['yahoo_ticker'] = get_yahoo_ticker(record.copy())
        data.append(record)
    return data

def scrape_stock_info_export_to_pg():
    session = Session()
    for url in STOCK_INFO_URLS:
        response = get_stock_info_page(url)
        soup_table = get_stock_info_soup_table(response)
        data = create_data_from_soup(soup_table)
        for record in data:
            try:
                session.merge(Stock(**record))
            except Exception:
                logger.debug('Something went wrong: %s' % record)
                logger.error(format_exc())
                continue
            logger.debug(record)
        logger.info('Succesfully updated stocks from %s' % url)
        session.commit()
    session.close()
