import os
import sys
import bpy
import gc
import json
import subprocess
import traceback

from blender_uasset_addon.import_uasset import load_uasset
from blender_uasset_addon.export_as_fbx import export_as_fbx
from blender_uasset_addon import bpy_util

# === CONFIGURATION ===
UASSET_DIR = r"H:/depot_747661/fnaf9/Content/Paks/Newfolder/Exports/fnaf9/Content"
UE_VERSION = "4.27"
BATCH_SIZE = 1000
STATE_FILE = "batch_state.json"

# === CLEAN SCENE ===
def clean_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for collection in bpy.data.collections:
        bpy.data.collections.remove(collection)
    for datablocks in (
        bpy.data.meshes, bpy.data.armatures, bpy.data.materials,
        bpy.data.images, bpy.data.textures, bpy.data.objects
    ):
        for block in datablocks:
            if block.users == 0:
                datablocks.remove(block)

# === STATE TRACKING ===
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"processed": []}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

# === FIND ALL UASSETS (skipping RIG and MAT) ===
def get_all_uassets():
    uassets = []
    for root, _, files in os.walk(UASSET_DIR):
        for file in files:
            if file.endswith(".uasset"):
                upper_file = file.upper()
                if "RIG" in upper_file or "MAT" in upper_file:
                    print(f"⏭️ Skipping RIG/MAT file: {file}")
                    continue
                full_path = os.path.join(root, file)
                fbx_path = full_path[:-6] + ".fbx"
                if not os.path.exists(fbx_path):  # Skip already exported
                    uassets.append(full_path)
    return uassets

# === PROCESS SINGLE FILE WITH ERROR SKIP ===
def process_uasset(file_path):
    print(f"🔄 Processing: {file_path}")
    clean_scene()
    try:
        obj, asset_type = load_uasset(file_path, load_textures=False, ue_version=UE_VERSION)
        if not obj:
            print(f"⚠️  Skipping (no object): {file_path}")
            return False
        bpy_util.deselect_all()
        obj.select_set(True)
        armature, meshes = bpy_util.get_selected_armature_and_meshes()
        fbx_path = file_path[:-6] + ".fbx"
        export_as_fbx(fbx_path, armature, meshes)
        print(f"✅ Exported: {fbx_path}")
        return True
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        traceback.print_exc()
        return False
    finally:
        clean_scene()
        gc.collect()

# === MAIN LOGIC ===
def main():
    state = load_state()
    processed = set(state.get("processed", []))
    all_files = [f for f in get_all_uassets() if f not in processed]

    if not all_files:
        print("🎉 All files processed!")
        return

    for file_path in all_files[:BATCH_SIZE]:
        success = process_uasset(file_path)
        if success:
            processed.add(file_path)
        else:
            print(f"⏭️ Skipped due to error: {file_path}")

    state["processed"] = list(processed)
    save_state(state)

    if len(all_files) > BATCH_SIZE:
        print("🔁 Relaunching for next batch...")
        subprocess.Popen([
            sys.executable,
            "--background",
            "--python", os.path.abspath(__file__)
        ])
    else:
        print("✅ Done with all batches.")

main()
