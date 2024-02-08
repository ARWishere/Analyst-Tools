"""
GlassDoor Scraper - GUI Application

This program is a simple GUI application for scraping employee reviews from GlassDoor using Selenium.

Created by Andrew Welling, docstrings provided by ChatGPT.

"""

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import csv
from pathlib import Path
from datetime import datetime
import undetected_chromedriver as uc
import tkinter as tk
from tkinter import simpledialog
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import DateEntry
import sys
from datetime import datetime, timedelta

# closes login prompt on GlassDoor
close_login = """
(function() {
    function addGlobalStyle(css) {
        var head, style;
        head = document.getElementsByTagName('head')[0];
        if (!head) return;
        style = document.createElement('style');
        style.type = 'text/css';
        style.innerHTML = css;
        head.appendChild(style);
    }
    addGlobalStyle("#HardsellOverlay {display:none !important;}");
    addGlobalStyle("body {overflow:auto !important; position: initial !important}");
    window.addEventListener("scroll", event => event.stopPropagation(), true);
    window.addEventListener("mousemove", event => event.stopPropagation(), true);
})();
"""


class DateEntryDialog(simpledialog.Dialog):
    """
    A dialog window for entering a URL and selecting start and end dates.

    Attributes:
        date1 (str): The start date in the format "%Y-%m-%d".
        date2 (str): The end date in the format "%Y-%m-%d".
    """
    def __init__(self, parent, title):
        """
        Initialize the DateEntryDialog.

        Args:
            parent: The parent window.
            title (str): The title of the dialog window.
        """
        self.date1 = None
        self.date2 = None
        simpledialog.Dialog.__init__(self, parent, title)

    def body(self, master):
        """
        Create the dialog body.

        Args:
            master: The master widget.

        Returns:
            tk.Entry: The entry widget for user input.
        """
        tk.Label(master, text="Paste review page URL:").grid(row=0, column=0, sticky="w", padx=10)
        self.user_input_entry = tk.Entry(master)
        self.user_input_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        tk.Label(master, text="Start Date:").grid(row=1, column=0, sticky="w", padx=10)
        tk.Label(master, text="End Date:").grid(row=2, column=0, sticky="w", padx=10)

        self.date1_entry = DateEntry(master, date_pattern="yyyy-mm-dd")
        self.date2_entry = DateEntry(master, date_pattern="yyyy-mm-dd")

        self.date1_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.date2_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        return self.user_input_entry

    def apply(self):
        """Apply the user input."""
        self.user_input = self.user_input_entry.get()
        self.date1 = self.date1_entry.get_date().strftime("%Y-%m-%d")
        self.date2 = self.date2_entry.get_date().strftime("%Y-%m-%d")


def display_error(err, fix):
    """
    Displays the error message in a messagebox.

    Args:
        error (str): The error that occured.
        fix (str): The fix for the error.
    """
    print(err)
    messagebox.showinfo(f"Error {err}", fix)
    sys.exit()


def display_result(user_input, dates):
    """
    Displays the result message in a messagebox.

    Args:
        user_input (str): The entered string.
        dates (tuple): A tuple containing two selected dates.
    """
    result_message = f"Link: {user_input}\nSelected Dates: {dates[0]}, {dates[1]}"
    messagebox.showinfo("Result", f"Download Successful for:\n{result_message}\nCheck your downloads folder")


def eval_url(url):
    if "?sort.sortType=RD&sort.ascending=false&filter.iso3Language=eng" not in url:
        url += "?sort.sortType=RD&sort.ascending=false&filter.iso3Language=eng"
    return url


def start(url, dates):
    """
    Start the web scraping process.

    Args:
        url (str): The URL of the Glassdoor review page.
        dates (tuple): A tuple containing start and end dates.

    Returns:
        list: A list of lists containing review data.
    """
    # create driver and begin the scrape
    opts = uc.ChromeOptions()
    opts.add_argument("--window-size=300,300")
    driver = uc.Chrome(options=opts, use_subprocess=True)
    driver.set_window_size(300, 300)
    data = scrape(driver, url, dates)
    return data


