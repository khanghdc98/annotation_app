# Global variables
image_list = []
current_index = 0
image_dir = ""
output_dir = ""
output_csv = "annotations.csv"
label_file = "/Users/user/Documents/Projects/annotation_app/unique_new_labels.json"
label_data = []
csv_columns = ["image_filename", "label"]
annotated_images = set()  # Track already labeled images
total_images = 0  # Total images in directory
base_path = ""
have_base_path = False