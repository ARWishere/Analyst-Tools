"""
LinkedIn Scraper - GUI Application

This program is a simple GUI application for scraping employee data from LinkedIn using the unofficial LinkedIn API.
It utilizes the `linkedin_api` library for authentication and data retrieval.

Created by Andrew Welling, docstrings provided by ChatGPT. fetch_employees and get_employees referenced from Tom Quirk's github

"""
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from linkedin_api import Linkedin
import os
import requests
import json
import time
import csv
from pathlib import Path
import sys

from company_verifier import CompanyVerifierGUI
from advanced_options import AdvancedSettings

# Global variables
clicks = 0
status = "Not started"
location = ""
window = tk.Tk()
status_lbl = None
company_entry = None
company_name = ""
location_lbl = None
total = 0
progress_var = tk.IntVar()
start_val = 0
end_val = sys.maxsize
# user must input their own username and password here
username = ''
password = ''


def auth():
    """
    Authenticate and set up the LinkedIn API.

    This function authenticates the program with the LinkedIn API using user credentials and initializes the API object.
    It also retrieves the user's LinkedIn profile to verify successful authentication.

    """
    global status, api
    print("Setting up")
    updateStatus("Authenticating and securing API access...")
    try:
        print("Auth")
        # Add your authentication logic here
        api = Linkedin(username, password)
        profile = api.get_profile('andrew-welling')
        retrieve_data()
    except Exception as error:
        print(error)
        status = f"Error: {type(error).__name__}"
        updateStatus(status)
        create_crash_log(error, "auth()")
        reset_clicks()


# the below methods are for retrieving necessary data from linkedin

# this method fetches the employee data from linkedin via requests in the form of a json file
# it uses 2 requests for every 10 users scraped
def fetch_employees(company_id, offset=0):
    """
    Fetch employee data from LinkedIn using the unofficial API.

    This function fetches employee data from LinkedIn using GraphQL requests and stores the data in a cache file.
    It uses two requests for every 10 users scraped.

    Parameters:
        company_id (str): The LinkedIn company ID.
        offset (int): The offset for paginating through employee data.

    Returns:
        dict: The JSON response containing employee data.

    """
    cache = f"LI_Scraper_companies/{company_id}/employees_{offset}.json"
    if os.path.exists(cache):
        r = json.loads(open(cache).read())
        print(f"[get_employees()]: OK! Using cached file \"{cache}\".")

    else:
        uri = f"/graphql?includeWebMetadata=true&variables=(start:{offset},origin:COMPANY_PAGE_CANNED_SEARCH,query:(flagshipSearchIntent:SEARCH_SRP,queryParameters:List((key:currentCompany,value:List({company_id})),(key:resultType,value:List(PEOPLE))),includeFiltersInResponse:false))&&queryId=voyagerSearchDashClusters.b0928897b71bd00a5a7291755dcd64f0"
        r = api._fetch(uri)

        if not r.ok:
            updateStatus(f"Error with LinkedIn api {r.status_code} ({r.reason}")
            print(f"Error with LinkedIn api {r.status_code} ({r.reason}")
            reset_clicks()
            return

        print(f"[fetch_employees()]: OK! LinkedIn returned status code {r.status_code} ({r.reason})")
        r = r.json()

        # Cache request
        os.makedirs(f"LI_Scraper_companies/{company_id}", exist_ok=True)
        with open(cache, "w") as f:
            json.dump(r, f)

        if not r["data"]["searchDashClustersByAll"]:
            updateStatus(f"Error with LinkedIn API " + r["errors"][0]["message"])
            print(f"Bad json. LinkedIn returned error:", r["errors"][0]["message"])
            os.remove(cache)
            reset_clicks()
            return

    return r["data"]["searchDashClustersByAll"]


