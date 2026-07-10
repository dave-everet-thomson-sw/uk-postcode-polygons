import csv
import json
import sys
import os
from pathlib import Path
from collections import defaultdict
from scipy.spatial import ConvexHull
import numpy as np

def extract_postcode_district(postcode):
    """
    Extract the district part of a postcode (e.g., 'BT1' from 'BT1 1AA').
    The district is the first 2-3 characters up to (but not including) the space.
    """
    if not postcode:
        return None
    parts = postcode.split()
    if parts:
        return parts[0]
    return None

def create_polygon_from_points(coordinates):
    """
    Create a polygon from a list of [lon, lat] coordinates using ConvexHull.
    Returns a polygon feature with the hull coordinates.
    """
    if len(coordinates) < 3:
        # Not enough points for a proper polygon
        return None
    
    try:
        # Convert to numpy array for ConvexHull calculation
        points = np.array(coordinates)
        
        # ConvexHull needs at least 3 non-collinear points
        if len(points) < 3:
            return None
        
        hull = ConvexHull(points)
        hull_points = points[hull.vertices]
        
        # Convert back to [lon, lat] format and close the polygon
        polygon_coords = [[float(p[0]), float(p[1])] for p in hull_points]
        polygon_coords.append(polygon_coords[0])  # Close the polygon
        
        return polygon_coords
    except Exception as e:
        print(f"Warning: Failed to create hull for {len(coordinates)} points: {e}", file=sys.stderr)
        return None

def csv_to_aggregated_geojson(csv_file, output_file):
    """
    Convert a postcode CSV file to aggregated GeoJSON format.
    Groups postcodes by district (first part) and creates polygon features.
    Only includes active postcodes.
    
    Args:
        csv_file: Path to the CSV file
        output_file: Path to the output GeoJSON file
    """
    
    if not os.path.isfile(csv_file):
        raise FileNotFoundError(f"CSV file not found: {csv_file}")
    
    # Dictionary to store coordinates grouped by postcode district
    postcode_districts = defaultdict(list)
    row_count = 0
    skipped_count = 0
    included_count = 0
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            row_count += 1
            
            # Only process active postcodes
            in_use = row.get('In Use?', '').strip()
            if in_use != 'Yes':
                skipped_count += 1
                continue
            
            postcode = row.get('Postcode', '').strip()
            latitude = row.get('Latitude', '').strip()
            longitude = row.get('Longitude', '').strip()
            
            # Skip if no postcode or coordinates are invalid/missing
            if not postcode or not latitude or not longitude:
                skipped_count += 1
                continue
            
            try:
                lat = float(latitude)
                lon = float(longitude)
                
                # Skip if coordinates are 0,0 (invalid placeholders)
                if lat == 0 and lon == 0:
                    skipped_count += 1
                    continue
                
            except ValueError:
                skipped_count += 1
                continue
            
            # Extract postcode district (e.g., 'BT1' from 'BT1 1AA')
            district = extract_postcode_district(postcode)
            if not district:
                skipped_count += 1
                continue
            
            # Add coordinate to the district's list
            postcode_districts[district].append([lon, lat])
            included_count += 1
    
    # Create features from aggregated districts
    features = []
    failed_districts = []
    
    for district in sorted(postcode_districts.keys()):
        coordinates = postcode_districts[district]
        
        # Create polygon from coordinates
        polygon_coords = create_polygon_from_points(coordinates)
        
        if polygon_coords is None:
            failed_districts.append((district, len(coordinates)))
            continue
        
        # Create feature
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [polygon_coords]
            },
            "properties": {
                "name": district,
                "description": f"{district} postcode district"
            }
        }
        
        features.append(feature)
    
    # Create FeatureCollection
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    
    # Write output GeoJSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, indent=2)
    
    print(f"✅ Conversion complete!")
    print(f"   Input file: {csv_file}")
    print(f"   Output file: {output_file}")
    print(f"   Total rows processed: {row_count}")
    print(f"   Active postcodes included: {included_count}")
    print(f"   Postcode districts created: {len(features)}")
    print(f"   Rows skipped: {skipped_count}")
    
    if failed_districts:
        print(f"\n   ⚠️  Districts that failed (< 3 points):")
        for district, count in failed_districts:
            print(f"      {district}: {count} points")

def main():
    if len(sys.argv) < 2:
        print("Usage: python csv_to_aggregated_geojson.py <csv_file> [output_file]")
        print("\nExample:")
        print('  python csv_to_aggregated_geojson.py "BT postcodes.csv"')
        print('  python csv_to_aggregated_geojson.py "BT postcodes.csv" "BT_aggregated.geojson"')
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Determine output file name
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        # Default: replace .csv with .geojson
        output_file = str(Path(csv_file).with_suffix('.geojson'))
    
    try:
        csv_to_aggregated_geojson(csv_file, output_file)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
