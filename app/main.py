import os
import json
import shutil
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, Canvas, Frame, Scrollbar, Entry, Label
from PIL import Image, ImageTk
from rest_client import RestClient
from utils import get_path_for_vector_db, get_base_path
from constant import image_list, current_index, image_dir, output_dir, output_csv, label_data, csv_columns, annotated_images, total_images, base_path, have_base_path, label_file, button_per_row


api_client = RestClient("http://34.97.0.203:8001")

THUMBNAIL_SIZE = (100, 100)  # Thumbnail size
def show_propagated_records_dialog(root, base_path, propagated_records, label):
    """
    Opens a dialog to review and remove propagated records before saving.
    """
    global image_list, current_index
    def remove_selected():
        """Removes selected items from propagated_records and image_list, then updates the UI."""
        nonlocal propagated_records
        # Remove selected images from both propagated_records and image_list
        propagated_records = [img for img in propagated_records if img not in selected_images]
        
        for img in selected_images:
            if img in image_list:
                image_list.remove(img)  # Remove from main image list as well
        
        selected_images.clear()
        update_grid()

        if not propagated_records:
            messagebox.showinfo("Success", "No more images to propagate.")
            dialog.destroy()
            save_annotation(label, skip_api_call=True)  # Resume save_annotation but skip API call
            return

    def submit_records():
        """Writes final propagated records to CSV and updates image list."""
        if not propagated_records:
            messagebox.showinfo("Info", "No records to save.")
            dialog.destroy()
            save_annotation(label, skip_api_call=True)  # Resume save_annotation but skip API call
            return

        # Save the remaining propagated records to CSV
        print("image name propagated: ", propagated_records)
        df = pd.DataFrame([[filename, label] for filename in propagated_records], columns=csv_columns)
        df.to_csv(output_csv, mode="a", header=not os.path.exists(output_csv), index=False)

        # Remove saved records from image_list
        for img in propagated_records:
            print("image_list", image_list[-2:])
            for img_path in image_list:
                temp_img_path = get_path_for_vector_db(img_path).replace("\\", "/")
                if img in temp_img_path:
                    print("removed: ", img_path)
                    image_list.remove(img_path)
                    print("img annotated", img)
                    annotated_images.add(img)
                    break
        
        update_progress_label()

        # Update UI to the next available image
        global current_index
        current_index += 1

        if current_index < len(image_list):
            global img_label, filename_label
            img_label, filename_label = show_image(current_index, image_list, img_label, filename_label) or (img_label, filename_label)
        else:
            messagebox.showinfo("Done", "All images labeled!")
            root.quit()

        dialog.destroy()

    def update_grid():
        """Refresh the grid with the current propagated records."""
        for widget in grid_frame.winfo_children():
            widget.destroy()

        row, col = 0, 0
        for img_path in propagated_records:
            try:
                # Find the real image path with extension
                img_full_path = None
                for ext in [".png", ".jpg", ".jpeg"]:
                    potential_path = os.path.join(base_path, img_path + ext).replace("\\", "/")
                    if os.path.exists(potential_path):
                        img_full_path = potential_path
                        break

                if not img_full_path:
                    print(f"Image file for {img_path} not found with any expected extension.")
                    continue

                if not os.path.exists(img_full_path):
                    print(f"Image file {img_full_path} not found.")
                    continue

                img = Image.open(img_full_path)
                img.thumbnail(THUMBNAIL_SIZE)
                img_tk = ImageTk.PhotoImage(img)

                btn = tk.Button(grid_frame, image=img_tk, width=100, height=100)
                btn.image = img_tk  # Prevent garbage collection

                btn.config(command=lambda p=img_path, b=btn: toggle_selection(p, b))
                btn.grid(row=row, column=col, padx=5, pady=5)

                col += 1
                if col >= 3:  # 3 images per row
                    col = 0
                    row += 1
            except Exception as e:
                print(f"Error loading {img_path}: {e}")

        canvas.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    def toggle_selection(img_path, button):
        """Toggles selection of an image (highlights if selected)."""
        if img_path in selected_images:
            selected_images.remove(img_path)
            button.config(bg="white")  # Reset color
        else:
            selected_images.add(img_path)
            button.config(bg="red")  # Highlight selected

    def on_mouse_scroll(event):
        """Enable mouse scroll for the image grid."""
        canvas.yview_scroll(-1 * (event.delta // 120), "units")

    # Create the dialog window
    dialog = tk.Toplevel(root)
    dialog.title("Review Propagated Records")
    dialog.geometry("500x500")
    dialog.transient(root)
    dialog.grab_set()

    tk.Label(dialog, text="Click images to select/remove. Scroll to navigate.", font=("Arial", 12)).pack(pady=5)

    frame_container = tk.Frame(dialog)
    frame_container.pack(fill="both", expand=True, padx=10, pady=5)

    canvas = tk.Canvas(frame_container)
    scrollbar = tk.Scrollbar(frame_container, orient="vertical", command=canvas.yview)

    scroll_frame = tk.Frame(canvas)
    scroll_frame.bind("<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all")))

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.config(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    grid_frame = tk.Frame(scroll_frame)
    grid_frame.pack()

    selected_images = set()

    update_grid()

    dialog.bind("<MouseWheel>", on_mouse_scroll)

    btn_frame = tk.Frame(dialog)
    btn_frame.pack(fill="x", pady=10)

    remove_btn = tk.Button(btn_frame, text="Remove Selected", command=remove_selected, bg="red", fg="white", width=20, height=2)
    remove_btn.pack(side="left", padx=10)

    submit_btn = tk.Button(btn_frame, text="Submit", command=submit_records, bg="green", fg="white", width=20, height=2)
    submit_btn.pack(side="right", padx=10)

    dialog.mainloop()

# Show image in GUI with height restriction
def show_image(current_index, image_list, img_label, filename_label):
    if not image_list:
        print("No images to display.")
        filename_label.config(text="No images available")
        img_label.config(image="")  # Clear the previous image
        return img_label, filename_label  # Ensure function always returns values

    image_path = image_list[current_index]  # Already an absolute path
    try:
        image = Image.open(image_path)
        max_height = 400
        img_width, img_height = image.size
        scale_factor = max_height / img_height
        new_size = (int(img_width * scale_factor), max_height) if img_height > max_height else (img_width, img_height)

        image = image.resize(new_size, Image.Resampling.LANCZOS)
        img = ImageTk.PhotoImage(image)
        img_label.config(image=img)
        img_label.image = img  # Prevent garbage collection
        filename_label.config(text=f"Image: {os.path.basename(image_path)}")

    except Exception as e:
        print(f"Error displaying image {image_path}: {e}")
        filename_label.config(text=f"Error loading image: {os.path.basename(image_path)}")
        img_label.config(image="")  # Clear image if error occurs

    return img_label, filename_label  # Always return valid objects


# Enable mouse scroll for label selection area
def on_mouse_scroll(event, label_canvas):
    label_canvas.yview_scroll(-1 * (event.delta // 120), "units")

# Create a scrollable label selection area
def refresh_label_buttons(label_data, label_inner_frame, label_canvas, save_annotation):
    # Clear existing buttons inside the frame without destroying it
    for widget in label_inner_frame.winfo_children():
        widget.destroy()
    
    # Sort labels alphabetically before displaying
    sorted_labels = sorted(label_data)

    # Create buttons dynamically
    row, col = 0, 0
    for label in sorted_labels:
        btn = tk.Button(
            label_inner_frame, text=label, font=("Arial", 10), 
            command=lambda l=label: save_annotation(l), 
            bg="lightgray", wraplength=100, anchor="center"  # Auto-fit content
        )
        btn.grid(row=row, column=col, padx=5, pady=5, sticky="w")

        col += 1
        if col >= button_per_row: 
            col = 0
            row += 1

    # Update scroll region
    label_canvas.update_idletasks()
    label_canvas.config(scrollregion=label_canvas.bbox("all"))

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
    image_list = sorted([img for img in all_images if os.path.splitext(get_path_for_vector_db(img))[0] not in annotated_images])
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
def save_annotation(label, skip_api_call=False):
    global current_index
    global annotated_images
    # if not image_list or not output_dir:
    #     messagebox.showwarning("Warning", "Please select an output directory first!")
    #     return

    image_name = image_list[current_index]
    image_name = get_path_for_vector_db(image_name) # Only for LSC dataset

     # If API call should be skipped, just append the record to CSV and move to the next image
    if skip_api_call:
        image_name_no_ext = str(os.path.splitext(image_name)[0])
        df = pd.DataFrame([[image_name_no_ext, label]], columns=csv_columns)
        df.to_csv(output_csv, mode="a", header=not os.path.exists(output_csv), index=False)
        annotated_images.add(image_name_no_ext)
        print(len(annotated_images))
        update_progress_label()
        
        # Move to the next image
        current_index += 1
        if current_index < len(image_list):
            global img_label, filename_label
            img_label, filename_label = show_image(current_index, image_list, img_label, filename_label) or (img_label, filename_label)
        else:
            messagebox.showinfo("Done", "All images labeled!")
            root.quit()
        return
    # label_folder = os.path.join(output_dir, label)

    # # Ensure label directory exists
    # os.makedirs(label_folder, exist_ok=True)

    # # Copy the image to the label directory
    # shutil.copy(os.path.join(image_dir, image_name), os.path.join(label_folder, image_name))

    # Propagate label by calling to server
    image_name_no_ext = str(os.path.splitext(image_name)[0])
    response = api_client.send_annotation(image_name_no_ext, no_return_records=10)
    
    propagated_records = response if response else []
    if len(propagated_records) == 0:
        save_annotation(label, skip_api_call=True)  # Resume save_annotation but skip API call
        return
    for record in propagated_records:
        img_full_path = None
        for ext in [".png", ".jpg", ".jpeg"]:
            potential_path = os.path.join(base_path, record + ext).replace("\\", "/")
            if os.path.exists(potential_path):
                img_full_path = potential_path
                break

        if not img_full_path:
            print(f"Image file for {record} not found with any expected extension.")
            continue
        img_filename_with_ext = get_path_for_vector_db(img_full_path)
        if img_filename_with_ext in annotated_images:
            propagated_records.remove(record)
    if not propagated_records:
        print("No propagated records received.")
    else:
        # Show dialog to allow user to modify the list
        show_propagated_records_dialog(root, base_path, propagated_records, label)

    # # Append annotation to CSV
    # print("image_name not propagated: ", image_name)
    # df = pd.DataFrame([[image_name, label]], columns=csv_columns)
    # if not os.path.exists(output_csv):
    #     df.to_csv(output_csv, index=False)
    # else:
    #     df.to_csv(output_csv, mode="a", header=False, index=False)

    # # Add image to annotated set and update progress
    # annotated_images.add(image_name)
    # update_progress_label()

    # # Move to next image
    # current_index += 1
    # if current_index < len(image_list):
    #     img_label, filename_label = show_image(current_index, image_list, img_label, filename_label) or (img_label, filename_label)
    # else:
    #     messagebox.showinfo("Done", "All images labeled!")
    #     root.quit()

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
tk.Button(top_frame, text="Exit", font=("Arial", 12), command=lambda: on_exit(root), fg="white", bg="red").pack(side="right", padx=10)

def on_exit(root):
    """Ensures all Tkinter windows close properly."""
    for window in root.winfo_children():  # Close any open dialogs
        window.destroy()
    root.quit()
    root.destroy()  # Fully terminate the application


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
    print("Loaded labels from JSON file.")
    refresh_label_buttons(label_data, label_inner_frame, label_canvas, save_annotation)

root.mainloop()
