"""
Plane Tracker - GUI Application

This program is a simple GUI application for getting historic flight data for an aircraft with some tail number.
It utilizes both the OpenSky API (data before oct 1) and the AeroDataBox API (data on/after oct 1) to pull flight data.
The airportsdata library and airports csv (https://github.com/mborsetti/airportsdata) is also used

Created by Andrew Welling, docstrings provided by ChatGPT.

"""

import time
import tkinter as tk
from tkinter import simpledialog
from tkinter import messagebox
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime, timedelta
from icao_nnumber_converter_us import n_to_icao, icao_to_n
from opensky_api import OpenSkyApi
import airportsdata
import json
import csv
import os
import sys
import requests
from pathlib import Path

month_in_unix = 2592000
oct_1_2023_unix = 1696143600
# user must supply their own AeroDataBox rapid api key
rapidapi_key = ""

class DateEntryDialog(simpledialog.Dialog):
    """
    A dialog window for entering a tail number and selecting start and end dates.

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
        tk.Label(master, text="Enter Tail Number:").grid(row=0, column=0, sticky="w", padx=10)
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


def get_dates():
    """
    Opens a DateEntryDialog to allow the user to select two dates.

    Returns:
        tuple: A tuple containing two selected dates.
    """
    dialog = DateEntryDialog(root, "Flight Tracker Client")
    date1 = dialog.date1
    date2 = dialog.date2
    return date1, date2


class LoadingBarPopup:
    """
    A popup window with a loading bar to indicate progress.

    Attributes:
        root: The root window.
        dialog: The dialog window.
        final_val (int): The final value for progress calculation.
        start_val (int): The starting value for progress calculation.
        loading_label: The label indicating the loading status.
        progress_var: The variable for progress tracking.
        loading_bar: The progress bar widget.
    """
    def __init__(self, root, start_val, final_val):
        """
        Initialize the LoadingBarPopup.

        Args:
            root: The root window.
            start_val (int): The starting value for progress calculation.
            final_val (int): The final value for progress calculation.
        """

        # note: both start and final should be in unix time
        self.root = root
        self.dialog = tk.Toplevel(root)
        self.dialog.title("Retrieval Progress")
        self.dialog.geometry("225x50")
        self.final_val = final_val
        self.start_val = start_val

        self.loading_label = ttk.Label(self.dialog, text="Obtaining Data...")
        self.loading_label.pack()

        self.progress_var = tk.DoubleVar()
        self.loading_bar = ttk.Progressbar(self.dialog, variable=self.progress_var, length=200,
                                           mode='determinate', orient="horizontal")
        self.progress_var.set(0)
        self.loading_bar.pack()

    def update_progress(self, current):
        """
        Update the progress of the loading bar.

        Args:
            current (int): The current progress value.
        """
        # map the current value between start and end to the position in the progress bar
        mapped_value = 100 * ((current - self.start_val) / (self.final_val - self.start_val))
        if mapped_value < 100:
            self.progress_var.set(mapped_value)
        else:
            self.dialog.destroy()  # close the window when progress reaches the end
        self.dialog.update()
        self.root.update()


def display_result(user_input, dates):
    """
    Displays the result message in a messagebox.

    Args:
        user_input (str): The entered string.
        dates (tuple): A tuple containing two selected dates.
    """
    result_message = f"Registration: {user_input}\nSelected Dates: {dates[0]}, {dates[1]}"
    messagebox.showinfo("Result", f"Download Successful for:\n{result_message}")


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


# we need to convert to unix time to use with opensky api
def convert_to_unix_time(date_str):
    """
    Converts a date string to Unix time.

    Args:
        date_str (str): The date string in the format "%Y-%m-%d".

    Returns:
        int: The Unix time corresponding to the input date.
    """
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


# convert back to regular time for the csv file
def convert_unix_to_regular(unix_time):
    """
    Converts Unix time to a regular time string.

    Args:
        unix_time (int): The Unix time.

    Returns:
        str: The regular time string in the format '%Y-%m-%d %H:%M:%S'.
    """
    regular_time = datetime.utcfromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')
    return regular_time


def get_plane_data(id, date1, date2, load_bar):
    """
    Retrieves flight data for a plane based on the given parameters.

    Args:
        id (str): Aircraft identifier - The tail number.
        date1 (str): Start date in the format "%Y-%m-%d".
        date2 (str): End date in the format "%Y-%m-%d".
        load_bar (tkinter obj) : The loading bar pop up

    Returns:
        list: A list containing flight data.
    """
    icao_num = n_to_icao(id)
    flight_data = []
    date1_unix = convert_to_unix_time(date1)
    date2_unix = convert_to_unix_time(date2)
    # if start date is above oct 1, use only aero box to get data
    if date1_unix >= oct_1_2023_unix:
        flight_data = get_plane_data_ADB(icao_num, date1, date2, load_bar)

    # if end date is below or equal to oct 1, only use open sky
    if date2_unix < oct_1_2023_unix:
        flight_data = get_plane_data_OSN(icao_num, date1_unix, date2_unix, load_bar)

    # if oct 1 2023 is included, OSN and ADB must be used together to get data
    if date1_unix < oct_1_2023_unix <= date2_unix:
        oct1dt = datetime(2023, 10, 1)
        flight_data.append(get_plane_data_OSN(icao_num, date1_unix, oct_1_2023_unix, load_bar))
        flight_data.append(get_plane_data_ADB(icao_num, oct1dt.strftime('%Y-%m-%d'), date2, load_bar))

    return flight_data


def get_plane_data_ADB(icao_num, date1, date2, load_bar):
    """
    Retrieves flight data for a plane using the Aero Data Box API.

    Args:
        icao_num (str): Aircraft ICAO code.
        date1 (str): Start date in the format "%Y-%m-%d".
        date2 (str): End date in the format "%Y-%m-%d".

    Returns:
        list: A list containing flight data.
    """
    current_date = datetime.strptime(date1, "%Y-%m-%d")
    flight_data = []

    while convert_to_unix_time(current_date.strftime("%Y-%m-%d")) <= convert_to_unix_time(date2):
        # get data for date
        data = get_data_for_date(current_date.strftime("%Y-%m-%d"), icao_num)
        time.sleep(.25)
        if data is not None:
            flight_data.append(data)
        load_bar.update_progress(convert_to_unix_time(current_date.strftime("%Y-%m-%d")))
        current_date += timedelta(days=1)

    return flight_data


def get_data_for_date(date, icao):
    """
    Retrieves flight data for a specified date using the Aero Data Box API.

    Args:
        date (str): Date in the format "%Y-%m-%d".
        icao (str): Aircraft ICAO code.

    Returns:
        list: A list containing flight data.
    """
    url = f"https://aerodatabox.p.rapidapi.com/flights/icao24/{icao}/{date}"
    querystring = {"withAircraftImage": "false", "withLocation": "true"}
    # user must fill in their own rapid-api key
    headers = {
        "X-RapidAPI-Key": rapidapi_key,
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
    }
    data = []
    response = requests.get(url, headers=headers, params=querystring)
    if not response.ok:
        print("error")
        print(response.status_code)
    # while rate limited (429 error), generate a new response and sleep until un rate limited
    while response.status_code == 429:
        response = requests.get(url, headers=headers, params=querystring)
        print("rate limited")
        time.sleep(5)
    if response.status_code == 400:
        display_error("400", "Bad request, tail number or dates could be invalid")
        exit()
    if response.status_code == 500 or response.status_code == 503:
        display_error("500 or 503", "Aero Data Box is down, try again later")
        exit()
    if response.status_code != 400 and response.status_code != 500 and response.status_code != 503 and response.status_code != 204 and response.status_code != 200:
        print("unknown error occurred")
        display_error("Unknown error", f"{response.status_code} error occurred")
        exit()
    if response.status_code != 204:  # a 204 code means no data for that day, so we ignore these calls
        respj = response.json()
        # we use this json response to extract the values we want
        departure_data = respj[0]['departure']
        arrival_data = respj[0]['arrival']
        if len(departure_data) != 0 and len(arrival_data) != 0:
            try:
                data = [departure_data['airport']['icao'],
                        departure_data['revisedTime']['utc'][:-1],
                        arrival_data['airport']['icao'],
                        respj[0]['lastUpdatedUtc'][:-1]]
                # key error for departure data
            except KeyError:
                try:
                    data = ["Unknown Airport",
                            "Unknown Time",
                            arrival_data['airport']['icao'],
                            respj[0]['lastUpdatedUtc'][:-1]]
                    # key error for arrival data
                except KeyError:
                    try:
                        data = [departure_data['airport']['icao'],
                                departure_data['revisedTime']['utc'][:-1],
                                "Unknown Airport",
                                "Unknown Time"]
                        # key error for both
                    except KeyError:
                        data = ["Unknown Airport",
                                "Unknown Time",
                                "Unknown Airport",
                                "Unknown Time"]
    if len(data) != 0:
        return data


# use the open sky network api to get flight data
def get_plane_data_OSN(icao_num, date1_unix, date2_unix, load_bar):
    """
    Retrieves flight data using the Open Sky Network API.

    Args:
        icao_num (str): Aircraft ICAO code.
        date1_unix (int): Start date in Unix time.
        date2_unix (int): End date in Unix time.
        load_bar (tkinter obj) : The loading bar pop up

    Returns:
        list: A list containing flight data.
    """
    api = OpenSkyApi()
    flight_data = []
    iterations = get_month_iterations(date1_unix, date2_unix)
    for start_date, end_date in iterations:
        try:
            month_data = api.get_flights_by_aircraft(icao_num, start_date, end_date) # gets a month of flight data
            if month_data is not None:
                for data in month_data:
                    data_to_append = []
                    if data.estDepartureAirport is not None and data.estArrivalAirport is not None:
                        data_to_append = [data.estDepartureAirport, convert_unix_to_regular(data.firstSeen),
                                          data.estArrivalAirport,
                                          convert_unix_to_regular(data.lastSeen)]
                    else:
                        if data.estArrivalAirport is None and data.estDepartureAirport is not None:
                            data_to_append = [data.estDepartureAirport, convert_unix_to_regular(data.firstSeen),
                                              "Airport Undetected", convert_unix_to_regular(data.lastSeen)]
                        if data.estArrivalAirport is not None and data.estDepartureAirport is None:
                            data_to_append = [data.estDepartureAirport, convert_unix_to_regular(data.firstSeen),
                                              "Airport Undetected", convert_unix_to_regular(data.lastSeen)]
                        if data.estArrivalAirport is None and data.estDepartureAirport is None:
                            data_to_append = ["Airport Undetected", convert_unix_to_regular(data.firstSeen),
                                              "Airport Undetected", convert_unix_to_regular(data.lastSeen)]
                    flight_data.append(data_to_append)
            load_bar.update_progress(end_date)  # end_date is already in unix time
        except TimeoutError:
            display_error("Timeout Error", "Website timeout\nTry again in a few minutes")
        except Exception as e:
            display_error(f"Error {e}", f"Error {e}, probably a server error, try again later")

    return flight_data


def get_month_iterations(start_unix_time, end_unix_time):
    """
    Gets start and end date iterations for a month in Unix time.

    Args:
        start_unix_time (int): Start date in Unix time.
        end_unix_time (int): End date in Unix time.

    Returns:
        list: A list containing tuples of start and end dates.
    """
    iterations = []
    current_unix_time = start_unix_time

    while current_unix_time < end_unix_time:
        next_unix_time = current_unix_time + month_in_unix

        if next_unix_time > end_unix_time:
            next_unix_time = end_unix_time

        iterations.append((current_unix_time, next_unix_time))
        current_unix_time = next_unix_time

    return iterations


def is_2d_list(lst):
    """
    Checks if a list is 2d. This is needed since OSN data is pulled by the month,
    thus creating a 2d list. ADB is pulled by the day so it's a 1d list

    Args:
        id (str): Aircraft identifier.
        date1 (str): Start date in the format "%Y-%m-%d".
        date2 (str): End date in the format "%Y-%m-%d".
        data (list): List of flight data.

    Returns:
        boolean
    """
    if isinstance(lst, list) and lst:
        return all(isinstance(sublist, list) for sublist in lst)
    return False


def create_csv(id, date1, date2, data):
    """
    Creates a CSV file containing flight data for a given aircraft and date range.

    Args:
        id (str): Aircraft identifier.
        date1 (str): Start date in the format "%Y-%m-%d".
        date2 (str): End date in the format "%Y-%m-%d".
        data (list): List of flight data.

    Returns:
        None

    Note:
        The CSV file is saved with the format "{tail number}_flight_data_{date1}_to_{date2}.csv" in the current directory.
    """
    airports = airportsdata.load()
    # Determine the user's downloads folder
    downloads_folder = Path.home() / "Downloads"

    # Create the downloads folder if it doesn't exist
    downloads_folder.mkdir(parents=True, exist_ok=True)

    filename = f"{id}_flight_data_{date1}_to_{date2}.csv"

    # Build the local file path
    local_filepath = downloads_folder / filename

    with open(local_filepath, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Departure Airport", "Departure City", "Departure Subdivision", "Departure Time (UTC)",
                             "Arrival Airport", "Arrival City", "Arrival Subdivision",
                             "Arrival Time (UTC)"])  # create header
        for flight_data_list in data:
            if not is_2d_list(flight_data_list):
                flight_data = flight_data_list
                try:
                    # the data collected for each airport is the icao code for it
                    # we use this airports dataset to turn these codes into airport names
                    # for airports that cant be converted, we use their icao code instead
                    csv_writer.writerow(
                        [airports[flight_data[0]]['name'], airports[flight_data[0]]['city'],
                         airports[flight_data[0]]['subd'], flight_data[1],
                         airports[flight_data[2]]['name'], airports[flight_data[2]]['city'],
                         airports[flight_data[2]]['subd'], flight_data[3]])
                except KeyError:
                    try:
                        # if arrival airport is unidentified by dataset
                        csv_writer.writerow(
                            [airports[flight_data[0]]['name'], airports[flight_data[0]]['city'],
                             airports[flight_data[0]]['subd'], flight_data[1],
                             flight_data[2], "N/A", "N/A", flight_data[3]])
                    except KeyError:
                        # if departure airport is unidentified by dataset
                        try:
                            csv_writer.writerow(
                                [flight_data[0], "N/A", "N/A", flight_data[1],
                                 airports[flight_data[2]]['name'], airports[flight_data[2]]['city'],
                                 airports[flight_data[2]]['subd'], flight_data[3]])
                        except KeyError:
                            # if both airports are unidentified by dataset
                            csv_writer.writerow([flight_data[0], "N/A", "N/A", flight_data[1],
                                                 flight_data[2], "N/A", "N/A", flight_data[3]])
                except IndexError as e:
                    print(e)
                    print(flight_data)
                    continue
            else:
                # for osn data
                for flight_data in flight_data_list:
                    if flight_data is not None:
                        try:
                            # the data collected for each airport is the icao code for it
                            # we use this airports dataset to turn these codes into airport names
                            # for airports that cant be converted, we use their icao code instead
                            csv_writer.writerow(
                                [airports[flight_data[0]]['name'], airports[flight_data[0]]['city'],
                                 airports[flight_data[0]]['subd'], flight_data[1],
                                 airports[flight_data[2]]['name'], airports[flight_data[2]]['city'],
                                 airports[flight_data[2]]['subd'], flight_data[3]])
                        except KeyError:
                            try:
                                # if arrival airport is unidentified by dataset
                                csv_writer.writerow(
                                    [airports[flight_data[0]]['name'], airports[flight_data[0]]['city'],
                                     airports[flight_data[0]]['subd'], flight_data[1],
                                     flight_data[2], "N/A", "N/A", flight_data[3]])
                            except KeyError:
                                # if departure airport is unidentified by dataset
                                try:
                                    csv_writer.writerow(
                                        [flight_data[0], "N/A", "N/A", flight_data[1],
                                         airports[flight_data[2]]['name'], airports[flight_data[2]]['city'],
                                         airports[flight_data[2]]['subd'], flight_data[3]])
                                except KeyError:
                                    # if both airports are unidentified by dataset
                                    csv_writer.writerow([flight_data[0], "N/A", "N/A", flight_data[1],
                                                         flight_data[2], "N/A", "N/A", flight_data[3]])
                        except IndexError as e:
                            print(e)
                            print(flight_data)
                            continue


def validate_dates(dates):
    """
    Validate the users selected date range

    Args:
        dates (Tuple): Tuple of user dates

    Returns:
        None, exits and throws error on invalid date
    """
    # if start date is greater than end date, throw error
    if convert_to_unix_time(dates[0]) > convert_to_unix_time(dates[1]):
        display_error("Invalid Date", "Invalid Date: Enter new dates and try again")
        exit()
    # if either date is higher than the current day
    if convert_to_unix_time(dates[0]) > convert_to_unix_time(str(datetime.now().date())) or \
            convert_to_unix_time(dates[1]) > convert_to_unix_time(str(datetime.now().date())):
        display_error("Invalid Date", "Invalid Date: Enter new dates and try again")
        exit()


def main():
    try:
        dialog = DateEntryDialog(root, "Flight Tracker Client")
        user_input = dialog.user_input
        dates = (dialog.date1, dialog.date2)
        validate_dates(dates)
        loading_popup = LoadingBarPopup(root, convert_to_unix_time(dates[0]), convert_to_unix_time(dates[1]))
        root.update_idletasks()
        data = get_plane_data(user_input, dates[0], dates[1], loading_popup)
        create_csv(user_input, dates[0], dates[1], data)
        if user_input is not None:
            display_result(user_input, dates)
        root.destroy()
    except Exception as e:
        display_error(f"{e}", f"{e}")
        print(e)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # hide window until complete

    main()
