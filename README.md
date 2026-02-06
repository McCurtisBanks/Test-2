# Terrain Generator (Wave Function Collapse + Biome Planning)

This project provides a Python-based terrain generator that uses a Wave Function Collapse (WFC) tile solver to produce a **1:1 scale** heightfield and exports it as a 3D **OBJ** model ready for import into Unreal Engine. The system blends multiple synthetic "planetary topography profiles" (Earth, Mars, Moon, Venus, Mercury, Europa, Titan) to seed height distributions and then assigns biomes and climates from elevation, latitude, and moisture.

> **Note on planetary data**: In this environment, live access to public topography datasets is not available. Instead, the generator encodes **approximate** elevation distributions and roughness profiles per planet to approximate the influence of multiple worlds. Replace these profiles with real datasets if you have them locally.

## Features
- Wave Function Collapse for tile-based terrain assembly.
- Multi-planet topography-inspired height distributions.
- Biome and climate classification (tundra, desert, forest, etc.).
- 1:1 scale mesh output (`OBJ`) suitable for Unreal Engine.
- Deterministic generation via random seed.

## Usage
```bash
python terrain_generator.py \
  --width 256 \
  --height 256 \
  --scale 1.0 \
  --seed 42 \
  --output terrain.obj
```

### Key options
- `--width`, `--height`: grid size in meters (1 unit = 1 meter).
- `--scale`: meters per grid cell (default 1.0). Keep at 1.0 for 1:1 scale.
- `--output`: OBJ file path.
- `--metadata`: optional JSON metadata path.

## Unreal Engine import tips
1. Import the OBJ.
2. Ensure **unit scale = centimeters** in Unreal. Since 1 unit = 1 meter in the OBJ, use a scale factor of 100 for centimeters.
3. For landscapes, consider converting the height data into a heightmap if desired.

## Biome and climate plan
The generator follows this plan:
1. **Elevation classes** from WFC tiles: ocean, shore, lowland, highland, mountain, polar.
2. **Temperature** is computed using:
   - Latitude (cold at poles, warm at equator).
   - Elevation lapse rate (temperature drop with altitude).
3. **Moisture** is derived from a noise-like field plus proximity to oceans.
4. **Biome assignment**:
   - Warm + wet = rainforest
   - Warm + dry = desert
   - Temperate + wet = forest
   - Temperate + dry = grassland
   - Cold + wet = taiga
   - Cold + dry = tundra
   - Very cold + high elevation = alpine/polar

## Replacing planetary profiles
If you have real planetary height datasets:
1. Load the dataset into the `PLANET_PROFILES` list in `terrain_generator.py`.
2. Replace the synthetic `mean`, `stdev`, and `roughness` values with statistics derived from the dataset.
3. Optionally feed per-cell samples into the WFC tile weights.

---
**License**: MIT
