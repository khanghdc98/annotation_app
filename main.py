import os
import json
import shutil
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, Canvas, Frame, Scrollbar, Entry, Label
from PIL import Image, ImageTk

# Global variables
image_list = []
current_index = 0
image_dir = ""
output_dir = ""
output_csv = "annotations.csv"
label_data = []
csv_columns = ["image_filename", "label"]
annotated_images = set()  # Track already labeled images

# Load labels from JSON file
def load_labels():
    global label_data
    json_file = filedialog.askopenfilename(title="Select Labels JSON", filetypes=[("JSON Files", "*.json")])
    if json_file:
        with open(json_file, "r") as f:
            label_data = json.load(f)
        refresh_label_buttons()

# Load images from directory (only those not in CSV)
def load_images():
    global image_list, image_dir, current_index, annotated_images
    image_dir = filedialog.askdirectory(title="Select Image Directory")
    
    if not image_dir:
        return

    # Read the existing CSV file and track labeled images
    annotated_images = set()
    if os.path.exists(output_csv):
        try:
            df = pd.read_csv(output_csv)
            annotated_images = set(df["image_filename"].tolist())
        except Exception as e:
            messagebox.showerror("Error", f"Could not read CSV file: {e}")

    # Filter out already annotated images
    all_images = [f for f in os.listdir(image_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    image_list = [img for img in all_images if img not in annotated_images]

    if not image_list:
        messagebox.showinfo("Info", "No new images to label.")
        return

    current_index = 0
    show_image()

# Select output directory
def select_output_folder():
    global output_dir
    output_dir = filedialog.askdirectory(title="Select Output Directory")
    if not output_dir:
        messagebox.showwarning("Warning", "No output directory selected!")

# Show image in GUI with height restriction
def show_image():
    global current_index
    if not image_list:
        return

    image_path = os.path.join(image_dir, image_list[current_index])
    image = Image.open(image_path)

    # Restrict image height (e.g., max 500 pixels)
    max_height = 500
    img_width, img_height = image.size
    scale_factor = max_height / img_height
    new_size = (int(img_width * scale_factor), max_height) if img_height > max_height else (img_width, img_height)

    image = image.resize(new_size, Image.Resampling.LANCZOS)
    img = ImageTk.PhotoImage(image)
    img_label.config(image=img)
    img_label.image = img
    filename_label.config(text=f"Image: {image_list[current_index]}")

# Save annotation (copy image instead of moving)
def save_annotation(label):
    global current_index
    if not image_list or not output_dir:
        messagebox.showwarning("Warning", "Please select an output directory first!")
        return

    image_name = image_list[current_index]
    label_folder = os.path.join(output_dir, label)

    # Ensure label directory exists
    os.makedirs(label_folder, exist_ok=True)

    # Copy the image to the label directory
    shutil.copy(os.path.join(image_dir, image_name), os.path.join(label_folder, image_name))

    # Append annotation to CSV
    df = pd.DataFrame([[image_name, label]], columns=csv_columns)
    if not os.path.exists(output_csv):
        df.to_csv(output_csv, index=False)
    else:
        df.to_csv(output_csv, mode="a", header=False, index=False)

    # Move to next image
    current_index += 1
    if current_index < len(image_list):
        show_image()
    else:
        messagebox.showinfo("Done", "All images labeled!")
        root.quit()

# Create a scrollable label selection area
def refresh_label_buttons():
    # Clear existing buttons inside the frame without destroying it
    for widget in label_inner_frame.winfo_children():
        widget.destroy()
    
    # Create buttons dynamically
    row, col = 0, 0
    for label in label_data:
        btn = tk.Button(
            label_inner_frame, text=label, font=("Arial", 10), 
            command=lambda l=label: save_annotation(l), 
            bg="lightgray", wraplength=100, anchor="center"  # Auto-fit content
        )
        btn.grid(row=row, column=col, padx=5, pady=5, sticky="w")

        col += 1
        if col >= 10:  # Limit to 10 buttons per row
            col = 0
            row += 1

    # Update scroll region
    label_canvas.update_idletasks()
    label_canvas.config(scrollregion=label_canvas.bbox("all"))

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

# Image Display Area
img_frame = tk.Frame(root, bd=2, relief="solid")
img_frame.pack(fill="both", expand=True, padx=20, pady=10)

img_label = tk.Label(img_frame, bg="black")  # Black background for contrast
img_label.pack(expand=True)

filename_label = tk.Label(root, text="", font=("Arial", 14))
filename_label.pack(pady=5)

# Scrollable Label Selection Area
label_container = tk.Frame(root)
label_container.pack(fill="x", padx=10, pady=5)

label_canvas = Canvas(label_container, height=300)
label_scrollbar = Scrollbar(label_container, orient="vertical", command=label_canvas.yview)

label_inner_frame = Frame(label_canvas)  # Ensure this is created once

label_inner_frame.bind("<Configure>", lambda e: label_canvas.config(scrollregion=label_canvas.bbox("all")))
label_canvas.create_window((0, 0), window=label_inner_frame, anchor="nw")

label_canvas.config(yscrollcommand=label_scrollbar.set)
label_canvas.pack(side="left", fill="x", expand=True)
label_scrollbar.pack(side="right", fill="y")

# Run Tkinter App
root.mainloop()
