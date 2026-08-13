#!/usr/bin/env python3
"""
Generate and save OpenAPI schema to file.

Usage:
    python generate_openapi.py
"""

import json
import os
import sys
from pathlib import Path

# Fix encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from main import app

def generate_openapi_schema():
    """Generate OpenAPI schema from FastAPI app"""
    print("Generating OpenAPI schema...")
    
    # Get the OpenAPI schema
    schema = app.openapi()
    
    # Save to file
    output_file = Path(__file__).parent / "openapi.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Schema saved to: {output_file}")
    
    # Print summary
    print("\nSchema Summary:")
    print(f"  Title: {schema['info']['title']}")
    print(f"  Version: {schema['info']['version']}")
    print(f"  Paths: {len(schema['paths'])}")
    print(f"  Tags: {len(schema['tags'])}")
    print(f"  Components: {len(schema.get('components', {}).get('schemas', {}))}")
    
    # Print all paths
    print("\nAvailable Endpoints:")
    for path in sorted(schema['paths'].keys()):
        methods = list(schema['paths'][path].keys())
        print(f"  {path}: {', '.join(m.upper() for m in methods)}")
    
    return schema

if __name__ == "__main__":
    try:
        schema = generate_openapi_schema()
        print("\nOpenAPI schema generation complete!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
