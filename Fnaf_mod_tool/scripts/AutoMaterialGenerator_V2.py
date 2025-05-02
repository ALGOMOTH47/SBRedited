import unreal
import os
import json

# SETTINGS
JSON_FOLDER = "/Game/json/Mats"  # Folder to look for material JSON files
SAVE_MATERIALS_TO = "/Game/Materials"  # Where to save generated materials
ROOT_DIR = "/Game"  # Root directory to search for textures

# Helpers
def ensure_directory_exists(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)

def find_texture_by_filename(root_dir, filename):
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_registry.scan_paths_synchronous([root_dir], True)
    assets = asset_registry.get_assets_by_path(root_dir, recursive=True)

    for asset in assets:
        if asset.asset_class == "Texture2D" and str(asset.asset_name).lower() == filename.lower():
            return asset.object_path
    return None

def create_material(material_name, textures):
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material_path = SAVE_MATERIALS_TO + "/" + material_name

    ensure_directory_exists(SAVE_MATERIALS_TO)

    if unreal.EditorAssetLibrary.does_asset_exist(material_path):
        print(f"⚠️ Material {material_name} already exists, skipping creation.")
        return unreal.load_asset(material_path)

    material_factory = unreal.MaterialFactoryNew()
    material = asset_tools.create_asset(material_name, SAVE_MATERIALS_TO, unreal.Material, material_factory)
    print(f"🎨 Created new material: {material_name}")

    x = -384
    y = -200
    y_spacing = 250

    for param_name, texture_filename in textures.items():
        short_name = os.path.basename(texture_filename).split(".")[0]
        texture_path = find_texture_by_filename(ROOT_DIR, short_name)

        if not texture_path:
            print(f"  - Texture not found for: {short_name}")
            continue

        texture = unreal.load_asset(texture_path)
        if not texture:
            print(f"  - Failed to load asset: {texture_path}")
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

        print(f"  - Added and connected TextureSample for {param_name} ({short_name})")

        y += y_spacing

    unreal.MaterialEditingLibrary.layout_material_expressions(material)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_asset(material_path)
    print(f"✅ Saved material: {material_name}")

    return material

def process_json_materials(json_folder):
    json_folder_path = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()) + json_folder.replace("/Game", "")

    if not os.path.exists(json_folder_path):
        print(f"Folder does not exist: {json_folder_path}")
        return

    json_files = []
    for root, dirs, files in os.walk(json_folder_path):
        for file in files:
            if file.endswith(".json") and "MAT" in file.upper():
                json_files.append(os.path.join(root, file))

    print(f"Found {len(json_files)} JSON material files to process.")

    with unreal.ScopedSlowTask(len(json_files), "Generating Materials from JSON...") as task:
        task.make_dialog(True)

        for i, full_path in enumerate(json_files):
            if task.should_cancel():
                print("Material generation canceled.")
                break

            file = os.path.basename(full_path)
            mat_name = os.path.splitext(file)[0]
            material_path = SAVE_MATERIALS_TO + "/" + mat_name

            task.enter_progress_frame(1.0, f"Processing {mat_name} ({i + 1}/{len(json_files)})")

            # Skip if asset already exists
            if unreal.EditorAssetLibrary.does_asset_exist(material_path):
                print(f"⚠️ Skipping existing material: {mat_name}")
                continue

            try:
                with open(full_path, 'r') as f:
                    data = json.load(f)

                if "Textures" in data:
                    textures = data["Textures"]
                    create_material(mat_name, textures)
                else:
                    print(f"❌ No 'Textures' section in {file}")

            except Exception as e:
                print(f"❌ Failed to process {file}: {str(e)}")

# Run
process_json_materials(JSON_FOLDER)
