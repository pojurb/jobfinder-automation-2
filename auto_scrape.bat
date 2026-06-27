@echo off
cd /d "%~dp0"
echo Running Job Scraper Pipeline...
python scrape.py
python score.py
python build.py
echo Pipeline finished.