# get the necessary employee data from the above json file and method
def get_employees(company_id, offset=0):
    global total, end_val
    """
    Retrieve necessary employee data from LinkedIn.

    This function retrieves necessary employee data from the JSON response obtained through the LinkedIn API.

    Parameters:
        company_id (str): The LinkedIn company ID.
        offset (int): The offset for paginating through employee data.

    Returns:
        list: List of dictionaries containing employee data.

    """

    def get_item_key(item, keys):
        if type(keys) == str:
            keys = [keys]

        cur = item
        for key in keys:
            if cur and key in cur.keys():
                cur = cur[key]
            else:
                return ""

        return cur

    j = fetch_employees(company_id, offset=offset)

    total = j["metadata"]["totalResultCount"]
    if end_val == 0:  # this is for if the user didnt specify an end val in advanced settings
        print("total emp: ", total)
        end_val = total

    if not j:
        return []

    if not j["_type"] == "com.linkedin.restli.common.CollectionResponse":
        return []

    employees = []
    for it in j["elements"]:
        if not it["_type"] == "com.linkedin.voyager.dash.search.SearchClusterViewModel":
            continue

        for it in it["items"]:
            if not it["_type"] == "com.linkedin.voyager.dash.search.SearchItem":
                continue

            e = it["item"]["entityResult"]
            if not e or not e["_type"] == "com.linkedin.voyager.dash.search.EntityResultViewModel":
                continue

            try:
                # print("\nEmployee:")
                # print("    ", get_item_key(e, ["title", "text"]))
                # print("    ", get_item_key(e, "entityUrn"))
                # print("    ", get_item_key(e, ["primarySubtitle", "text"]))
                # print("    ", get_item_key(e, ["secondarySubtitle", "text"]))

                employees.append({
                    "title": get_item_key(e, ["title", "text"]),
                    "entityUrn": get_item_key(e, "entityUrn"),
                    "primarySubtitle": get_item_key(e, ["primarySubtitle", "text"]),
                    "secondarySubtitle": get_item_key(e, ["secondarySubtitle", "text"]),
                })
            except Exception as e:
                print(f"Error {e} when processing employees with id {company_id}")
                updateStatus(f"Error {e} when processing employees with id {company_id}")
                create_crash_log(e, "get_employees()")
                reset_clicks()
                exit(1)

    return employees


# retrieves the company's urn id from a company name
def get_company_id_from_name(companyName):
    """
    Get the LinkedIn company ID from a company name.

    This function searches for companies on LinkedIn based on a provided name and verifies the correct company using a GUI.

    Parameters:
        company_name (str): The name of the company to search for.

    Returns:
        str: The LinkedIn company ID.

    """
    global company_name
    companies = api.search_companies(keywords=companyName, limit=5)
    # verify company with gui below
    companyObj = verify_company_gui(companies)
    company_name = companyObj['name']
    print(company_name)
    print(companyObj)
    return companyObj['urn_id']


# currently trying to fix errors with pop up window not closing
def verify_company_gui(companies):
    """
    Verify the correct company using a GUI.

    This function creates a pop-up GUI window using the `CompanyVerifierGUI` class to allow the user to select the correct company.

    Parameters:
        companies (list): List of company objects.

    Returns:
        dict: The selected company object.

    """
    verify_obj = CompanyVerifierGUI(window, companies)

    # wait for the Toplevel window to be destroyed
    window.wait_window(verify_obj.master)

    selected_company = verify_obj.get_selected_object()
    print(selected_company)

    if selected_company is None:
        print(selected_company)
        updateStatus("Restart")
        reset_clicks()
    else:
        return selected_company

