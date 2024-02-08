# Financial Analyst Python Tools

This repository contains a collection of Python tools tailored for financial analysts. These tools are built using the `tkinter` library for the user interface. In order to run them, you could just download and run the scripts, but it's reccomended that the the user use `pyinstaller` to create an executable or application file. All projects output csv files to the users local /Downloads/ folder, the LinkedIn scraper asks the user for a location to download.

**Make sure to read below, as you must supply your own API key or account depending on the project you run!**

## Projects

### 1. LinkedIn Employee Scraper

This tool utilizes the unofficial LinkedIn API to scrape employee information from LinkedIn profiles. It enables users to gather data for analysis and insights related to employees of companies. More specifically, it gets the users name (if possible), they're headline, and their location (or subline). It then attempts to pull the users role from the headline. It pulls ~3 users per second. This project also caches the json responses used to collect data, so in the event that a network issue occurs mid scrape, progress can be easily restored. The user can clear the cache in advanced options. Advanced options also has a login for the user, as well an option to only scrape a certain number of employees.

**In its current state, this only pulls 1000 employees for any given company. A workaround is being worked on.**

#### Usage
1. Install the required packages using `pip install -r requirements.txt`.
2. Sign in with your LinkedIn account by entering your username and password at the top of the linkedin_scraper.py.
3. Run the script to start scraping employee data.

#### PyInstaller Usage
1. Download the LinkedIn directory.
2. Install [PyInstaller](https://pyinstaller.org/en/stable/installation.html).
3. Edit linkedin_scraper.py to add your username and password and save the file. Alternativaely, use the advanced options in the client and enter your username and password there.
4. Run `python -m PyInstaller --onefile --windowed --hidden-import "babel.numbers" --add-data “/path/to/jobs.csv:.” "path/to/linkedin_scraper.py"`.

### 2. Glassdoor Review Scraper

The Glassdoor Review Scraper employs Selenium and an undetected Chrome driver to extract reviews from Glassdoor. It assists in retrieving valuable feedback and ratings about companies for analysis. It pulls ~3 reviews per second. In order to scrape, the user must find the desired organizations reviews page on GlassDoor (For example, Apple: https://www.glassdoor.com/Reviews/Apple-Reviews-E1138.htm) and paste it into the interface.

#### Usage
1. Install the required packages using `pip install -r requirements.txt`.
2. Run the script to initiate the scraping process and retrieve Glassdoor reviews.

#### PyInstaller Usage
1. Download the GlassDoor directory.
2. Install [PyInstaller](https://pyinstaller.org/en/stable/installation.html).
3. Run `python -m PyInstaller --onefile --windowed --hidden-import "babel.numbers" "/path/to/glassdoor_scraper.py"`.
4. Find and run the application. 

### 3. Plane Tracker

The Plane Tracker tool leverages the Open Sky Network API and the Aero Data Box API to get historic flight data. Users can monitor flight data for analysis and research purposes.

#### Usage
1. Install the required packages using `pip install -r requirements.txt`.
2. Obtain an API key from [RapidAPI](https://rapidapi.com/aedbx-aedbx/api/aerodatabox/pricing).
3. Copy and paste your API key into the `rapidapi-key` variable at the top of planetracker.py.
4. Run the script to track planes and access flight data.

#### PyInstaller Usage
1. Download the Plane Tracker directory.
2. Install [PyInstaller](https://pyinstaller.org/en/stable/installation.html).
3. Obtain an API key from [RapidAPI](https://rapidapi.com/aedbx-aedbx/api/aerodatabox/pricing).
4. Copy and paste your API key into the `rapidapi-key` variable in planetracker.py and save the file.
5. Run `python -m PyInstaller --onefile --windowed --add-binary="/path/to/airportsdata/:airportsdata/" --hidden-import "babel.numbers" "/path/to/planetracker.py"`.
6. Find and run the application. 

## Requirements
- Python 3.x
- `tkinter`
- `pyinstaller`
- Selenium
- [Unofficial LinkedIn API](https://github.com/tomquirk/linkedin-api)
- `airportsdata`
- `icao-nnumber-converter-us`
- Undetected Chrome driver
- Requests (for Open Sky Network API)
- API key from RapidAPI (for Aero Data Box API)

## Disclaimer
These tools are provided for educational and research purposes only. Usage of these tools may be subject to the terms and conditions of the respective APIs and platforms they interact with. Use at your own discretion.
