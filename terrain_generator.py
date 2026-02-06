#!/usr/bin/env python3
"""
Terrain Generator using Wave Function Collapse (WFC) with multi-planet
topography-inspired profiles. Outputs a 1:1 scale OBJ mesh.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class PlanetProfile:
    name: str
    mean: float
    stdev: float
    roughness: float
    weight: float


@dataclass(frozen=True)
class TileType:
    name: str
    height_range: Tuple[float, float]
    allowed_neighbors: Sequence[str]
    weight: float


PLANET_PROFILES: List[PlanetProfile] = [
    PlanetProfile(name="Earth", mean=200.0, stdev=1200.0, roughness=0.6, weight=1.0),
    PlanetProfile(name="Mars", mean=-800.0, stdev=2500.0, roughness=0.7, weight=0.9),
    PlanetProfile(name="Moon", mean=0.0, stdev=1700.0, roughness=0.8, weight=0.7),
    PlanetProfile(name="Venus", mean=0.0, stdev=1100.0, roughness=0.5, weight=0.6),
    PlanetProfile(name="Mercury", mean=100.0, stdev=2000.0, roughness=0.9, weight=0.6),
    PlanetProfile(name="Europa", mean=-300.0, stdev=800.0, roughness=0.4, weight=0.5),
    PlanetProfile(name="Titan", mean=-500.0, stdev=900.0, roughness=0.4, weight=0.5),
]

TILE_TYPES: Dict[str, TileType] = {
    "ocean": TileType(
        name="ocean",
        height_range=(-6000.0, -200.0),
        allowed_neighbors=("ocean", "shore", "lowland"),
        weight=1.0,
    ),
    "shore": TileType(
        name="shore",
        height_range=(-200.0, 50.0),
        allowed_neighbors=("ocean", "shore", "lowland"),
        weight=1.1,
    ),
    "lowland": TileType(
        name="lowland",
        height_range=(0.0, 800.0),
        allowed_neighbors=("shore", "lowland", "highland"),
        weight=1.4,
    ),
    "highland": TileType(
        name="highland",
        height_range=(400.0, 2000.0),
        allowed_neighbors=("lowland", "highland", "mountain"),
        weight=1.0,
    ),
    "mountain": TileType(
        name="mountain",
        height_range=(1500.0, 6500.0),
        allowed_neighbors=("highland", "mountain", "polar"),
        weight=0.7,
    ),
    "polar": TileType(
        name="polar",
        height_range=(0.0, 3000.0),
        allowed_neighbors=("ocean", "shore", "lowland", "highland", "mountain", "polar"),
        weight=0.4,
    ),
}


def _weighted_choice(rng: random.Random, items: Sequence[Tuple[str, float]]) -> str:
    total = sum(weight for _, weight in items)
    pick = rng.uniform(0.0, total)
    current = 0.0
    for name, weight in items:
        current += weight
        if current >= pick:
            return name
    return items[-1][0]


def _planet_sample(rng: random.Random, profiles: Sequence[PlanetProfile]) -> float:
    weights = [profile.weight for profile in profiles]
    total = sum(weights)
    pick = rng.uniform(0.0, total)
    current = 0.0
    selected = profiles[-1]
    for profile in profiles:
        current += profile.weight
        if current >= pick:
            selected = profile
            break
    base = rng.gauss(selected.mean, selected.stdev)
    rough = rng.gauss(0.0, selected.stdev * selected.roughness)
    return base + rough


def _initial_tile_weights(rng: random.Random, planet_profiles: Sequence[PlanetProfile]) -> Dict[str, float]:
    weights = {}
    for tile_name, tile in TILE_TYPES.items():
        samples = [_planet_sample(rng, planet_profiles) for _ in range(30)]
        matches = sum(
            1 for sample in samples if tile.height_range[0] <= sample <= tile.height_range[1]
        )
        weights[tile_name] = tile.weight * max(0.05, matches / len(samples))
    return weights


def _neighbors(x: int, y: int, width: int, height: int) -> Iterable[Tuple[int, int]]:
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height:
            yield nx, ny


def wave_function_collapse(
    width: int,
    height: int,
    rng: random.Random,
    planet_profiles: Sequence[PlanetProfile],
) -> List[List[str]]:
    tile_weights = _initial_tile_weights(rng, planet_profiles)
    grid: List[List[set[str]]] = [
        [set(TILE_TYPES.keys()) for _ in range(width)] for _ in range(height)
    ]

    def entropy(cell: set[str]) -> float:
        if len(cell) <= 1:
            return 0.0
        weights = [tile_weights[name] for name in cell]
        total = sum(weights)
        return -sum((w / total) * math.log(w / total) for w in weights if w > 0)

    while True:
        candidates: List[Tuple[int, int, float]] = []
        for y in range(height):
            for x in range(width):
                if len(grid[y][x]) > 1:
                    candidates.append((x, y, entropy(grid[y][x])))
        if not candidates:
            break
        min_entropy = min(item[2] for item in candidates)
        low_entropy = [item for item in candidates if item[2] == min_entropy]
        x, y, _ = rng.choice(low_entropy)
        options = grid[y][x]
        choice = _weighted_choice(rng, [(name, tile_weights[name]) for name in options])
        grid[y][x] = {choice}

        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            current_options = grid[cy][cx]
            allowed = set()
            for option in current_options:
                allowed.update(TILE_TYPES[option].allowed_neighbors)
            for nx, ny in _neighbors(cx, cy, width, height):
                before = set(grid[ny][nx])
                after = before & allowed
                if after != before and after:
                    grid[ny][nx] = after
                    stack.append((nx, ny))

    return [[next(iter(cell)) for cell in row] for row in grid]


def _temperature_at(lat_norm: float, elevation: float) -> float:
    base_temp = 1.0 - abs(lat_norm)
    lapse = max(0.0, 1.0 - elevation / 8000.0)
    return base_temp * lapse


def _moisture_at(rng: random.Random, distance_to_ocean: float) -> float:
    base = rng.uniform(0.0, 1.0)
    ocean_bonus = max(0.0, 1.0 - distance_to_ocean / 12.0)
    return min(1.0, 0.6 * base + 0.4 * ocean_bonus)


def _biome(temperature: float, moisture: float, elevation: float) -> str:
    if elevation > 3500 or temperature < 0.15:
        return "alpine"
    if temperature < 0.3 and moisture < 0.35:
        return "tundra"
    if temperature < 0.4 and moisture >= 0.35:
        return "taiga"
    if temperature > 0.65 and moisture < 0.35:
        return "desert"
    if temperature > 0.65 and moisture >= 0.35:
        return "rainforest"
    if moisture >= 0.5:
        return "forest"
    return "grassland"


def _distance_to_ocean(tiles: List[List[str]], x: int, y: int) -> float:
    if tiles[y][x] == "ocean":
        return 0.0
    max_radius = 10
    for radius in range(1, max_radius + 1):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < len(tiles[0]) and 0 <= ny < len(tiles):
                    if tiles[ny][nx] == "ocean":
                        return math.hypot(dx, dy)
    return float(max_radius)


def generate_heightfield(
    tiles: List[List[str]],
    rng: random.Random,
    planet_profiles: Sequence[PlanetProfile],
) -> List[List[float]]:
    height = len(tiles)
    width = len(tiles[0])
    heights: List[List[float]] = [[0.0 for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            tile = TILE_TYPES[tiles[y][x]]
            sample = _planet_sample(rng, planet_profiles)
            min_h, max_h = tile.height_range
            heights[y][x] = max(min(sample, max_h), min_h)
    return heights


def assign_biomes(
    tiles: List[List[str]],
    heights: List[List[float]],
    rng: random.Random,
) -> List[List[str]]:
    height = len(tiles)
    width = len(tiles[0])
    biomes: List[List[str]] = [["" for _ in range(width)] for _ in range(height)]
    for y in range(height):
        lat_norm = (y / (height - 1)) * 2.0 - 1.0
        for x in range(width):
            elevation = heights[y][x]
            temp = _temperature_at(lat_norm, elevation)
            distance = _distance_to_ocean(tiles, x, y)
            moisture = _moisture_at(rng, distance)
            biomes[y][x] = _biome(temp, moisture, elevation)
    return biomes


def export_obj(
    heights: List[List[float]],
    scale: float,
    output_path: str,
) -> None:
    height = len(heights)
    width = len(heights[0])
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write("# Terrain OBJ\n")
        for y in range(height):
            for x in range(width):
                z = heights[y][x]
                handle.write(f"v {x * scale:.3f} {y * scale:.3f} {z:.3f}\n")
        for y in range(height - 1):
            for x in range(width - 1):
                v1 = y * width + x + 1
                v2 = v1 + 1
                v3 = v1 + width
                v4 = v3 + 1
                handle.write(f"f {v1} {v2} {v4}\n")
                handle.write(f"f {v1} {v4} {v3}\n")


def write_metadata(
    path: str,
    tiles: List[List[str]],
    heights: List[List[float]],
    biomes: List[List[str]],
) -> None:
    data = {
        "width": len(tiles[0]),
        "height": len(tiles),
        "tiles": tiles,
        "heights": heights,
        "biomes": biomes,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WFC terrain generator")
    parser.add_argument("--width", type=int, default=128)
    parser.add_argument("--height", type=int, default=128)
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--output", type=str, default="terrain.obj")
    parser.add_argument("--metadata", type=str, default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    tiles = wave_function_collapse(args.width, args.height, rng, PLANET_PROFILES)
    heights = generate_heightfield(tiles, rng, PLANET_PROFILES)
    biomes = assign_biomes(tiles, heights, rng)
    export_obj(heights, args.scale, args.output)
    if args.metadata:
        write_metadata(args.metadata, tiles, heights, biomes)
    print(f"Generated {args.output} ({args.width}x{args.height})")


if __name__ == "__main__":
    main()
