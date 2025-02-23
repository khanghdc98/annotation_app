import os
import json
import shutil
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, Canvas, Frame, Scrollbar, Entry, Label
from PIL import Image, ImageTk
from rest_client import RestClient
from utils import get_path_for_vector_db, get_base_path
from constant import image_list, current_index, image_dir, output_dir, output_csv, label_data, csv_columns, annotated_images, total_images, base_path, have_base_path, label_file
from appUI import show_propagated_records_dialog, show_image, refresh_label_buttons, on_mouse_scroll


api_client = RestClient("http://34.97.0.203:8001")

# Load labels from JSON file
def load_labels():
    global label_data
    json_file = filedialog.askopenfilename(title="Select Labels JSON", filetypes=[("JSON Files", "*.json")])
    if json_file:
        with open(json_file, "r") as f:
            label_data = sorted(json.load(f))  # Sort labels alphabetically
        refresh_label_buttons(label_data, label_inner_frame, label_canvas, save_annotation)

# Load images from directory (only those not in CSV)
def load_images():
    global image_list, image_dir, current_index, annotated_images, total_images
    image_dir = filedialog.askdirectory(title="Select Image Directory")
    
    if not image_dir:
        return

    # Read the existing CSV file and track labeled images
    annotated_images = set()
    if os.path.exists(output_csv):
        try:
            df = pd.read_csv(output_csv)
            annotated_images = set(df["image_filename"].tolist())  # Ensure column name matches CSV
        except Exception as e:
            messagebox.showerror("Error", f"Could not read CSV file: {e}")

    # Get all images (absolute paths) and filter out already annotated ones
    all_images = [
        os.path.join(image_dir, f) for f in os.listdir(image_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    total_images = len(all_images)
    print(f"Total images: {total_images}")

    # Ensure we only load new images
    image_list = [img for img in all_images if get_path_for_vector_db(img) not in annotated_images]
    print(f"New images to label: {len(image_list)}")

    if not image_list:
        messagebox.showinfo("Info", "No new images to label.")
        return

    global have_base_path
    if not have_base_path:
        global base_path 
        base_path = get_base_path(image_list[0])
        have_base_path = True
        print("Base path: ", base_path)

    current_index = 0
    update_progress_label()  # Update progress count
    global img_label, filename_label
    img_label, filename_label = show_image(current_index, image_list, img_label, filename_label) or (img_label, filename_label)



# Select output directory
def select_output_folder():
    global output_dir
    output_dir = filedialog.askdirectory(title="Select Output Directory")
    if not output_dir:
        messagebox.showwarning("Warning", "No output directory selected!")

# Update progress label
def update_progress_label():
    progress_label.config(text=f"Progress: {len(annotated_images)}/{total_images}")

# Save annotation (copy image instead of moving)
def save_annotation(label):
    global current_index
    # if not image_list or not output_dir:
    #     messagebox.showwarning("Warning", "Please select an output directory first!")
    #     return

    image_name = image_list[current_index]
    image_name = get_path_for_vector_db(image_name) # Only for LSC dataset
    # label_folder = os.path.join(output_dir, label)

    # # Ensure label directory exists
    # os.makedirs(label_folder, exist_ok=True)

    # # Copy the image to the label directory
    # shutil.copy(os.path.join(image_dir, image_name), os.path.join(label_folder, image_name))

    # Propagate label by calling to server
    image_name_no_ext = str(os.path.splitext(image_name)[0])
    response = api_client.send_annotation(image_name_no_ext, no_return_records=3)
    
    # propagated_records = response.data if response else []
    propagated_records = ["202006/01/20200601_111322_000.jpg"]
    if not propagated_records:
        print("No propagated records received.")
    else:
        # Show dialog to allow user to modify the list
        show_propagated_records_dialog(root, propagated_records, label)

    # Append annotation to CSV
    df = pd.DataFrame([[image_name, label]], columns=csv_columns)
    if not os.path.exists(output_csv):
        df.to_csv(output_csv, index=False)
    else:
        df.to_csv(output_csv, mode="a", header=False, index=False)

    # Add image to annotated set and update progress
    annotated_images.add(image_name)
    update_progress_label()

    # Move to next image
    current_index += 1
    if current_index < len(image_list):
        global img_label, filename_label
        img_label, filename_label = show_image(current_index, image_list, img_label, filename_label) or (img_label, filename_label)
    else:
        messagebox.showinfo("Done", "All images labeled!")
        root.quit()

# Set custom CSV filename
def set_csv_filename():
    global output_csv
    filename = csv_entry.get().strip()
    if filename:
        if not filename.endswith(".csv"):
            filename += ".csv"
        output_csv = filename
        messagebox.showinfo("Success", f"Output CSV set to: {output_csv}")
    else:
        messagebox.showwarning("Warning", "Invalid CSV filename!")
import tkinter as tk
from tkinter import messagebox, Canvas, Scrollbar
from PIL import Image, ImageTk
import os
import pandas as pd


# Tkinter GUI Setup
root = tk.Tk()
root.title("Image Annotation Tool")
root.attributes('-fullscreen', True)  # Full-screen mode

# Top Menu Buttons
top_frame = tk.Frame(root)
top_frame.pack(fill="x", pady=10)

tk.Button(top_frame, text="Load Labels", font=("Arial", 12), command=load_labels).pack(side="left", padx=10)
tk.Button(top_frame, text="Load Images", font=("Arial", 12), command=load_images).pack(side="left", padx=10)
tk.Button(top_frame, text="Set Output Folder", font=("Arial", 12), command=select_output_folder).pack(side="left", padx=10)
tk.Button(top_frame, text="Exit", font=("Arial", 12), command=root.quit, fg="white", bg="red").pack(side="right", padx=10)

# CSV Filename Entry
csv_frame = tk.Frame(root)
csv_frame.pack(fill="x", padx=10, pady=5)

Label(csv_frame, text="Output CSV:", font=("Arial", 12)).pack(side="left", padx=5)
csv_entry = Entry(csv_frame, font=("Arial", 12), width=30)
csv_entry.pack(side="left", padx=5)
tk.Button(csv_frame, text="Set", font=("Arial", 12), command=set_csv_filename).pack(side="left", padx=5)

# Image Display Area (Smaller Height)
img_frame = tk.Frame(root, bd=2, relief="solid", height=300)
img_frame.pack(fill="both", expand=True, padx=20, pady=10)

img_label = tk.Label(img_frame, bg="black")  # Black background for contrast
img_label.pack(expand=True)

filename_label = tk.Label(root, text="", font=("Arial", 14))
filename_label.pack(pady=5)

# Progress Label
progress_label = tk.Label(root, text="Progress: 0/0", font=("Arial", 12))
progress_label.pack(pady=5)

# Scrollable Label Selection Area
label_container = tk.Frame(root)
label_container.pack(fill="x", padx=10, pady=5)

label_canvas = Canvas(label_container, height=300)
label_scrollbar = Scrollbar(label_container, orient="vertical", command=label_canvas.yview)

label_inner_frame = Frame(label_canvas)
label_canvas.create_window((0, 0), window=label_inner_frame, anchor="nw")

label_canvas.config(yscrollcommand=label_scrollbar.set)
label_canvas.pack(side="left", fill="x", expand=True)
label_scrollbar.pack(side="right", fill="y")

label_canvas.bind_all("<MouseWheel>", on_mouse_scroll)

# Load labels
json_file = label_file
if json_file:
    with open(json_file, "r") as f:
        label_data = sorted(json.load(f))  # Sort labels alphabetically
    refresh_label_buttons(label_data, label_inner_frame, label_canvas, save_annotation)

root.mainloop()
