#!/bin/bash

alembic upgrade head
python worker.py
