import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import requests
from file_handler import get_filtered_images, save_approved_image
from image_display import get_full_image_path
from api_handler import get_neighbors
from merge_output import merge_csv_files
from config import OUTPUT_DIR

API_URL = "http://34.97.0.203:8001/explore/explore_neighbor_images"

class ImageReviewApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Review App")

        # **Start at top-left corner**
        self.root.geometry("+0+0")  # Position window at top-left

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.root.geometry(f"{int(screen_width * 0.9)}x{int(screen_height * 0.9)}")

        self.action_label = ""
        self.images = []
        self.current_index = 0
        self.neighbors = []

        # **Title Label (Dynamic)**
        self.title_label = tk.Label(root, text="Select a CSV File", font=("Arial", 16))
        self.title_label.pack(pady=10)

        # **Progress Label (Fixed)**
        self.progress_label = tk.Label(root, text="0/0", font=("Arial", 12))
        self.progress_label.pack(pady=5)

        # **Main Layout Frame**
        self.main_frame = tk.Frame(root)
        self.main_frame.pack(expand=True, fill="both")

        # **Left Section (Neighbors - Before)**
        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side="left", expand=True, fill="both")

        # **Center Section (Main Image)**
        self.center_frame = tk.Frame(self.main_frame)
        self.center_frame.pack(side="left", expand=True, fill="both")

        # **Right Section (Neighbors - After)**
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side="left", expand=True, fill="both")

        # **Canvases for Images**
        self.left_canvas = tk.Frame(self.left_frame)
        self.left_canvas.pack(expand=True, fill="both")

        self.center_canvas = tk.Canvas(self.center_frame, width=500, height=500)
        self.center_canvas.pack(expand=True)

        self.right_canvas = tk.Frame(self.right_frame)
        self.right_canvas.pack(expand=True, fill="both")

        # **Button Layout (Centered)**
        self.buttons_frame = tk.Frame(root)
        self.buttons_frame.pack(fill="x", pady=10)
        self.buttons_frame.place(relx=0.5, rely=0.95, anchor="s")  # Center buttons

        self.back_btn = tk.Button(self.buttons_frame, text="BACK", command=self.load_previous)
        self.back_btn.pack(side="left", padx=10)

        self.approve_btn = tk.Button(self.buttons_frame, text="APPROVE", bg="green", command=self.approve_image)
        self.approve_btn.pack(side="left", padx=10)

        self.load_neighbors_btn = tk.Button(self.buttons_frame, text="LOAD NEIGHBORS", command=self.load_neighbors)
        self.load_neighbors_btn.pack(side="left", padx=10)

        self.decline_btn = tk.Button(self.buttons_frame, text="DECLINE", bg="red", command=self.skip_image)
        self.decline_btn.pack(side="left", padx=10)

        self.next_btn = tk.Button(self.buttons_frame, text="NEXT", command=self.load_next)
        self.next_btn.pack(side="right", padx=10)

        # **File Selection Button**
        self.select_file_btn = tk.Button(root, text="Select CSV File", command=self.select_file)
        self.select_file_btn.pack(pady=10)

    def select_file(self):
        """Opens file dialog and loads images from CSV"""
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        self.action_label = os.path.basename(file_path).replace(".csv", "")
        self.title_label.config(text=f"Is this image belong to {self.action_label}?")
        self.images = get_filtered_images(file_path)
        self.current_index = 0

        if self.images:
            self.load_image()
            self.update_progress()

    def load_image(self):
        """Displays images in the three areas"""
        if not self.images:
            return

        center_image_path = get_full_image_path(self.images[self.current_index])
        self.display_image(self.center_canvas, center_image_path, (500, 500))

        # Clear left & right panels (neighbors are loaded separately)
        for widget in self.left_canvas.winfo_children():
            widget.destroy()
        for widget in self.right_canvas.winfo_children():
            widget.destroy()

    def display_image(self, canvas, image_path, size, row=0, col=0):
        """Displays an image in the given canvas using a grid layout."""
        if image_path and os.path.exists(image_path):
            img = Image.open(image_path)
            img = img.resize(size, Image.Resampling.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)

            label = tk.Label(canvas, image=img_tk)
            label.image = img_tk  # Keep reference
            label.grid(row=row, column=col, padx=5, pady=5)  # Place in grid

    def update_progress(self):
        """Updates progress label and checks if all images are reviewed."""
        if self.current_index  + 1>= len(self.images):
            self.progress_label.config(text="All images reviewed!")
            messagebox.showinfo("Done!", "You have reviewed all images.")
            merge_csv_files()
            self.root.quit()  # Exit the app
        else:
            self.progress_label.config(text=f"{self.current_index+1}/{len(self.images)}")

    def load_previous(self):
        """Loads previous image"""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()
            self.update_progress()

    def load_next(self):
        """Loads next image and exits if finished"""
        if self.current_index < len(self.images) - 1:
            self.current_index += 1
            self.load_image()
            self.update_progress()
        else:
            self.update_progress()  # This will trigger the exit

    def approve_image(self):
        """Approves the current image"""
        if self.images:
            save_approved_image(self.action_label, self.images[self.current_index])
            self.load_next()

    def skip_image(self):
        """Skips the current image"""
        self.load_next()

    def load_neighbors(self):
        """Fetch and display neighboring images in a grid layout."""
        if not self.images:
            return

        image_url = self.images[self.current_index]
        response = get_neighbors(image_url)

        if not response:
            print("No neighbors found.")
            return

        middle_index = len(response) // 2
        front_neighbors = response[:middle_index]
        back_neighbors = response[middle_index + 1:]

        # Define the grid size (3 rows, 2 columns)
        GRID_ROWS = 3
        GRID_COLS = 2

        # Clear left & right canvas before adding new images
        for widget in self.left_canvas.winfo_children():
            widget.destroy()
        for widget in self.right_canvas.winfo_children():
            widget.destroy()

        # Display Left Neighbors (Before)
        for i, img_url in enumerate(front_neighbors[:GRID_ROWS * GRID_COLS]):
            full_path = get_full_image_path(img_url)
            row, col = divmod(i, GRID_COLS)  # Convert index to grid row/col
            self.display_image(self.left_canvas, full_path, (150, 150), row, col)

        # Display Right Neighbors (After)
        for i, img_url in enumerate(back_neighbors[:GRID_ROWS * GRID_COLS]):
            full_path = get_full_image_path(img_url)
            row, col = divmod(i, GRID_COLS)  # Convert index to grid row/col
            self.display_image(self.right_canvas, full_path, (150, 150), row, col)

        print(f"Neighbors loaded: {len(response)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageReviewApp(root)
    root.mainloop()
