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
import subprocess
from datetime import date, datetime
from pathlib import Path

import polars as pl

from utils.config import DB_PATH, OUTPUT_DIR, engine, get_last_year, get_logger
from utils.models import Base

logger = get_logger('pipeline')


WEB_APP_DIR = Path(__file__).parent / 'web' / 'app'
WEB_APP_DIST = WEB_APP_DIR / 'dist'


def init_database():
    """Create all tables in the SQLite database."""
    logger.info('Initializing database at %s', DB_PATH)
    Base.metadata.create_all(engine)


def run_etl():
    """Run all ETL jobs sequentially. Each job is isolated so a failure in one
    does not prevent the others from running or data from being persisted."""
    from utils.stock_info_etl import StockInfoETL
    from utils.stock_valuation_etl import StockValuationETL
    from utils.stock_financial_statements_etl import StockFinancialStatementsETL
    from utils.stock_price_history_etl import StockPriceHistoryETL

    etl_steps = [
        ('Stock Info', StockInfoETL),
        ('Financial Statements', StockFinancialStatementsETL),
        ('Stock Valuation', StockValuationETL),
        ('Price History', StockPriceHistoryETL),
    ]

    failures = []
    for name, etl_class in etl_steps:
        logger.info('=== Running %s ETL ===', name)
        try:
            etl_class.job()
        except Exception:
            logger.exception('ETL step "%s" failed', name)
            failures.append(name)

    if failures:
        logger.warning('ETL completed with failures in: %s', ', '.join(failures))


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
        logger.warning('No results for fiscal year %s, returning all results', last_year)
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

    logger.info('Generated %s screening results for output', len(records))
    return records


def build_web_app():
    """Build the Vite/React frontend if a build hasn't been produced yet.

    The CI workflow runs `npm ci && npm run build` before invoking this
    script, so this fallback is mainly for local development. It is silently
    skipped if Node/npm is unavailable and a prebuilt dist already exists.
    """
    index_html = WEB_APP_DIST / 'index.html'
    if index_html.exists():
        logger.info('Using prebuilt frontend at %s', WEB_APP_DIST)
        return

    if not WEB_APP_DIR.exists():
        raise FileNotFoundError(
            'Frontend source directory %s is missing' % WEB_APP_DIR
        )

    npm = shutil.which('npm')
    if npm is None:
        raise RuntimeError(
            'Frontend has not been built and npm is not available. '
            'Run `npm ci && npm run build` inside %s and retry.' % WEB_APP_DIR
        )

    logger.info('Building frontend in %s', WEB_APP_DIR)
    if not (WEB_APP_DIR / 'node_modules').exists():
        subprocess.run([npm, 'ci'], cwd=WEB_APP_DIR, check=True)
    subprocess.run([npm, 'run', 'build'], cwd=WEB_APP_DIR, check=True)


def generate_site(data):
    """Generate static website with embedded stock data."""
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    build_web_app()

    # Copy the Vite dist into the output dir
    if not WEB_APP_DIST.exists():
        raise FileNotFoundError(
            'Expected built frontend at %s but it does not exist' % WEB_APP_DIST
        )

    for entry in WEB_APP_DIST.iterdir():
        dst = output_dir / entry.name
        if entry.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(entry, dst)
        else:
            shutil.copy2(entry, dst)

    # Write data as a JSON envelope (rows + metadata)
    generation_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    payload = {'generated_at': generation_date, 'rows': data}
    data_path = output_dir / 'data.json'
    with open(data_path, 'w') as f:
        json.dump(payload, f)
    logger.info('Wrote %s records to %s', len(data), data_path)

    # Copy SQLite database to output for download
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, output_dir / 'stocks.db')
        logger.info('Copied database to %s', output_dir / 'stocks.db')


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
        logger.info('=== Site generation complete: %s ===', OUTPUT_DIR)


if __name__ == '__main__':
    main()
