import unreal
import os
import json
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk

def clean_texture_name(raw_name):
    if raw_name.startswith("Texture2D'") and raw_name.endswith("'"):
        raw_name = raw_name[len("Texture2D'"):-1]
    raw_name = os.path.splitext(raw_name)[0]
    return raw_name

def parse_texture_params(json_data):
    texture_params = {}
    try:
        properties = json_data[0]['Properties']
    except Exception as e:
        unreal.log_error(f"Error reading JSON properties: {e}")
        return texture_params

    for tex_param in properties.get('TextureParameterValues', []):
        param_info = tex_param.get('ParameterInfo', {})
        param_name = param_info.get('Name', '').lower()
        param_value = tex_param.get('ParameterValue', {})
        if isinstance(param_value, dict):
            raw_tex_name = param_value.get('ObjectName', '')
            cleaned_tex_name = clean_texture_name(raw_tex_name)
            texture_params[param_name] = cleaned_tex_name
    return texture_params

def create_material_from_textures(material_name, texture_params, textures_root_path='/Game'):
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.MaterialFactoryNew()
    package_path = '/Game/GeneratedMaterials'

    existing_material = unreal.EditorAssetLibrary.find_asset_data(f"{package_path}/{material_name}").get_asset()
    if existing_material:
        unreal.log_warning(f"Material '{material_name}' already exists. Skipping.")
        return existing_material

    new_material = asset_tools.create_asset(material_name, package_path, None, factory)
    if not new_material:
        unreal.log_error(f"Failed to create material: {material_name}")
        return None

    material_lib = unreal.MaterialEditingLibrary
    sample_nodes = {}
    x_pos = -384
    y_pos = 0

    for param_name, tex_name in texture_params.items():
        tex_asset_path = f"{textures_root_path}/{tex_name}"
        texture_asset = unreal.EditorAssetLibrary.load_asset(tex_asset_path)

        if not texture_asset:
            alt_path = tex_asset_path.replace('/Game/', '/Game/ShadingAssets/Textures/')
            texture_asset = unreal.EditorAssetLibrary.load_asset(alt_path)

        if not texture_asset:
            unreal.log_warning(f"Texture asset not found: {tex_asset_path}")
            continue

        tex_sample_node = material_lib.create_material_expression(new_material, unreal.MaterialExpressionTextureSample, x_pos, y_pos)
        tex_sample_node.texture = texture_asset

        if 'normal' in param_name:
            tex_sample_node.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
        else:
            tex_sample_node.sampler_type = unreal.MaterialSamplerType.SAMPLERTYPE_COLOR

        sample_nodes[param_name] = tex_sample_node
        y_pos += 200

    def connect_property(param, channel, target):
        if param in sample_nodes:
            material_lib.connect_material_property(sample_nodes[param], channel, getattr(unreal.MaterialProperty, target, unreal.MaterialProperty.MP_BASE_COLOR))

    connect_property('albedo', 'RGB', 'MP_BASE_COLOR')
    connect_property('basecolor', 'RGB', 'MP_BASE_COLOR')
    connect_property('normal', 'RGB', 'MP_NORMAL')
    connect_property('roughness', 'R', 'MP_ROUGHNESS')
    connect_property('metallic', 'R', 'MP_METALLIC')
    connect_property('specular', 'R', 'MP_SPECULAR')
    connect_property('ao', 'R', 'MP_AMBIENT_OCCLUSION')
    connect_property('ambientocclusion', 'R', 'MP_AMBIENT_OCCLUSION')
    connect_property('emissive', 'RGB', 'MP_EMISSIVE_COLOR')
    connect_property('displacement', 'R', 'MP_WORLD_POSITION_OFFSET')

    material_lib.recompile_material(new_material)
    unreal.EditorAssetLibrary.save_loaded_asset(new_material)

    unreal.log(f"✅ Created material '{material_name}' with textures: {list(sample_nodes.keys())}")
    return new_material

def process_json_folder_with_progress(folder_path):
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]

    # Tkinter setup for progress bar
    root = tk.Tk()
    root.title("Material Creation Progress")
    root.geometry("500x100")

    label = tk.Label(root, text="Creating materials...")
    label.pack(pady=5)

    progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate", maximum=len(json_files))
    progress.pack(pady=10)

    root.update()

    for idx, json_file in enumerate(json_files, start=1):
        full_path = os.path.join(folder_path, json_file)
        unreal.log(f"📄 Processing: {full_path}")
        try:
            with open(full_path, 'r') as f:
                json_data = json.load(f)
        except Exception as e:
            unreal.log_error(f"Failed to load JSON file {json_file}: {e}")
            continue

        material_name = json_data[0].get('Name', os.path.splitext(json_file)[0])
        texture_params = parse_texture_params(json_data)

        if not texture_params:
            unreal.log_warning(f"⚠️ No textures found in {json_file}")
            continue

        create_material_from_textures(material_name, texture_params)

        progress["value"] = idx
        root.update_idletasks()

    label.config(text="Done!")
    root.after(1500, root.destroy)
    root.mainloop()

def choose_json_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select JSON Folder")
    return folder_path

# Run the full process
selected_folder = choose_json_folder()
if selected_folder:
    process_json_folder_with_progress(selected_folder)
else:
    unreal.log_warning("❌ No folder selected. Exiting.")
