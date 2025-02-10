import os
import json
import shutil
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# Global variables
image_list = []
current_index = 0
image_dir = ""
output_csv = "annotations.csv"
label_data = []
csv_columns = ["image_filename", "label"]

# Load labels from JSON file
def load_labels():
    global label_data
    json_file = filedialog.askopenfilename(title="Select Labels JSON", filetypes=[("JSON Files", "*.json")])
    if json_file:
        with open(json_file, "r") as f:
            label_data = json.load(f)
        label_listbox.delete(0, tk.END)  # Clear existing labels
        for label in label_data:
            label_listbox.insert(tk.END, label)

# Load images from directory
def load_images():
    global image_list, image_dir, current_index
    image_dir = filedialog.askdirectory(title="Select Image Directory")
    if image_dir:
        image_list = [f for f in os.listdir(image_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        current_index = 0
        show_image()

# Show image in the GUI
def show_image():
    global current_index
    if not image_list:
        return

    image_path = os.path.join(image_dir, image_list[current_index])
    image = Image.open(image_path)
    image = image.resize((400, 400), Image.Resampling.LANCZOS)
    img = ImageTk.PhotoImage(image)
    img_label.config(image=img)
    img_label.image = img
    filename_label.config(text=image_list[current_index])

# Save annotation to CSV
def save_annotation(label):
    global current_index
    if not image_list:
        return

    image_name = image_list[current_index]
    output_dir = os.path.join(image_dir, label)

    # Ensure label directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Append annotation to CSV
    df = pd.DataFrame([[image_name, label]], columns=csv_columns)
    if not os.path.exists(output_csv):
        df.to_csv(output_csv, index=False)
    else:
        df.to_csv(output_csv, mode="a", header=False, index=False)

    # Move the image to label directory
    shutil.move(os.path.join(image_dir, image_name), os.path.join(output_dir, image_name))

    # Move to next image
    current_index += 1
    if current_index < len(image_list):
        show_image()
    else:
        messagebox.showinfo("Done", "All images labeled!")
        root.quit()

# Tkinter GUI Setup
root = tk.Tk()
root.title("Image Annotation Tool")

frame = tk.Frame(root)
frame.pack(pady=10)

# Image Display
img_label = tk.Label(frame)
img_label.pack()

filename_label = tk.Label(root, text="", font=("Arial", 12))
filename_label.pack(pady=5)

# Load Buttons
btn_frame = tk.Frame(root)
btn_frame.pack()

tk.Button(btn_frame, text="Load Labels", command=load_labels).grid(row=0, column=0, padx=5)
tk.Button(btn_frame, text="Load Images", command=load_images).grid(row=0, column=1, padx=5)

# Label Selection List
label_listbox = tk.Listbox(root, height=10, width=50)
label_listbox.pack(pady=10)

def on_label_select(event):
    selected_index = label_listbox.curselection()
    if selected_index:
        selected_label = label_listbox.get(selected_index[0])
        save_annotation(selected_label)

label_listbox.bind("<Double-Button-1>", on_label_select)

root.mainloop()