def read_csv(file_path):
    data_list = []
    with open(file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            # Assuming each row has only one element
            data_list.append(row[0])
    return data_list

def categorize_job(Li_job, job_list):
    # TODO: make it so they must share the first letter of the word before starting count
    """
    Categorizes a LinkedIn job headline based on a very large list of predefined job roles.

    Parameters:
    - LI_job (str): LinkedIn job headline to be categorized.
    - job_list (list): List of jobs from a dataset used for comparison.

    Returns:
    - tuple str: The categorized jobs with the 2 highest scores based on matching words,
           or "Role undetected" if no matching category is found.
    """
    try:
        # first remove company name from Li_job
        if company_name.lower() in Li_job:
            Li_job = Li_job.replace(company_name.lower(), '')

        possible_jobs = {}
        for job in job_list:
            if job in Li_job:
                # put job into dictionary to count char similarity scores
                possible_jobs.update({job: 0})

        # create a new dictionary to store non-substring values
        filtered_jobs = {}

        # iterate through the original dictionary, remove substring vals
        for job_1 in possible_jobs:
            is_substring = False
            for job_2 in possible_jobs:
                if job_1 != job_2 and job_1 in job_2:
                    is_substring = True
                    break

            # if job_1 is not a substring of any other job, add it to the filtered dictionary
            if not is_substring:
                filtered_jobs[job_1] = possible_jobs[job_1]

        possible_jobs = filtered_jobs

        # check char similarity and get two highest
        print(possible_jobs)
        if len(possible_jobs) != 0:
            for job in possible_jobs:
                for char in job:
                    if char in Li_job:
                        possible_jobs[job] += 1
            possible_jobs = sorted(possible_jobs, key=possible_jobs.get, reverse=True)
            if len(possible_jobs) > 1:
                return possible_jobs[0], possible_jobs[1]
            else:
                return possible_jobs[0], ""
        else:
            return "Role undetected", ""
    except Exception as e:
        print(e)
        print(Li_job)


def retrieve_data():
    """
    Retrieve data from LinkedIn and store it in a CSV file.

    This function retrieves employee data from LinkedIn and stores it in a CSV file.
    It initiates the data retrieval process and calls the `finish_up` function upon completion.

    """
    global status, status_lbl
    print("Retrieving data")
    # print("Company:", company)
    # print("file loc:", location)
    updateStatus("Obtaining data, may take a while")
    try:
        # print("Scraping...")
        # scraping and searching here
        i = (start_val // 10) * 10  # use floor division to make the start val a multiple of 10
        print(i)
        print(end_val)
        employee_lists = []
        employees = [1]  # initialized with a value so while loop can run
        # print(len(employees))
        id = get_company_id_from_name(companyName=company)
        print(id)
        while (len(employees) != 0) and ((i + 10) <= end_val):
            # offset is always multiples of 10, as one call scrapes 10 employees
            # print(id)
            employees = get_employees(id, offset=i)
            employee_lists.append(employees)
            i += 10
            # update progress of prog bar
            update_progress_bar(i)
            print(i)
            print(end_val)
            time.sleep(.1)  # sleep needed to prevent rate limiting, might eliminate since taking requests takes awhile
        # print(len(employee_lists))
        finish_up(employee_lists)
    except Exception as error:
        print(error)
        updateStatus(f"Error: {type(error).__name__}")
        create_crash_log(error, "retrieve_data()")
        reset_clicks()


# update status and download the file
def finish_up(employee_lists):
    """
    Finalize the data retrieval process and store employee data in a CSV file.

    This function receives a 2D list of employees for a company, and stores the data in a CSV file.
    The CSV file is named '{company}_linkedin_data.csv' and includes headers for "Name," "Role," and "Location."

    Parameters:
        employee_lists (list): A 2D list containing employee data for a company.

    """
    # employee lists is a 2d list of employees for a company
    global location
    updateStatus("Storing data to file")
    try:
        # download file here
        location += f"{company}_linkedin_data.csv".replace(" ", "_")
        directory = os.path.dirname(location)

        # Create the directory if it does not exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        # location error?
        with open(location, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Name", "Headline", "Job Title", "Job Title", "Location"])  # create header
            for emp_list in employee_lists:
                for emp in emp_list:
                    jobs_cat = categorize_job(emp['primarySubtitle'].lower(), read_csv('jobs.csv'))
                    csv_writer.writerow([emp['title'], emp['primarySubtitle'], jobs_cat[0], jobs_cat[1], emp['secondarySubtitle']])

        updateStatus("Download Successful!")
        reset_clicks()
    except Exception as e:
        print(e)
        updateStatus(f"Error: {type(e).__name__}")
        create_crash_log(e, "finish_up()")
        reset_clicks()


# all GUI creation methods are below this
def handle_file_button():
    """
    Handle the 'Select Location' button click.

    This function opens a file dialog to allow the user to select a directory for downloading the CSV file.

    """
    global location
    location = filedialog.askdirectory(initialdir="/", title="Select Directory")
    location_lbl.config(text=location)


def handle_click():
    """
    Handle the 'Run' button click.

    This function is called when the 'Run' button is clicked. It initiates the data retrieval process by calling the 'auth' function.

    """
    global clicks, company_entry, company, progress_var
    # print(clicks)
    company = company_entry.get()
    if clicks == 0:
        updateStatus("Starting...")
        progress_var.set(0)
        auth()
        clicks += 1


def create_gui():
    """
    Create the main GUI for the LinkedIn Scraper.

    This function creates the main graphical user interface (GUI) for the LinkedIn Scraper application.
    It includes fields for entering the company name, selecting the download location, and buttons for running the scraper.

    """
    global window, location, status_lbl, company_entry, location_lbl, progress, progress_var

    # Create the GUI
    window.geometry("300x250")
    window.title("LinkedIn Scraper")

    # Create field to enter company names
    tk.Label(master=window, text="Company Name").pack()
    company_entry = tk.Entry(master=window)
    company_entry.pack()

    # Create fields to get file location to download file
    tk.Label(master=window, text="Select Directory to Download File").pack()
    file_button = tk.Button(master=window, text="Select location", fg="black", bg="white", command=handle_file_button)
    file_button.pack()

    # Display file location below button
    location_lbl = tk.Label(master=window, text=location)
    location_lbl.pack()

    # Create the run button at the bottom
    button_text = "Run"
    button = tk.Button(master=window, text=button_text, width=10, height=2, bg="white", fg="black",
                       command=handle_click)
    button.pack()

    # Create adv options button
    adv_button = tk.Button(master=window, text="Advanced Options", width=14, height=1, bg="white", fg="black",
                           command=open_advanced_options)
    adv_button.pack()

    # Create the status text at the bottom
    status_lbl = tk.Label(text=status)
    status_lbl.pack()

    # Create progress bar at bottom
    progress = ttk.Progressbar(window, length=200, mode='determinate', variable=progress_var)
    progress.pack()


def open_advanced_options():
    global start_val, end_val, username, password
    """
    Advanced settings for advanced user

    This function creates a pop-up GUI window using the `advanced_options` class to allow the user to customize their scraping

    """
    settings_obj = AdvancedSettings(window)

    # wait for the Toplevel window to be destroyed
    window.wait_window(settings_obj.master)

    if settings_obj.username != "":
        print("upd us")
        username = settings_obj.username
    if settings_obj.password != "":
        print("upd ps")
        password = settings_obj.password
    if settings_obj.start != 0:  # NOTE START SHOULD START AT 0 NOT 1
        start_val = int(settings_obj.start)
        print("updates st to " + str(start_val))
    if settings_obj.end != 0:
        print("upd end")
        end_val = ((int(settings_obj.end) // 10) + 1) * 10  # turns end val into a multiple of 10 just in case
        print("updates end to " + str(end_val))


def updateStatus(newStatus):
    """
    Update the current status text in the GUI.

    This function updates the status label in the GUI with a new status message.

    Parameters:
        newStatus (str): The new status message.

    """
    global status_lbl
    status_lbl.config(text=newStatus)
    window.update()


def update_progress_bar(prog):
    global progress_var
    """
    Update the current progress in the progress bar in the GUI

    This function updates the progress bar in the GUI with a new value

    Parameters:
        prog (int): New progress value

    """
    # print(total)
    if prog > end_val:
        prog = end_val
    # print((prog / total) * 99.9)
    progress_var.set(((prog - start_val) / (end_val - start_val)) * 99.9)
    progress.update()


def reset_clicks():
    """
    Reset the click counter to allow running the scraper again.

    This function resets the global click counter to -1, enabling the 'Run' button to be clicked again.

    """
    global clicks
    clicks = -1
    # print(clicks)



def create_crashes_folder():
    # Create 'crashes' folder if it doesn't exist
    documents_folder = Path.home() / "Documents"
    crashes_folder = documents_folder / "crashes"
    crashes_folder.mkdir(exist_ok=True)

def create_crash_log(error, funcName):
    documents_folder = Path.home() / "Documents"
    crashes_folder = documents_folder / "crashes"

    create_crashes_folder()

    # Generate a unique filename using timestamp
    timestamp = str(int(time.time()))
    filename = f"crash_log_LI_Scraper_{timestamp}.txt"

    filepath = crashes_folder / filename

    with open(filepath, 'w') as file:
        file.write(str(error) + " at method " + funcName)

    print(f"File '{filename}' saved in 'crashes' folder.")


# Call the GUI creation function
create_gui()

# Start the main loop
window.mainloop()
