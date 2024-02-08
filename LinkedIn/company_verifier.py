import tkinter as tk
from tkinter import messagebox
import time


class CompanyVerifierGUI:
    def __init__(self, master, object_list):
        self.master = tk.Toplevel()
        self.master.title("Company Verification")

        self.object_list = object_list
        self.selected_object = None
        self.selection_made = False

        self.create_widgets()

    def create_widgets(self):
        # Display the objects and create buttons for each
        for obj in self.object_list:
            print(obj)
            company_text = str(obj['name']) + ": " + str(obj['headline'])  # expects the api companies result
            button = tk.Button(self.master, text=company_text,
                               command=lambda o=obj: self.on_selection(o))
            button.pack(pady=5)

        # Button for indicating none of them are correct
        none_button = tk.Button(self.master, text="None are correct",
                                command=lambda: self.on_selection(None))
        none_button.pack(pady=10)

    def on_selection(self, company):
        self.selected_object = company
        self.selection_made = True
        self.master.destroy()
        self.master.update()

    def get_selected_object(self):
        return self.selected_object


if __name__ == "__main__":
    # Example list of objects
    objects = ["Object 1", "Object 2", "Object 3"]

    # Create Tkinter window
    root = tk.Tk()

    # Initialize the GUI with the list of objects
    gui = CompanyVerifierGUI(root, objects)

    # Run the Tkinter event loop
    root.mainloop()
