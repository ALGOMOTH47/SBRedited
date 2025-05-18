import os
import json

# Root folder where JSON files are stored recursively
json_root = r"H:\f\Fnaf_mod_tool\fnaf9\Content\json\Maps"

# Folders where actual .uasset files may exist
search_dirs = [
    r"H:\f\Fnaf_mod_tool\fnaf9\Content",
    r"H:\f\Fnaf_mod_tool\meshes",
    r"H:\f\Fnaf_mod_tool\textures"
]

def get_all_json_files(folder):
    json_files = []
    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(".json"):
                json_files.append(os.path.join(root, file))
    return json_files

def extract_referenced_names(json_data):
    names = set()

    def recurse(data):
        if isinstance(data, dict):
            for v in data.values():
                recurse(v)
        elif isinstance(data, list):
            for item in data:
                recurse(item)
        elif isinstance(data, str):
            parts = data.replace("\\", "/").split("/")
            last = parts[-1]
            if "." in last:
                base = last.split(".")[0]
                if base:
                    names.add(base.lower())

    recurse(json_data)
    return names

def name_exists_somewhere(base_name, search_dirs):
    for folder in search_dirs:
        for root, _, files in os.walk(folder):
            for file in files:
                name, ext = os.path.splitext(file)
                if ext.lower() == '.uasset' and name.lower() == base_name:
                    return True
    return False

def main():
    json_files = get_all_json_files(json_root)
    report_lines = []

    for json_file in json_files:
        print(f"📄 Processing: {json_file}")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to parse {json_file}: {e}")
            continue

        referenced_names = extract_referenced_names(data)
        print(f"   🔍 Found {len(referenced_names)} referenced names")

        missing = []

        for name in referenced_names:
            if not name_exists_somewhere(name, search_dirs):
                print(f"   ❗ Missing: {name}")
                missing.append(name)

        if missing:
            report_lines.append(f"Missing files from: {json_file}")
            report_lines.extend(missing)
            report_lines.append("")

    output_path = os.path.join(json_root, "missing_files_report.txt")
    with open(output_path, "w", encoding='utf-8') as out_file:
        out_file.write("\n".join(report_lines))

    print(f"\n✅ Done. Missing file report saved to:\n{output_path}")

if __name__ == "__main__":
    main()
