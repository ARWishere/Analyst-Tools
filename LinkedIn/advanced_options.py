import tkinter as tk
from tkinter import messagebox
import time
import os
import shutil

class AdvancedSettings:
    def __init__(self, root):
        self.master = tk.Toplevel(root)
        self.master.title("Advanced Options")

        self.username = ""
        self.password = ""
        # add note to make sure start and end are in employee range
        self.start = 0
        self.end = 0

        self.create_widgets()

    def create_widgets(self):
        # Username and Password Entry
        self.username_label = tk.Label(self.master, text="Email:")
        self.username_label.grid(row=0, column=0, padx=10, pady=5, sticky=tk.E)
        self.username_entry = tk.Entry(self.master)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5, columnspan=2)

        self.password_label = tk.Label(self.master, text="Password:")
        self.password_label.grid(row=1, column=0, padx=10, pady=5, sticky=tk.E)
        self.password_entry = tk.Entry(self.master, show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=5, columnspan=2)

        # Start and End Value Entry
        self.start_label = tk.Label(self.master, text="Scrape From (int): ")
        self.start_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
        self.start_entry = tk.Entry(self.master, width=5)
        self.start_entry.grid(row=2, column=1, padx=5, pady=5)

        self.end_label = tk.Label(self.master, text="Scrape To (int): ")
        self.end_label.grid(row=2, column=2, padx=5, pady=5, sticky=tk.E)
        self.end_entry = tk.Entry(self.master, width=5)
        self.end_entry.grid(row=2, column=3, padx=5, pady=5)

        # Clear Cache Button
        self.clear_cache_button = tk.Button(self.master, text="Clear Cache", command=self.clear_cache)
        self.clear_cache_button.grid(row=3, column=1, columnspan=2, pady=10)

        # Save button
        self.clear_cache_button = tk.Button(self.master, text="Save and Exit", command=self.on_save)
        self.clear_cache_button.grid(row=4, column=1, columnspan=2, pady=10)

    def clear_cache(self):
        cache_folder_path = "LI_Scraper_companies"

        try:
            # Check if the folder exists before attempting to delete
            if os.path.exists(cache_folder_path):
                shutil.rmtree(cache_folder_path)
                messagebox.showinfo("Cache Deleted", f"The cache has been deleted successfully!")
            else:
                messagebox.showinfo("Cache Empty", f"The cache is already empty")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def on_save(self):
        self.username = self.username_entry.get()
        self.password = self.password_entry.get()
        self.start = self.start_entry.get()
        self.end = self.end_entry.get()

        # check if start and end value are integers, or add custom codes, ie: half, quarter?

        self.master.destroy()
        self.master.update()
        messagebox.showinfo("Saved", "Information saved for this run")



if __name__ == "__main__":

    # Create Tkinter window
    root = tk.Tk()

    # Initialize the GUI with the list of objects
    gui = AdvancedSettings(root)

    # Run the Tkinter event loop
    root.mainloop()
