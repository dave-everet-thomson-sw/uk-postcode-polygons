import csv
import json
import sys
import os
from pathlib import Path

def csv_to_geojson(csv_file, output_file, include_inactive=False):
    """
    Convert a postcode CSV file to GeoJSON format.
    Each postcode becomes a Point feature.
    
    Args:
        csv_file: Path to the CSV file
        output_file: Path to the output GeoJSON file
        include_inactive: If True, include postcodes marked as "No" in the In Use column
    """
    
    if not os.path.isfile(csv_file):
        raise FileNotFoundError(f"CSV file not found: {csv_file}")
    
    features = []
    row_count = 0
    skipped_count = 0
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            row_count += 1
            
            # Skip rows without valid coordinates or marked as not in use (unless include_inactive is True)
            in_use = row.get('In Use?', '').strip()
            if not include_inactive and in_use != 'Yes':
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
            
            # Create feature
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "name": postcode,
                    "description": f"{postcode} postcode district",
                    "postcode": postcode,
                    "county": row.get('County', '').strip(),
                    "district": row.get('District', '').strip(),
                    "ward": row.get('Ward', '').strip(),
                    "country": row.get('Country', '').strip(),
                    "in_use": in_use
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
    print(f"   Features created: {len(features)}")
    print(f"   Rows skipped: {skipped_count}")
    print(f"   Include inactive: {include_inactive}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python csv_to_geojson.py <csv_file> [output_file] [--include-inactive]")
        print("\nExample:")
        print('  python csv_to_geojson.py "BT postcodes.csv"')
        print('  python csv_to_geojson.py "BT postcodes.csv" "BT.geojson"')
        print('  python csv_to_geojson.py "BT postcodes.csv" "BT.geojson" --include-inactive')
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Determine output file name
    if len(sys.argv) > 2 and not sys.argv[2].startswith('--'):
        output_file = sys.argv[2]
    else:
        # Default: replace .csv with .geojson
        output_file = str(Path(csv_file).with_suffix('.geojson'))
    
    # Check for --include-inactive flag
    include_inactive = '--include-inactive' in sys.argv
    
    try:
        csv_to_geojson(csv_file, output_file, include_inactive)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
