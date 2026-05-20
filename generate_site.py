#!/usr/bin/env python3
"""
Main pipeline: run ETL jobs, compute screening scores, and generate a static website.

Usage:
    python generate_site.py                    # Run full pipeline
    python generate_site.py --skip-etl         # Skip ETL, just regenerate site from existing DB
    python generate_site.py --etl-only         # Run ETL only, no site generation
"""
import argparse
import json
import os
import shutil
from datetime import date, datetime
from pathlib import Path

import polars as pl

from utils.config import DB_PATH, OUTPUT_DIR, engine, get_last_year, logger
from utils.models import Base


def init_database():
    """Create all tables in the SQLite database."""
    logger.info('Initializing database at %s' % DB_PATH)
    Base.metadata.create_all(engine)


def run_etl():
    """Run all ETL jobs sequentially. Each job is isolated so a failure in one
    does not prevent the others from running or data from being persisted."""
    from utils.stock_info_etl import StockInfoETL
    from utils.stock_valuation_etl import StockValuationETL
    from utils.stock_financial_statements_etl import StockFinancialStatementsETL

    etl_steps = [
        ('Stock Info', StockInfoETL),
        ('Financial Statements', StockFinancialStatementsETL),
        ('Stock Valuation', StockValuationETL),
    ]

    failures = []
    for name, etl_class in etl_steps:
        logger.info('=== Running %s ETL ===' % name)
        try:
            etl_class.job()
        except Exception as e:
            logger.error('ETL step "%s" failed: %s' % (name, e))
            failures.append(name)

    if failures:
        logger.warning('ETL completed with failures in: %s' % ', '.join(failures))


def compute_scores():
    """Compute screening scores and return as JSON-serializable list."""
    from scoring import compute_screen_results

    logger.info('=== Computing Screening Scores ===')
    results = compute_screen_results()

    if results.is_empty():
        logger.warning('No screening results computed')
        return []

    # Filter to last fiscal year
    last_year = get_last_year().year
    results = results.with_columns(
        pl.col('report_date').cast(pl.String).str.slice(0, 4).cast(pl.Int32).alias('report_year')
    )
    filtered = results.filter(pl.col('report_year') == last_year).drop('report_year')

    if filtered.is_empty():
        logger.warning('No results for fiscal year %s, returning all results' % last_year)
        filtered = results.drop('report_year')

    # Convert to JSON-serializable format
    def convert_value(v):
        if v is None or (isinstance(v, float) and (v != v)):  # NaN check
            return None
        if isinstance(v, (datetime, date)):
            return v.isoformat()
        return v

    records = filtered.to_dicts()
    for record in records:
        for key in record:
            record[key] = convert_value(record[key])

    logger.info('Generated %s screening results for output' % len(records))
    return records


def generate_site(data):
    """Generate static website with embedded stock data."""
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy static assets
    static_src = Path('web/static')
    if static_src.exists():
        for subdir in ['css', 'js', 'img']:
            src = static_src / subdir
            dst = output_dir / subdir
            if src.exists():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)

    # Write data as JSON file
    data_path = output_dir / 'data.json'
    with open(data_path, 'w') as f:
        json.dump(data, f)
    logger.info('Wrote %s records to %s' % (len(data), data_path))

    # Generate index.html
    generation_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    html = generate_index_html(generation_date)
    index_path = output_dir / 'index.html'
    with open(index_path, 'w') as f:
        f.write(html)
    logger.info('Wrote %s' % index_path)

    # Copy SQLite database to output for download
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, output_dir / 'stocks.db')
        logger.info('Copied database to %s' % (output_dir / 'stocks.db'))


def generate_index_html(generation_date: str) -> str:
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#23191C">
    <title>Nordic Stock Screener</title>
    <link rel="stylesheet" type="text/css" href="https://fonts.googleapis.com/css?family=Open+Sans" />
    <link href="css/index.css" rel="stylesheet">
    <link href="css/tabulator_simple.min.css" rel="stylesheet">
    <script type="text/javascript" src="js/tabulator.min.js"></script>
    <script type="text/javascript" src="js/update_table.js"></script>
</head>
<body onload="loadData();">
    <div class="main">
        <div class="buttonribbon">
            <h1>Nordic Stock Screener</h1>
            <span class="generation-date">Updated: {generation_date}</span>
            <button id="download_data_link" class="actionbtn">Download CSV</button>
            <a href="stocks.db" class="actionbtn" download>Download DB</a>
        </div>
        <div class="tablecontainer">
            <div class="tablewrapper">
                <div id="example-table"></div>
            </div>
        </div>
    </div>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description='Nordic Stock Screener Pipeline')
    parser.add_argument('--skip-etl', action='store_true', help='Skip ETL, regenerate site from existing DB')
    parser.add_argument('--etl-only', action='store_true', help='Run ETL only, skip site generation')
    args = parser.parse_args()

    init_database()

    if not args.skip_etl:
        run_etl()

    if not args.etl_only:
        data = compute_scores()
        generate_site(data)
        logger.info('=== Site generation complete: %s ===' % OUTPUT_DIR)


if __name__ == '__main__':
    main()
