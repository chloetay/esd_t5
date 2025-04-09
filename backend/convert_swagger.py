import yaml
import json
from pathlib import Path

def convert_swagger_file(yaml_path):
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    output_path = yaml_path.with_name("apispec.json")
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Converted: {yaml_path} → {output_path}")

def main():
    base_dir = Path(__file__).parent  # current folder: backend/
    for yaml_file in base_dir.rglob("swagger.yaml"):
        convert_swagger_file(yaml_file)

if __name__ == "__main__":
    main()
