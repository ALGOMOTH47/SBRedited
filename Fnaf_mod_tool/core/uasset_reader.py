import os

def read_asset_file(path):
    try:
        with open(path, "rb") as f:
            data = f.read()

        actors = []
        if b"Begin Actor" in data:
            name = os.path.splitext(os.path.basename(path))[0]
            actors.append({
                "name": name,
                "transform": {
                    "location": [0.0, 0.0, 0.0],
                    "rotation": [0.0, 0.0, 0.0],
                    "scale": [1.0, 1.0, 1.0]
                }
            })
        return actors
    except Exception as e:
        print(f"Failed to parse {path}: {e}")
        return None
