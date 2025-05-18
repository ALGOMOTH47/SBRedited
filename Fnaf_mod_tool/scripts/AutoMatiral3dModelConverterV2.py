import unreal
import os
import json

# ======= CONFIGURATION =======
JSON_FOLDER = r"H:\f\Fnaf_mod_tool\fnaf9\Content\json\other"
MATERIAL_SEARCH_FOLDER = '/Game/GeneratedMaterials'  # Folder to search for materials
DEFAULT_MATERIAL_PATH = '/Game/Materials/FailNoMatirealFound'  # Fallback material
# ==============================

def load_material_by_name(name, slot_index=0):
    assets = unreal.EditorAssetLibrary.list_assets(MATERIAL_SEARCH_FOLDER, recursive=True, include_folder=False)
    for asset_path in assets:
        if asset_path.endswith(name) or asset_path.endswith(name + '.' + name):
            asset = unreal.EditorAssetLibrary.load_asset(asset_path)
            if isinstance(asset, unreal.MaterialInterface):
                return asset

    # Fallback
    default_mat = unreal.EditorAssetLibrary.load_asset(DEFAULT_MATERIAL_PATH)
    if default_mat and isinstance(default_mat, unreal.MaterialInterface):
        unreal.log_warning(f"Material '{name}' not found for slot {slot_index}, using fallback.")
        return default_mat

    unreal.log_error(f"Material '{name}' not found and fallback material is invalid.")
    return None

def find_all_static_meshes():
    meshes = []
    assets = unreal.EditorAssetLibrary.list_assets('/Game', recursive=True, include_folder=False)
    for asset_path in assets:
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append(asset)
    return meshes

def load_json_for_mesh(mesh_name):
    json_path = os.path.join(JSON_FOLDER, mesh_name + ".json")
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
        return data
    return None

def get_material_names_from_json(json_data):
    material_names = []
    if isinstance(json_data, list):
        for entry in json_data:
            if isinstance(entry, dict) and entry.get("Type") == "StaticMesh":
                props = entry.get("Properties")
                if isinstance(props, dict):
                    mats = props.get("StaticMaterials", [])
                    for mat in mats:
                        if isinstance(mat, dict):
                            mat_interface = mat.get("MaterialInterface")
                            if isinstance(mat_interface, dict):
                                object_name = mat_interface.get("ObjectName", "")
                                if isinstance(object_name, str) and (
                                    object_name.startswith("Material'") or object_name.startswith("MaterialInstanceConstant'")
                                ):
                                    material_name = object_name.split("'")[1].split(".")[0].split("/")[-1]
                                    material_names.append(material_name)
    return material_names

def main():
    meshes = find_all_static_meshes()
    total_meshes = len(meshes)

    with unreal.ScopedSlowTask(total_meshes, 'Assigning materials to meshes...') as task:
        task.make_dialog(True)

        for i, mesh in enumerate(meshes):
            if task.should_cancel():
                break

            mesh_name = os.path.basename(mesh.get_name())
            remaining = total_meshes - i
            task.enter_progress_frame(1, f"[{remaining} remaining] Processing: {mesh_name}")

            json_data = load_json_for_mesh(mesh_name)
            if not json_data:
                unreal.log_warning(f"Skipping {mesh_name} (no JSON found)")
                continue

            material_names = get_material_names_from_json(json_data)
            if not material_names:
                unreal.log_warning(f"Skipping {mesh_name} (no materials found in JSON)")
                continue

            for idx, material_name in enumerate(material_names):
                material_asset = load_material_by_name(material_name, idx)
                if material_asset:
                    mesh.set_material(idx, material_asset)
                    unreal.EditorAssetLibrary.save_asset(mesh.get_path_name())
                    unreal.log(f"Assigned material '{material_name}' to slot {idx} on '{mesh_name}'")

    unreal.log("Material assignment finished.")

main()
