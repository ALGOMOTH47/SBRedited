import unreal
import os
import json

# Set your folder where the JSON files are located
JSON_FOLDER = r"H:\f\Fnaf_mod_tool\fnaf9\Content\json\other"

# Helper: Load a material by its short name
def load_material_by_name(name, slot_index=0):
    assets = unreal.EditorAssetLibrary.list_assets('/Game', recursive=True, include_folder=False)
    for asset_path in assets:
        if asset_path.endswith(name) or asset_path.endswith(name + '.' + name):
            asset = unreal.EditorAssetLibrary.load_asset(asset_path)
            if isinstance(asset, unreal.MaterialInterface):
                return asset
    unreal.log_warning(f"Material '{name}' for slot {slot_index} not found.")
    return None

# Step 1: Find all StaticMeshes
def find_all_static_meshes():
    meshes = []
    assets = unreal.EditorAssetLibrary.list_assets('/Game', recursive=True, include_folder=False)
    for asset_path in assets:
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append(asset)
    return meshes

# Step 2: Load JSON for given mesh name
def load_json_for_mesh(mesh_name):
    json_path = os.path.join(JSON_FOLDER, mesh_name + ".json")
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            data = json.load(f)
        return data
    return None

# Step 3: Find material names from JSON
def get_material_names_from_json(json_data):
    material_names = []
    if isinstance(json_data, list):
        for entry in json_data:
            if entry.get("Type") == "StaticMesh":
                props = entry.get("Properties", {})
                mats = props.get("StaticMaterials", [])
                for mat in mats:
                    mat_interface = mat.get("MaterialInterface")
                    if not mat_interface:
                        continue
                    object_name = mat_interface.get("ObjectName", "")
                    if object_name.startswith("Material'") or object_name.startswith("MaterialInstanceConstant'"):
                        material_name = object_name.split("'")[1].split(".")[0].split("/")[-1]
                        material_names.append(material_name)
    return material_names

# Main function
def main():
    meshes = find_all_static_meshes()
    total_meshes = len(meshes)

    with unreal.ScopedSlowTask(total_meshes, 'Assigning materials to meshes...') as task:
        task.make_dialog(True)  # Show cancel button

        for i, mesh in enumerate(meshes):
            if task.should_cancel():
                break  # User pressed cancel button

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

            # Assign materials
            for idx, material_name in enumerate(material_names):
                material_asset = load_material_by_name(material_name, idx)
                if material_asset:
                    mesh.set_material(idx, material_asset)
                    unreal.EditorAssetLibrary.save_asset(mesh.get_path_name())
                    unreal.log(f"Assigned material '{material_name}' to slot {idx} on '{mesh_name}'")
                else:
                    unreal.log_warning(f"Material '{material_name}' not found for {mesh_name}")

    unreal.log("Material assignment finished.")

# Execute the script
main()
