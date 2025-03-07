import pandas as pd
import os
from config import OUTPUT_DIR, TEMP_DIR

def load_csv(file_path):
    """Loads the CSV file and returns a DataFrame."""
    if not os.path.exists(file_path):
        return None
    return pd.read_csv(file_path, header=None, names=["partial_url"])

def get_filtered_images(csv_path):
    """Returns images that are not in golden corpus"""
    action_label = os.path.basename(csv_path).replace(".csv", "")
    golden_path = f"{TEMP_DIR}/temp_golden_corpus_for_{action_label}.csv"
    
    df = load_csv(csv_path)
    if df is None:
        return []

    if os.path.exists(golden_path):
        golden_df = load_csv(golden_path)
        df = df[~df["partial_url"].isin(golden_df["partial_url"])]  # Remove reviewed images

    return df["partial_url"].tolist()

def save_approved_image(action_label, image_url):
    """Save approved image to golden corpus"""
    golden_path = f"{TEMP_DIR}/temp_golden_corpus_for_{action_label}.csv"
    with open(golden_path, "a") as f:
        f.write(f"{image_url}\n")
