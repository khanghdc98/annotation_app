import tkinter as tk
from tkinter import messagebox
import pandas as pd
from PIL import Image, ImageTk
import os

from constant import *


THUMBNAIL_SIZE = (100, 100)  # Thumbnail size
def show_propagated_records_dialog(root, propagated_records, label):
    """
    Opens a dialog to review and remove propagated records before saving.

    Args:
        propagated_records (list): List of image file paths returned by the server.
        label (str): The label assigned to the current image.
    """
    def remove_selected():
        """Removes selected items from the list and updates the UI."""
        nonlocal propagated_records
        propagated_records = [img for img in propagated_records if img not in selected_images]
        selected_images.clear()
        update_grid()
        if len(propagated_records) == 0:
            messagebox.showinfo("Success", "No more image to propagate")
            dialog.destroy()


    def toggle_selection(img_path, button):
        """Toggles selection of an image (highlights if selected)."""
        if img_path in selected_images:
            selected_images.remove(img_path)
            button.config(bg="white")  # Reset color
        else:
            selected_images.add(img_path)
            button.config(bg="red")  # Highlight selected

    def submit_records():
        """Writes final propagated records to the CSV file."""
        if not propagated_records:
            messagebox.showinfo("Info", "No records to save.")
            dialog.destroy()
            return

        df = pd.DataFrame([[filename, label] for filename in propagated_records], columns=csv_columns)
        df.to_csv(output_csv, mode="a", header=not os.path.exists(output_csv), index=False)

        messagebox.showinfo("Success", "Propagated annotations saved.")
        dialog.destroy()

    def update_grid():
        """Refresh the grid with the current propagated records."""
        for widget in grid_frame.winfo_children():
            widget.destroy()

        row, col = 0, 0
        for img_path in propagated_records:
            try:
                img = Image.open(os.path.join(base_path, img_path))
                img.thumbnail(THUMBNAIL_SIZE)
                img_tk = ImageTk.PhotoImage(img)

                # Create button first without command
                btn = tk.Button(grid_frame, image=img_tk, width=100, height=100)
                btn.image = img_tk  # Prevent garbage collection

                # Assign command after creating button
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

    def on_mouse_scroll(event):
        """Enable mouse scroll for the image grid."""
        canvas.yview_scroll(-1 * (event.delta // 120), "units")

    # Create the dialog window
    dialog = tk.Toplevel(root)
    dialog.title("Review Propagated Records")
    dialog.geometry("500x500")  # Increased size
    dialog.transient(root)
    dialog.grab_set()

    # Instructions
    tk.Label(dialog, text="Click images to select/remove. Scroll to navigate.", font=("Arial", 12)).pack(pady=5)

    # Create a frame to hold the scrollable area
    frame_container = tk.Frame(dialog)
    frame_container.pack(fill="both", expand=True, padx=10, pady=5)

    # Scrollable frame setup
    canvas = tk.Canvas(frame_container)
    scrollbar = tk.Scrollbar(frame_container, orient="vertical", command=canvas.yview)

    scroll_frame = tk.Frame(canvas)
    scroll_frame.bind("<Configure>", lambda e: canvas.config(scrollregion=canvas.bbox("all")))

    # Ensure frame remains within canvas
    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.config(yscrollcommand=scrollbar.set)

    # Packing scroll elements
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Grid frame inside scrollable area
    grid_frame = tk.Frame(scroll_frame)
    grid_frame.pack()

    # Track selected images
    selected_images = set()

    # Populate the grid
    update_grid()

    # Enable mouse scrolling
    dialog.bind("<MouseWheel>", on_mouse_scroll)

    # Buttons frame (placed OUTSIDE the scrollable area)
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(fill="x", pady=10)  # Ensure it's always visible

    # Buttons with fixed width to avoid shrinking text
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
        if col >= 11:  # Limit to 11 buttons per row
            col = 0
            row += 1

    # Update scroll region
    label_canvas.update_idletasks()
    label_canvas.config(scrollregion=label_canvas.bbox("all"))