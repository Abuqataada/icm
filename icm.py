import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import requests
import socket
import app
import threading


# Global variable to store the Flask process
flask_process = None


def get_local_ip():
    """Retrieve the local IP address of the machine."""
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except Exception as e:
        return "Unable to retrieve IP"


def run_flask():
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
                messagebox.showwarning("Warning", line.decode('utf-8'), end="")  # Print stdout to console (or log it)

            for line in flask_process.stderr:
                messagebox.showwarning("Warning", line.decode('utf-8'), end="")  # Print stderr to console (or log it)

        # Run output reading in a separate thread to avoid blocking the GUI
        output_thread = threading.Thread(target=read_output)
        output_thread.daemon = True
        output_thread.start()

        messagebox.showinfo("Success", "ICM CLICKATHON server is running!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start server: {str(e)}")


def stop_flask():
    global flask_process
    if not flask_process or flask_process.poll() is not None:
        messagebox.showwarning("Warning", "The server is not running!")
        return

    try:
        # Send a POST request to the shutdown route
        response = requests.post("http://127.0.0.1:5000/shutdown")
        response.raise_for_status()  # Raise an error for bad responses

        # Terminate the Flask process
        flask_process.terminate()
        flask_process.wait()
        flask_process = None
        messagebox.showinfo("Stopped", "ICM CLICKATHON server has been stopped.")
    except requests.ConnectionError:
        messagebox.showerror(
            "Error", "Unable to connect to the server. It may already be stopped."
        )
    except requests.Timeout:
        messagebox.showerror("Error", "Request timed out while trying to stop the server.")
    except requests.HTTPError as http_err:
        messagebox.showerror("Error", f"HTTP error occurred: {http_err}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")


def exit_app():
    """Exit the application."""
    if flask_process:
        stop_flask()  # Ensure the Flask server is stopped before exiting
    root.destroy()  # Close the application window


# Create the main window
root = tk.Tk()
root.title("ICM CLICKATHON App Server")

# Set the window size
root.geometry("400x300")

# Create a style for ttk
style = ttk.Style()
style.configure("TLabel", padding=10)
style.configure("TButton", padding=10)

# Custom style for the exit button
style.configure(
    "Exit.TButton", background="red", foreground="black", font=("Arial", 10, "bold")
)
style.map(
    "Exit.TButton",
    background=[("active", "darkred")],  # Change to dark red when active
    foreground=[("active", "red")],  # Change text color when active
)

# Display the local IP address
ip_address = get_local_ip()
ip_label = ttk.Label(root, text=f"Server IP: {ip_address}")
ip_label.pack(pady=5)

# Display the URL with the local IP address
url_label = ttk.Label(root, text=f"Connect to: http://{ip_address}:5000")
url_label.pack(pady=5)

# Create buttons to run and stop the Flask app
run_button = ttk.Button(root, text="Run App Server", command=run_flask)
run_button.pack(pady=10)

stop_button = ttk.Button(root, text="Stop Server", command=stop_flask)
stop_button.pack(pady=10)

# Create an exit button with custom style
exit_button = ttk.Button(root, text="Exit", command=exit_app, style="Exit.TButton")
exit_button.pack(side=tk.RIGHT, padx=10, pady=10)

# Start the GUI event loop
root.mainloop()
