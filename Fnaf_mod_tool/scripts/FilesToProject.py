import os
import shutil

# Base folder where to search for files (regardless of .txt paths)
source_folder = r"H:\f\Fnaf_mod_tool\assets"  # <- your actual source
destination_root = r"H:\f\Fnaf_mod_tool\backup"
txt_file = r"H:\f\Fnaf_mod_tool\scripts\file_list.txt"
# Read paths from the txt file
with open(txt_file, 'r') as f:
    lines = [line.strip() for line in f if line.strip()]

print(f"Processing {len(lines)} entries...")

# Extract unique base names from txt file
base_name_to_paths = {}

for line in lines:
    base_name = os.path.splitext(os.path.basename(line))[0]
    if base_name not in base_name_to_paths:
        base_name_to_paths[base_name] = []
    base_name_to_paths[base_name].append(line)

# Walk through source_folder and index all files by base name
source_index = {}

for dirpath, _, filenames in os.walk(source_folder):
    for fname in filenames:
        base = os.path.splitext(fname)[0]
        full_path = os.path.join(dirpath, fname)
        if base not in source_index:
            source_index[base] = []
        source_index[base].append(full_path)

# Match and copy
for base_name, target_paths in base_name_to_paths.items():
    if base_name in source_index:
        for source_file in source_index[base_name]:
            ext = os.path.splitext(source_file)[1]
            # Use the first path in the txt file for folder structure
            ref_txt_path = target_paths[0]
            relative_subpath = os.path.relpath(ref_txt_path, start=os.path.commonpath(lines))
            dest_dir = os.path.join(destination_root, os.path.dirname(relative_subpath))

            os.makedirs(dest_dir, exist_ok=True)
            dest_file = os.path.join(dest_dir, os.path.basename(source_file))

            shutil.copy2(source_file, dest_file)
            print(f"Copied: {source_file} → {dest_file}")
    else:
        print(f"[!] No match found for: {base_name}")

print("Done.")
