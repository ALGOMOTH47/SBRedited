import unreal
import os
import json

# SETTINGS
JSON_FOLDER = "H:/f/Fnaf_mod_tool/json/Maps/mats"  # Full path to material JSON files
SAVE_MATERIALS_TO = "/Game/Matireals"  # Where to save generated materials
ROOT_DIR = "/Game"  # Root directory to search for textures

# Helpers
def ensure_directory_exists(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)

def find_texture_by_filename(root_dir, filename):
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_registry.scan_paths_synchronous([root_dir], True)
    assets = asset_registry.get_assets_by_path(root_dir, recursive=True)

    base_name = os.path.basename(filename).split(".")[0].lower()

    for asset in assets:
        if asset.asset_class == "Texture2D" and str(asset.asset_name).lower() == base_name:
            return asset.object_path

    # Fallback fuzzy match: try partial matching
    for asset in assets:
        if asset.asset_class == "Texture2D" and base_name in str(asset.asset_name).lower():
            return asset.object_path

    return None

def material_exists_in_folder(material_name, folder_path):
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = asset_registry.get_assets_by_path(folder_path, recursive=False)

    for asset in assets:
        if asset.asset_class == "Material" and str(asset.asset_name) == material_name:
            return True
    return False

def create_material(material_name, textures):
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material_path = SAVE_MATERIALS_TO + "/" + material_name

    ensure_directory_exists(SAVE_MATERIALS_TO)

    if unreal.EditorAssetLibrary.does_asset_exist(material_path):
        print(f"Material {material_name} already exists, skipping creation.")
        return unreal.load_asset(material_path)

    resolved_textures = {}
    for param_name, texture_filename in textures.items():
        texture_path = find_texture_by_filename(ROOT_DIR, texture_filename)
        if texture_path:
            resolved_textures[param_name] = texture_path
        else:
            print(f"  - Texture not found for: {texture_filename}")

    if len(resolved_textures) == 0:
        print(f"⚠️ No textures found for {material_name}. Still creating empty material.")

    material_factory = unreal.MaterialFactoryNew()
    material = asset_tools.create_asset(material_name, SAVE_MATERIALS_TO, unreal.Material, material_factory)
    print(f"🎨 Created new material: {material_name}")

    x = -384
    y = -200
    y_spacing = 250

    for param_name, texture_path in resolved_textures.items():
        texture = unreal.load_asset(texture_path)
        if not texture:
            continue

        tex_sample = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionTextureSample, x, y)
        tex_sample.texture = texture

        param_name_lower = param_name.lower()
        if "normal" in param_name_lower:
            tex_sample.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
            unreal.MaterialEditingLibrary.connect_material_property(tex_sample, "RGB", unreal.MaterialProperty.MP_NORMAL)
        elif "emissive" in param_name_lower:
            unreal.MaterialEditingLibrary.connect_material_property(tex_sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        elif "ao" in param_name_lower or "rough" in param_name_lower or "metal" in param_name_lower:
            unreal.MaterialEditingLibrary.connect_material_property(tex_sample, "RGB", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
        elif "basecolor" in param_name_lower or "diffuse" in param_name_lower or "albedo" in param_name_lower:
            unreal.MaterialEditingLibrary.connect_material_property(tex_sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

        print(f"  - Added and connected TextureSample for {param_name} ({os.path.basename(str(texture_path))})")

        y += y_spacing

    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(material_path)
    unreal.SystemLibrary.collect_garbage()
    print(f"✅ Saved and cleaned up memory for material: {material_name}")

    return material

# Main
def process_json_materials(json_folder):
    json_files = []
    for root, dirs, files in os.walk(json_folder):
        for file in files:
            if file.endswith(".json"):
                json_files.append(os.path.join(root, file))

    with unreal.ScopedSlowTask(len(json_files), "Generating Materials from JSON...") as task:
        task.make_dialog(True)

        for i, full_path in enumerate(json_files):
            if task.should_cancel():
                print("Material generation canceled.")
                break

            file = os.path.basename(full_path)
            mat_name = os.path.splitext(file)[0]

            task.enter_progress_frame(1.0, f"Processing {mat_name}...")

            if material_exists_in_folder(mat_name, SAVE_MATERIALS_TO):
                print(f"Material {mat_name} already exists in Materials folder, skipping.")
                continue

            with open(full_path, 'r') as f:
                try:
                    data = json.load(f)
                except Exception as e:
                    print(f"❌ Failed to parse JSON {file}: {e}")
                    continue

                if "Textures" in data and isinstance(data["Textures"], dict):
                    textures = data["Textures"]
                    create_material(mat_name, textures)
                else:
                    print(f"No valid 'Textures' section in {file}")

# Run
process_json_materials(JSON_FOLDER)
