# TODO for v3
## Architecture:

* Front-end webserver 
  * Serving a dash site
  * Querying database for stocks, info etc.
* Worker back-end webserver
  * Scrapes data and writes to Database
  * Some machine learning later on?
  * Initializes database
  * Using Celert for scheduling?
* Database
  * A postgres database
