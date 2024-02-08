# Financial Analyst Python Tools

This repository contains a collection of Python tools tailored for financial analysts. These tools are built using the `tkinter` library for the user interface. In order to run them, the user must use `pyinstaller` to create an executable or application file. All projects output csv files to the users local /Downloads/ folder.

## Projects

### 1. LinkedIn Employee Scraper

This tool utilizes the unofficial LinkedIn API to scrape employee information from LinkedIn profiles. It enables users to gather data for analysis and insights related to professionals on the platform. More specifically, it gets the users name (if possible), they're headline, and their location (or subline). It then attempts to pull the users role from the headline. It pulls ~3 users per second.

#### Usage
1. Install the required packages using `pip install -r requirements.txt`.
2. Sign in with your LinkedIn account by entering your username and password at the top of the script.
3. Run the script to start scraping employee data.

### 2. Glassdoor Review Scraper

The Glassdoor Review Scraper employs Selenium and an undetected Chrome driver to extract reviews from Glassdoor. It assists in retrieving valuable feedback and ratings about companies for analysis. It pulls ~3 reviews per second. In order to scrape, the user must find the desired organizations reviews page on GlassDoor (For example, Apple: https://www.glassdoor.com/Reviews/Apple-Reviews-E1138.htm) and paste it into the interface.

#### Usage
1. Install the required packages using `pip install -r requirements.txt`.
2. Run the script to initiate the scraping process and retrieve Glassdoor reviews.

### 3. Plane Tracker

The Plane Tracker tool leverages the Open Sky Network API and the Aero Data Box API to get historic flight data. Users can monitor flight data for analysis and research purposes.

#### Usage
1. Install the required packages using `pip install -r requirements.txt`.
2. Obtain an API key from [RapidAPI](https://rapidapi.com/aedbx-aedbx/api/aerodatabox/pricing).
3. Copy and paste the API key into the `rapidapi-key` variable at the top of the script.
4. Run the script to track planes and access flight data.

## Requirements
- Python 3.x
- `tkinter`
- `pyinstaller`
- Selenium
- [Unofficial LinkedIn API](https://github.com/tomquirk/linkedin-api)
- airportsdata
- icao-nnumber-converter-us
- Undetected Chrome driver
- Requests (for Open Sky Network API)
- API key from RapidAPI (for Aero Data Box API)

## Disclaimer
These tools are provided for educational and research purposes only. Usage of these tools may be subject to the terms and conditions of the respective APIs and platforms they interact with. Use at your own discretion.
