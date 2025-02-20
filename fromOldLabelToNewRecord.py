import json

def load_txt_mapping(txt_file):
    """
    Reads the .txt file and maps label names to old label codes.
    
    :param txt_file: Path to the .txt file containing old labels.
    :return: Dictionary mapping label names to old label codes.
    """
    label_mapping = {}
    with open(txt_file, "r") as file:
        for line in file:
            parts = line.strip().split(" ", 1)  # Split at first space
            if len(parts) == 2:
                code, label = parts
                label_mapping[label] = code  # Map label name to code
    return label_mapping

def map_old_label_name(i: int, old_label_name: str, txt_file: str, old_to_new_map: dict, new_label_map: dict):
    """
    Maps an old label name to a record with newId and newLabel.

    :param old_label_name: The old label name (e.g., "Holding some clothes").
    :param txt_file: Path to the .txt file to map label names to codes.
    :param old_to_new_map: Dictionary mapping old codes to new labels.
    :param new_label_map: Dictionary mapping new labels to new IDs.
    :return: A dictionary with newId and newLabel.
    """
    # Load label name to code mapping
    label_name_to_code = load_txt_mapping(txt_file)

    # Get the old code from the label name
    old_code = label_name_to_code.get(old_label_name)
    if not old_code:
        return {"error": f"Label '{old_label_name}' not found in the .txt file."}

    # Get the new label from the old code
    new_label = old_to_new_map.get(old_code, "Unknown")

    # Get the new ID from the new label
    new_id = next((k for k, v in new_label_map.items() if v == new_label), "Unknown")
    print(f"{i}. {old_label_name:50} -> {i}. {new_label}")

    return {"newId": new_id, "newLabel": new_label}

# Load JSON files
with open("oldToNewLabelMap.json", "r") as file:
    old_to_new_label_map = json.load(file)

with open("newLabelMap.json", "r") as file:
    new_label_map = json.load(file)

# Example Usage:
txt_file_path = "Charades_v1_classes.txt"  # Path to your .txt file
old_label_name_input = "Holding some clothes"  # Example label name

if __name__ == "__main__":
    all_old_labels = []
    with open(txt_file_path, "r") as file:
        for line in file:
            all_old_labels.append(line.strip().split(" ", 1)[1])
    for i, old_label_name_input in enumerate(all_old_labels):
        mapped_record = map_old_label_name(i, old_label_name_input, txt_file_path, old_to_new_label_map, new_label_map)