def convert_to_unix_time(date_str):
    """
    Converts a date string to Unix time.

    Args:
        date_str (str): The date string in the format "%Y-%m-%d".

    Returns:
        int: The Unix time corresponding to the input date.
    """
    try:
        date_str = datetime.strptime(date_str, "%b %d, %Y")
        date_str = date_str.strftime("%Y-%m-%d")
    except ValueError:
        print("likely diff format")

    date_object = None

    try:
        date_object = datetime.strptime(str(date_str), "%Y-%m-%d")
    except ValueError:
        try:
            date_object = datetime.strptime(str(date_str), "%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print(e)

    unix_time = int((date_object - datetime(1970, 1, 1)) / timedelta(seconds=1))
    return unix_time


def find_element_approval(element):
    """
    Find the approval status of an element with an approval rating.
    This is for CEO Approval, being approving of the employer, and approving the company outlook

    Args:
        element: The element to check.

    Returns:
        str: The approval status ("Yes", "No", "N/A", "good", or "error").
    """
    try:
        # try and find grey minus sign, the rect
        element.find_element('xpath', './/*[name()="rect"]')
        return "N/A"
    except NoSuchElementException:
        try:
            # try and find the grey circle, the circle
            element.find_element('xpath', './/*[name()="circle"]')
            return "N/A"
        except NoSuchElementException:
            try:
                # this means we found a check mark or x, the path
                # this element will always contain a "d" attribute, which we use
                # to tell us if this is an x or a check
                d_attribute = element.find_element('xpath', './/*[name()="path"]').get_attribute("d")
                # the way we differentiate these 2 cases is if it starts with an uppercase or lowercase m
                # M = x mark, m = check mark
                if d_attribute.startswith("M"):
                    return "No"
                if d_attribute.startswith("m"):
                    return "Yes"
                return "good"
            except NoSuchElementException:
                return "error"


def scrape(driver, url, dates):
    """
    Scrape reviews from Glassdoor.

    Args:
        driver: The Selenium WebDriver.
        url (str): The URL of the Glassdoor review page.
        dates (tuple): A tuple containing start and end dates.

    Returns:
        list: A list of lists containing review data.
    """
    review_list = []
    try:
        # Open the website
        driver.get(url)
        start_unix = convert_to_unix_time(dates[0])
        current_unix_date = start_unix  # we just need a current date to get us started
        end_unix = convert_to_unix_time(dates[1])
        print(end_unix)

        # we have treat end unix as the start point since the reviews start at the most recent
        # so, if the user inputs dates that dont start in the present, we still hav to account for that

        while end_unix >= current_unix_date >= start_unix:
            time.sleep(5)

            # wait for reviews to load
            reviews_ref = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'ReviewsRef'))
            )

            # close login prompt, only used sometimes
            driver.execute_script(close_login)

            elements_with_empReview_id = driver.find_elements('xpath', '//*[starts-with(@id, "empReview")]')

            # print(elements_with_empReview_id)
            for element in elements_with_empReview_id:
                # Extract and print the relevant information from each element
                star_rating = element.find_element('xpath',
                                                   './/*[contains(@class, "review-details__review-details-module__overallRating")]')
                review_title = element.find_element('xpath',
                                                    './/*[contains(@class, "review-details__review-details-module__titleHeadline")]')
                pros_span = element.find_element('xpath', './/span[@data-test="pros"]')
                cons_span = element.find_element('xpath', './/span[@data-test="cons"]')
                review_date = element.find_element('xpath',
                                                   './/*[contains(@class, "review-details__review-details-module__reviewDate")]')
                icon_ratings = element.find_elements('xpath',
                                                     './/*[contains(@class, "mr-std review-details__review-details-module__ratingDetail")]')
                recommend = icon_ratings[0]
                ceo_approval = icon_ratings[1]
                outlook = icon_ratings[2]
                review_date_unix = convert_to_unix_time(review_date.text)

                # only add data if it's in the valid dates the user chose
                if start_unix <= review_date_unix <= end_unix:
                    current_unix_date = convert_to_unix_time(review_date.text)
                    review_list.append([star_rating.text, review_title.text,
                                        find_element_approval(recommend), find_element_approval(ceo_approval),
                                        find_element_approval(outlook),
                                        pros_span.text, cons_span.text, review_date.text])
                if review_date_unix < start_unix:
                    current_unix_date = review_date_unix  # this ends the loop

            # find and click next button
            # wait for next button to load
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Next']"))
            )
            next_button.click()

            # wait for new page to load
            WebDriverWait(driver, 10).until(EC.url_changes(url))
        driver.quit()
        return review_list

    except Exception as e:
        # close the browser window
        print(e)
        driver.quit()
        return review_list


def write_to_csv(data):
    """
    Write data to a CSV file and store in local downloads folder.

    Args:
        data (list): A list of lists containing review data.
    """
    downloads_folder = Path.home() / "Downloads"

    # Create the downloads folder if it doesn't exist
    downloads_folder.mkdir(parents=True, exist_ok=True)
    current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"glassdoor_data_{current_date}.csv"
    filename = filename.replace(" ", "_")

    # Build the local file path
    local_filepath = downloads_folder / filename
    print(local_filepath)

    with open(local_filepath, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Star Rating", "Review Title", "Recommends Company", "CEO Approval",
                             "Positive Company Outlook", "Review Pros", "Review Cons",
                             "Date Published"])  # create header
        for review in data:
            csv_writer.writerow(review)


def main():
    try:
        dialog = DateEntryDialog(root, "GlassDoor Scraper")
        user_input = dialog.user_input
        dates = (dialog.date1, dialog.date2)
        url = eval_url(user_input)
        data = start(url, dates)
        # running start will run the scraping as well
        # now write the data to a csv
        write_to_csv(data)
        if user_input is not None:
            print("")
        display_result(user_input, dates)
        root.destroy()
    except Exception as e:
        display_error(f"{e}", f"{e}")
        print(e)
        sys.exit()


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # hide window until complete

    main()
