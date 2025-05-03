import subprocess
from tkinter import messagebox
import requests
import socket
import app
import threading
import customtkinter as ctk
import os
import json
from models import db, School, Group, User


# Global variable to store the Flask process
flask_process = None

def load_txt_and_sync_to_sqlite(file_path="db_dumps/remote_dump.txt"):
    if not os.path.exists(file_path):
        print("Dump file not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Make sure tables are created
    db.create_all()

    # Sync schools
    for s in data.get("schools", []):
        if not School.query.filter_by(id=s['id']).first():
            db.session.add(School(id=s['id'], name=s['name'], season=s['season']))

    # Sync groups
    for g in data.get("groups", []):
        if not Group.query.filter_by(id=g['id']).first():
            db.session.add(Group(
                id=g['id'], name=g['name'], passcode=g['passcode'],
                is_admin=g['is_admin'], school_id=g['school_id']
            ))

    # Sync users
    for u in data.get("users", []):
        if not User.query.filter_by(id=u['id']).first():
            db.session.add(User(
                id=u['id'], fullname=u['fullname'],
                school_id=u['school_id'], group_id=u['group_id'],
                is_admin=False
            ))

    db.session.commit()
    print("Data synced to local DB.")


def get_local_ip():
    """Retrieve the local IP address of the machine."""
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except Exception as e:
        return "Unable to retrieve IP"


def run_flask():
    load_txt_and_sync_to_sqlite()
    global flask_process
    if flask_process and flask_process.poll() is None:
        messagebox.showwarning("Warning", "The server is already running!")
        return

    try:
        # Start the Flask application
        flask_process = subprocess.Popen(
            ["python", "app.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Optionally read stdout and stderr for debugging
        def read_output():
            for line in flask_process.stdout:
                messagebox.showwarning("Warning", line.decode('utf-8'))

            for line in flask_process.stderr:
                messagebox.showwarning("Warning", line.decode('utf-8'))

        # Run output reading in a separate thread to avoid blocking the GUI
        output_thread = threading.Thread(target=read_output)
        output_thread.daemon = True
        output_thread.start()

        messagebox.showinfo("Success", "ICM CLICKATHON server is running!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start server: {str(e)}")


def stop_flask(ip_address):
    global flask_process
    if not flask_process or flask_process.poll() is not None:
        messagebox.showwarning("Warning", "The server is not running!")
        return

    try:
        # Send a POST request to the shutdown route
        response = requests.post("http://{ip_address}:5000/shutdown")
        response.raise_for_status()  # Raise an error for bad responses

        # Terminate the Flask process
        flask_process.terminate()
        flask_process.wait()
        flask_process = None
        messagebox.showinfo("Stopped", "ICM CLICKATHON server has been stopped.")
    except requests.ConnectionError:
        flask_process = None
        messagebox.showerror(
            "Error", "Unable to connect to the server. It may already be stopped."
        )
    except requests.Timeout:
        flask_process = None
        messagebox.showerror("Error", "Request timed out while trying to stop the server.")
    except requests.HTTPError as http_err:
        messagebox.showerror("Error", f"HTTP error occurred: {http_err}")
        flask_process = None
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")
        flask_process = None


def exit_app():
    """Exit the application."""
    if flask_process:
        stop_flask()  # Ensure the Flask server is stopped before exiting
    app.destroy()  # Close the application window


# Initialize CustomTkinter
ctk.set_appearance_mode("System")  # Modes: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (default), "dark-blue", "green"

# Create the main window
app = ctk.CTk()
app.title("ICM CLICKATHON App Server")
app.geometry("400x300")

# Display IP
ip_address = get_local_ip()
ip_label = ctk.CTkLabel(app, text=f"Server IP: {ip_address}", font=ctk.CTkFont(size=14))
ip_label.pack(pady=10)

url_label = ctk.CTkLabel(app, text=f"Connect to: http://{ip_address}:5000", font=ctk.CTkFont(size=14))
url_label.pack(pady=5)

# Buttons
run_button = ctk.CTkButton(app, text="Start ICM Server", command=run_flask)
run_button.pack(pady=10)

stop_button = ctk.CTkButton(app, text="Stop Server", command=lambda: stop_flask(ip_address))
stop_button.pack(pady=10)

exit_button = ctk.CTkButton(app, text="Exit", command=exit_app, fg_color="red", hover_color="darkred", text_color="white")
exit_button.pack(pady=20)

# Run the app
app.mainloop()
