import json
import sys
import os

def geometry_collection_to_feature_collection(geojson_obj):
    """
    Convert a GeoJSON GeometryCollection into a FeatureCollection.
    Each geometry becomes a separate feature with empty properties.
    """
    if not isinstance(geojson_obj, dict):
        raise ValueError("Input must be a GeoJSON object (dict).")

    if geojson_obj.get("type") != "GeometryCollection":
        raise ValueError("GeoJSON object must have type 'GeometryCollection'.")

    geometries = geojson_obj.get("geometries", [])
    if not isinstance(geometries, list):
        raise ValueError("'geometries' must be a list.")

    features = []
    for geom in geometries:
        if not isinstance(geom, dict) or "type" not in geom:
            raise ValueError("Each geometry must be a valid GeoJSON geometry object.")
        features.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {}
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }

def main(input_path, output_path):
    # Validate input file
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read input GeoJSON
    with open(input_path, "r", encoding="utf-8") as infile:
        try:
            geojson_data = json.load(infile)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in input file: {e}")

    # Convert
    feature_collection = geometry_collection_to_feature_collection(geojson_data)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Write output GeoJSON
    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump(feature_collection, outfile, indent=2)

    print(f"✅ Conversion complete. Output saved to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_geojson.py <input_file.geojson> <output_file.geojson>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        main(input_file, output_file)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
