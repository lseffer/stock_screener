# Stock screener
For stocks listed on Nasdaq OMX Nordic 

Script fetches data from Yahoo and Morningstar APIs and outputs stocks ranked from best to worst to Google spreadsheets.

__Loosely based on:__	

Piotroski F-Score - https://en.wikipedia.org/wiki/Piotroski_F-Score

Magic Formula -	https://en.wikipedia.org/wiki/Magic_formula_investing

## Usage:
* Create Google Service Account Credentials JSON
    * Instructions: http://gspread.readthedocs.io/en/latest/oauth2.html
* Create a spreadsheet file in your Google Drive and share it with client_email found in above mentioned JSON file.

Then run
* `pip install -r requirements.txt`
* `python stock_screener.py --sac_file path/to/sac_file.json --gspreadsheet name_or_id_of_your_spreadsheet`

## TO DO:
* Add more screening methods
* Add more columns OR useful information to the google spreadsheet output
* Ask for feedback
