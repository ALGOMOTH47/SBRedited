import json
import os

# Function to search for the 'ReferencedTextures' key and extract texture details
def find_referenced_textures(json_file):
    with open(json_file, 'r') as file:
        # Read the entire JSON content
        data = json.load(file)

        # Search for the 'ReferencedTextures' field in the JSON structure
        def search_for_textures(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == 'ReferencedTextures' and isinstance(value, list):
                        print(f"Found 'ReferencedTextures':")
                        for texture in value:
                            texture_name = texture.get('ObjectName', 'Unknown')
                            texture_path = texture.get('ObjectPath', 'Unknown')
                            
                            # Strip the file path and extension
                            file_name = os.path.basename(texture_path)  # Get the file name with extension
                            texture_base_name = os.path.splitext(file_name)[0]  # Remove the extension

                            print(f"  - Texture Name: {texture_name}, Path: {texture_path}")
                            print(f"    Stripped Texture Name: {texture_base_name}")
                    # Recursively search for nested dictionaries
                    search_for_textures(value)
            elif isinstance(obj, list):
                for item in obj:
                    # Recursively search each item in the list
                    search_for_textures(item)

        # Start searching from the root of the JSON structure
        search_for_textures(data)

# Example usage
json_file = r"H:\f\Fnaf_mod_tool\json\Maps\_cable_color_tiling.json"  # Replace with the path to your JSON file
find_referenced_textures(json_file)
