#!/usr/bin/env python3
"""
create_ponds_world.py  –  Generates ponds_world for Anglers Retreat.

Builds a void world containing a tropical fishing dock and bait shack hub
island centred at x=500, z=0, y=64 to match existing plugin data.
Fisherman Joe's position (x=510, z=3, y=65) stays in CustomNPCs/config.yml.

Requirements:
    pip install nbtlib

Usage (run from server root):
    python create_ponds_world.py
"""

import io, math, os, struct, time, zlib
import nbtlib
from nbtlib import tag

WORLD_DIR    = "ponds_world"
DATA_VERSION = 4082   # Minecraft 1.21.1
SEED         = 0

# Island centre / surface elevation
IX, IZ = 500, 0
IY     = 64


# ─── Block state helpers ──────────────────────────────────────────────────────

def bs(name: str, **props) -> dict:
    return {"n": name, "p": props}

# Terrain
AIR           = bs("minecraft:air")
SAND          = bs("minecraft:sand")
GRAVEL        = bs("minecraft:gravel")
COARSE_DIRT   = bs("minecraft:coarse_dirt")
WATER         = bs("minecraft:water", level="0")

# Wood / structure
OAK_PLANKS      = bs("minecraft:oak_planks")
DARK_OAK_PLANKS = bs("minecraft:dark_oak_planks")
OAK_LOG         = bs("minecraft:oak_log", axis="y")
JUNGLE_LOG      = bs("minecraft:jungle_log", axis="y")
JUNGLE_LEAVES   = bs("minecraft:jungle_leaves", distance="1", persistent="true", waterlogged="false")
BAMBOO_PLANKS   = bs("minecraft:bamboo_planks")
BAMBOO_MOSAIC   = bs("minecraft:bamboo_mosaic")
BAMBOO_BLOCK    = bs("minecraft:bamboo_block", axis="y")
STRIPPED_BAMBOO = bs("minecraft:stripped_bamboo_block", axis="y")

# Furniture / decoration
LANTERN       = bs("minecraft:lantern", hanging="false", waterlogged="false")
HANG_LANTERN  = bs("minecraft:lantern", hanging="true",  waterlogged="false")
BARREL_UP     = bs("minecraft:barrel", facing="up", open="false")
CRAFTING_TABLE = bs("minecraft:crafting_table")
CHEST_S       = bs("minecraft:chest", facing="south", type="single", waterlogged="false")
LILY_PAD      = bs("minecraft:lily_pad")
SUGAR_CANE    = bs("minecraft:sugar_cane")
FERN          = bs("minecraft:fern")
SEA_GRASS     = bs("minecraft:seagrass")


def oak_fence(n="false", s="false", e="false", w="false"):
    return bs("minecraft:oak_fence", north=n, south=s, east=e, west=w, waterlogged="false")

def bamboo_stair(facing, half="bottom"):
    return bs("minecraft:bamboo_stairs", facing=facing, half=half, shape="straight", waterlogged="false")

def bamboo_slab(t="bottom"):
    return bs("minecraft:bamboo_slab", type=t, waterlogged="false")

def oak_trapdoor(facing="east"):
    return bs("minecraft:oak_trapdoor", facing=facing, open="true", half="bottom",
               powered="false", waterlogged="false")


# ─── Island design ────────────────────────────────────────────────────────────

def design_island() -> dict:
    """Returns {(x, y, z): block_dict} for the tropical fishing hub island."""
    blocks: dict = {}

    def place(x, y, z, blk):
        blocks[(x, y, z)] = blk

    def fill(x1, y1, z1, x2, y2, z2, blk):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            for y in range(min(y1, y2), max(y1, y2) + 1):
                for z in range(min(z1, z2), max(z1, z2) + 1):
                    blocks[(x, y, z)] = blk

    cx, cz = IX, IZ
    sy = IY

    # ── Sandy oval island base (4 blocks deep) ────────────────────────────────
    rx, rz = 19, 11  # semi-axes
    for x in range(cx - rx - 1, cx + rx + 2):
        for z in range(cz - rz - 1, cz + rz + 2):
            if math.sqrt(((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2) <= 1.0:
                fill(x, sy - 4, z, x, sy, z, SAND)

    # Texture: scatter gravel and coarse dirt on surface
    for dx, dz in [(7, -8), (-5, 7), (13, 5), (-9, -4), (15, -7)]:
        if (cx + dx, sy, cz + dz) in blocks:
            place(cx + dx, sy, cz + dz, GRAVEL)
    for dx, dz in [(4, -9), (-7, 6), (10, 8), (-12, -2)]:
        if (cx + dx, sy, cz + dz) in blocks:
            place(cx + dx, sy, cz + dz, COARSE_DIRT)

    # ── Fishing pond (self-contained, east of island) ─────────────────────────
    px1, px2 = cx + 12, cx + 30
    pz1, pz2 = cz - 7, cz + 7
    pb = sy - 3   # pond bottom

    fill(px1, pb, pz1, px2, pb, pz2, SAND)          # sandy bottom
    for y in range(pb + 1, sy):                       # containment walls
        fill(px1, y, pz1, px1, y, pz2, SAND)
        fill(px2, y, pz1, px2, y, pz2, SAND)
        fill(px1, y, pz1, px2, y, pz1, SAND)
        fill(px1, y, pz2, px2, y, pz2, SAND)
    fill(px1 + 1, pb + 1, pz1 + 1, px2 - 1, sy - 1, pz2 - 1, WATER)   # water body

    # ── Fishing dock ──────────────────────────────────────────────────────────
    # Oak plank pier running east from island edge to pond edge
    fill(cx + 7, sy, cz - 2, cx + 25, sy, cz + 2, OAK_PLANKS)
    for x in range(cx + 7, cx + 26, 3):                        # dark oak accent strips
        fill(x, sy, cz - 2, x, sy, cz + 2, DARK_OAK_PLANKS)

    # Support posts going down into pond
    for dx in [10, 14, 18, 22]:
        for y in range(sy - 2, sy):
            place(cx + dx, y, cz - 2, OAK_LOG)
            place(cx + dx, y, cz + 2, OAK_LOG)

    # Side railings
    for dx in range(7, 26):
        e = "true" if dx < 25 else "false"
        w = "true" if dx > 7  else "false"
        place(cx + dx, sy + 1, cz - 2, oak_fence(e=e, w=w))
        place(cx + dx, sy + 1, cz + 2, oak_fence(e=e, w=w))
    for dz in range(-2, 3):
        n = "true" if dz > -2 else "false"
        s = "true" if dz < 2  else "false"
        place(cx + 25, sy + 1, cz + dz, oak_fence(n=n, s=s))

    # Lanterns on railing (replace fence at those positions)
    for dx in [9, 15, 21]:
        place(cx + dx, sy + 1, cz - 2, LANTERN)
        place(cx + dx, sy + 1, cz + 2, LANTERN)

    # Barrel + open trapdoors at dock tip
    place(cx + 24, sy + 1, cz, BARREL_UP)
    for dz in [-1, 0, 1]:
        place(cx + 25, sy, cz + dz, oak_trapdoor("east"))

    # ── Bait Shack ────────────────────────────────────────────────────────────
    # West end of island:  x = cx-17 to cx-5,  z = cz-5 to cz+5
    sx1, sx2 = cx - 17, cx - 5
    sz1, sz2 = cz - 5,  cz + 5

    fill(sx1, sy,     sz1, sx2, sy,     sz2, BAMBOO_PLANKS)   # raised foundation
    fill(sx1, sy + 1, sz1, sx2, sy + 1, sz2, BAMBOO_MOSAIC)   # floor

    # Walls
    fill(sx1, sy + 2, sz1, sx2, sy + 4, sz1, BAMBOO_BLOCK)    # north
    fill(sx1, sy + 2, sz2, sx2, sy + 4, sz2, BAMBOO_BLOCK)    # south
    fill(sx1, sy + 2, sz1, sx1, sy + 4, sz2, BAMBOO_BLOCK)    # west
    fill(sx2, sy + 2, sz1, sx2, sy + 4, sz2, STRIPPED_BAMBOO) # east (counter side)

    # Open the east face (service counter opening)
    for z in range(sz1 + 1, sz2):
        blocks.pop((sx2, sy + 2, z), None)
        blocks.pop((sx2, sy + 3, z), None)
        blocks.pop((sx2, sy + 4, z), None)
    # Counter slab ledge
    fill(sx2, sy + 3, sz1 + 1, sx2, sy + 3, sz2 - 1, bamboo_slab("top"))

    # Ceiling
    fill(sx1, sy + 5, sz1, sx2, sy + 5, sz2, BAMBOO_PLANKS)

    # Pitched bamboo roof + ridge
    for x in range(sx1, sx2 + 1):
        place(x, sy + 6, sz1, bamboo_stair("north"))
        place(x, sy + 6, sz2, bamboo_stair("south"))
        for z in range(sz1 + 1, sz2):
            place(x, sy + 6, z, bamboo_slab())
        place(x, sy + 7, cz, bamboo_slab())

    # Interior furniture
    place(sx1 + 1, sy + 2, cz - 2, BARREL_UP)
    place(sx1 + 2, sy + 2, cz - 2, BARREL_UP)
    place(sx1 + 1, sy + 2, cz,     CRAFTING_TABLE)
    place(sx1 + 1, sy + 2, cz + 2, CHEST_S)
    place(sx1 + 5, sy + 5, cz,     HANG_LANTERN)
    place(sx1 + 3, sy + 5, sz1 + 1, HANG_LANTERN)
    place(sx1 + 3, sy + 5, sz2 - 1, HANG_LANTERN)

    # Lantern post just outside the shack
    place(sx2 + 1, sy + 1, cz, OAK_LOG)
    place(sx2 + 1, sy + 2, cz, OAK_LOG)
    place(sx2 + 1, sy + 3, cz, LANTERN)

    # ── Palm trees ────────────────────────────────────────────────────────────
    def palm(px, pz, h=5):
        if (px, sy, pz) not in blocks:
            return
        for y in range(sy, sy + h):
            place(px, y, pz, JUNGLE_LOG)
        top = sy + h
        for ldx, ldz in [(-2,0),(2,0),(0,-2),(0,2),(-1,1),(1,1),(-1,-1),(1,-1),
                          (-1,0),(1,0),(0,-1),(0,1),(0,0)]:
            place(px + ldx, top, pz + ldz, JUNGLE_LEAVES)
        for ldx, ldz in [(-1,0),(1,0),(0,-1),(0,1),(0,0)]:
            place(px + ldx, top + 1, pz + ldz, JUNGLE_LEAVES)

    for px, pz, h in [
        (cx - 14, cz - 9, 6),
        (cx - 13, cz + 9, 5),
        (cx + 4,  cz - 10, 7),
        (cx + 6,  cz + 10, 6),
        (cx - 5,  cz - 10, 5),
        (cx + 16, cz - 7,  5),
    ]:
        palm(px, pz, h)

    # ── Sugar cane at pond edge ────────────────────────────────────────────────
    for dx, dz in [(8, -4), (8, 4), (9, -5), (9, 5)]:
        if (cx + dx, sy, cz + dz) in blocks:
            place(cx + dx, sy + 1, cz + dz, SUGAR_CANE)
            place(cx + dx, sy + 2, cz + dz, SUGAR_CANE)

    # ── Lily pads on pond surface ─────────────────────────────────────────────
    for dx, dz in [(14, -5), (17, 4), (19, -3), (22, 6), (25, -5), (16, 0)]:
        if (cx + dx, sy - 1, cz + dz) in blocks:   # water present below
            place(cx + dx, sy, cz + dz, LILY_PAD)

    # ── Seagrass in pond ──────────────────────────────────────────────────────
    for dx, dz in [(15, -2), (16, 3), (18, -5), (21, 1), (24, -6)]:
        if (cx + dx, sy - 2, cz + dz) in blocks:
            place(cx + dx, sy - 1, cz + dz, SEA_GRASS)

    # ── Island ferns ─────────────────────────────────────────────────────────
    for dx, dz in [(3, -8), (-5, 6), (-8, -5), (0, -9), (-11, 0)]:
        if (cx + dx, sy, cz + dz) in blocks:
            place(cx + dx, sy + 1, cz + dz, FERN)

    return blocks


# ─── NBT helpers ─────────────────────────────────────────────────────────────

def make_bs_nbt(blk: dict) -> tag.Compound:
    """Convert block state dict to nbtlib Compound."""
    props = blk.get("p", {})
    if props:
        return tag.Compound({
            "Name": tag.String(blk["n"]),
            "Properties": tag.Compound({k: tag.String(v) for k, v in props.items()})
        })
    return tag.Compound({"Name": tag.String(blk["n"])})


def pack_indices(indices: list, palette_size: int) -> tag.LongArray:
    """Pack 4096 block indices into a LongArray (MC 1.16+ no-cross-boundary format)."""
    bits    = max(4, math.ceil(math.log2(max(palette_size, 2))))
    vplong  = 64 // bits
    n_longs = math.ceil(4096 / vplong)
    longs   = [0] * n_longs
    for i, v in enumerate(indices):
        li = i // vplong
        bi = (i % vplong) * bits
        longs[li] |= (v & ((1 << bits) - 1)) << bi
    # Convert to signed 64-bit
    result = [(l - (1 << 64) if l >= (1 << 63) else l) for l in longs]
    return tag.LongArray(result)


def build_chunk_nbt(cx: int, cz: int, all_blocks: dict) -> dict:
    """Return dict for nbtlib.File() representing one chunk."""
    # Collect blocks local to this chunk
    chunk_blocks = {}
    for (bx, by, bz), blk in all_blocks.items():
        if (bx >> 4) == cx and (bz >> 4) == cz:
            chunk_blocks[(bx & 15, by, bz & 15)] = blk  # (lx, y, lz)

    # Group into 16-tall sections
    sec_map: dict = {}
    for (lx, by, lz), blk in chunk_blocks.items():
        sy  = by >> 4
        ly  = by & 15
        sec_map.setdefault(sy, {})[(lx, ly, lz)] = blk

    sections = []
    for sy_idx in sorted(sec_map.keys()):
        sec_blocks = sec_map[sy_idx]
        palette    = [AIR]
        pmap       = {AIR["n"] + str(AIR["p"]): 0}
        indices    = [0] * 4096   # index = ly*256 + lz*16 + lx

        for (lx, ly, lz), blk in sec_blocks.items():
            key = blk["n"] + str(blk["p"])
            if key not in pmap:
                pmap[key] = len(palette)
                palette.append(blk)
            indices[ly * 256 + lz * 16 + lx] = pmap[key]

        pal_nbt = tag.List[tag.Compound]([make_bs_nbt(b) for b in palette])
        if len(palette) == 1:
            bs_nbt = tag.Compound({"palette": pal_nbt})
        else:
            bs_nbt = tag.Compound({"palette": pal_nbt,
                                   "data":    pack_indices(indices, len(palette))})

        sections.append(tag.Compound({
            "Y":            tag.Byte(sy_idx),
            "block_states": bs_nbt,
            "biomes":       tag.Compound({
                "palette": tag.List[tag.String]([tag.String("minecraft:beach")])
            })
        }))

    hm = tag.LongArray([0] * 37)  # heightmaps – server recalculates on load
    return {
        "DataVersion":   tag.Int(DATA_VERSION),
        "xPos":          tag.Int(cx),
        "zPos":          tag.Int(cz),
        "yPos":          tag.Int(-4),
        "Status":        tag.String("minecraft:full"),
        "LastUpdate":    tag.Long(0),
        "sections":      tag.List[tag.Compound](sections) if sections else tag.List[tag.Compound]([]),
        "block_entities": tag.List[tag.Compound]([]),
        "fluid_ticks":   tag.List[tag.Compound]([]),
        "block_ticks":   tag.List[tag.Compound]([]),
        "InhabitedTime": tag.Long(0),
        "PostProcessing": tag.List[tag.List]([]),
        "Heightmaps":    tag.Compound({
            "MOTION_BLOCKING":          hm,
            "MOTION_BLOCKING_NO_LEAVES": hm,
            "OCEAN_FLOOR":              hm,
            "WORLD_SURFACE":            hm,
        }),
        "structures": tag.Compound({
            "References": tag.Compound({}),
            "starts":     tag.Compound({})
        })
    }


# ─── Region file writer ───────────────────────────────────────────────────────

def chunk_to_bytes(chunk_dict: dict) -> bytes:
    """Serialize chunk NBT to raw (non-gzipped) bytes."""
    f   = nbtlib.File(chunk_dict)
    buf = io.BytesIO()
    f.write(buf, byteorder="big", gzipped=False)
    return buf.getvalue()


def write_region(rx: int, rz: int, chunk_coords: list, all_blocks: dict, out_dir: str):
    path = os.path.join(out_dir, "region", f"r.{rx}.{rz}.mca")
    ts   = int(time.time())

    payloads:      dict = {}
    sec_offsets:   dict = {}
    sec_sizes:     dict = {}
    current_sector = 2  # sectors 0+1 = header

    for (cx, cz) in chunk_coords:
        lcx = cx & 31
        lcz = cz & 31
        raw        = chunk_to_bytes(build_chunk_nbt(cx, cz, all_blocks))
        compressed = zlib.compress(raw)
        # Chunk entry: 4-byte big-endian length, 1-byte compression type, data
        payload = struct.pack(">I", len(compressed) + 1) + b'\x02' + compressed
        # Pad to 4096-byte sector boundary
        pad      = (4096 - len(payload) % 4096) % 4096
        payload += b'\x00' * pad
        n_sec    = len(payload) // 4096

        payloads[(lcx, lcz)]    = payload
        sec_offsets[(lcx, lcz)] = current_sector
        sec_sizes[(lcx, lcz)]   = n_sec
        current_sector += n_sec

    # 8 KiB header (location table + timestamp table)
    loc_table = bytearray(4096)
    ts_table  = bytearray(4096)
    for (lcx, lcz) in payloads:
        idx = lcx + lcz * 32
        off = sec_offsets[(lcx, lcz)]
        sz  = sec_sizes[(lcx, lcz)]
        loc_table[idx * 4]     = (off >> 16) & 0xFF
        loc_table[idx * 4 + 1] = (off >> 8)  & 0xFF
        loc_table[idx * 4 + 2] =  off         & 0xFF
        loc_table[idx * 4 + 3] =  sz          & 0xFF
        struct.pack_into(">I", ts_table, idx * 4, ts)

    with open(path, "wb") as f:
        f.write(loc_table)
        f.write(ts_table)
        for key in sorted(payloads):
            f.write(payloads[key])

    print(f"  Written {path}  ({len(payloads)} chunks)")


# ─── level.dat ───────────────────────────────────────────────────────────────

def write_level_dat(out_dir: str):
    """Create a void-flat level.dat."""
    level = nbtlib.File({
        "Data": tag.Compound({
            "DataVersion":     tag.Int(DATA_VERSION),
            "version":         tag.Int(19133),
            "Version": tag.Compound({
                "Id":       tag.Int(DATA_VERSION),
                "Name":     tag.String("1.21.1"),
                "Series":   tag.String("main"),
                "Snapshot": tag.Byte(0)
            }),
            "LevelName":       tag.String("ponds_world"),
            "GameType":        tag.Int(0),   # survival
            "Difficulty":      tag.Byte(1),  # easy
            "DifficultyLocked": tag.Byte(0),
            "allowCommands":   tag.Byte(1),
            "hardcore":        tag.Byte(0),
            "initialized":     tag.Byte(1),
            "Time":            tag.Long(0),
            "DayTime":         tag.Long(6000),
            "LastPlayed":      tag.Long(int(time.time() * 1000)),
            "SpawnX":          tag.Int(IX),
            "SpawnY":          tag.Int(IY + 1),
            "SpawnZ":          tag.Int(IZ),
            "SpawnAngle":      tag.Float(0.0),
            "clearWeatherTime": tag.Int(0),
            "rainTime":        tag.Int(0),
            "raining":         tag.Byte(0),
            "thunderTime":     tag.Int(0),
            "thundering":      tag.Byte(0),
            "BorderCenterX":   tag.Double(0.0),
            "BorderCenterZ":   tag.Double(0.0),
            "BorderSize":      tag.Double(60000000.0),
            "DataPacks": tag.Compound({
                "Enabled": tag.List[tag.String]([
                    tag.String("vanilla"),
                    tag.String("file/bukkit")
                ]),
                "Disabled": tag.List[tag.String]([])
            }),
            "WorldGenSettings": tag.Compound({
                "bonus_chest":      tag.Byte(0),
                "generate_features": tag.Byte(0),
                "seed":             tag.Long(SEED),
                "dimensions": tag.Compound({
                    "minecraft:overworld": tag.Compound({
                        "type": tag.String("minecraft:overworld"),
                        "generator": tag.Compound({
                            "type": tag.String("minecraft:flat"),
                            "settings": tag.Compound({
                                "biome":    tag.String("minecraft:the_void"),
                                "features": tag.Byte(0),
                                "lakes":    tag.Byte(0),
                                "layers":   tag.List[tag.Compound]([]),
                                "structure_overrides": tag.List[tag.String]([])
                            })
                        })
                    }),
                    "minecraft:the_nether": tag.Compound({
                        "type": tag.String("minecraft:the_nether"),
                        "generator": tag.Compound({
                            "type":     tag.String("minecraft:noise"),
                            "settings": tag.String("minecraft:nether"),
                            "biome_source": tag.Compound({
                                "type":   tag.String("minecraft:multi_noise"),
                                "preset": tag.String("minecraft:nether")
                            })
                        })
                    }),
                    "minecraft:the_end": tag.Compound({
                        "type": tag.String("minecraft:the_end"),
                        "generator": tag.Compound({
                            "type":     tag.String("minecraft:noise"),
                            "settings": tag.String("minecraft:end"),
                            "biome_source": tag.Compound({
                                "type": tag.String("minecraft:the_end")
                            })
                        })
                    })
                })
            })
        })
    })

    level.save(os.path.join(out_dir, "level.dat"), gzipped=True)
    print(f"  Written {out_dir}/level.dat  (void flat world)")


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    print(f"Creating {WORLD_DIR}/ ...")

    for sub in ["region", "data", "entities", "poi", "playerdata", "advancements",
                os.path.join("datapacks", "bukkit")]:
        os.makedirs(os.path.join(WORLD_DIR, sub), exist_ok=True)

    # Minimal bukkit datapack marker (Paper requires this)
    pack_meta = os.path.join(WORLD_DIR, "datapacks", "bukkit", "pack.mcmeta")
    if not os.path.exists(pack_meta):
        with open(pack_meta, "w") as f:
            f.write('{"pack":{"pack_format":48,"description":"Bukkit"}}')

    write_level_dat(WORLD_DIR)

    print("Designing tropical island ...")
    blocks = design_island()
    print(f"  {len(blocks)} blocks placed")

    # Determine unique chunks and group by region
    region_chunks: dict = {}
    for (bx, by, bz) in blocks:
        cx, cz = bx >> 4, bz >> 4
        rx, rz = cx >> 5, cz >> 5
        region_chunks.setdefault((rx, rz), set()).add((cx, cz))

    print(f"Writing {len(region_chunks)} region file(s) ...")
    for (rx, rz), chunk_set in region_chunks.items():
        write_region(rx, rz, list(chunk_set), blocks, WORLD_DIR)

    print()
    print("=" * 55)
    print("  ponds_world generated successfully!")
    print("=" * 55)
    print(f"  Island centre  :  x={IX}, z={IZ}, surface y={IY}")
    print(f"  Spawn point    :  x={IX}, y={IY+1}, z={IZ}")
    print(f"  Bait Shack     :  x={IX-17}–{IX-5}, z={IZ-5}–{IZ+5}")
    print(f"  Fishing Dock   :  x={IX+7}–{IX+25}, z={IZ-2}–{IZ+2}")
    print(f"  Fishing Pond   :  x={IX+12}–{IX+30}, z={IZ-7}–{IZ+7}")
    print()
    print("  Fisherman Joe is already configured at x=510, z=3.")
    print("  Start the server then run:  /spawnnpc  (in ponds_world)")
    print("=" * 55)


if __name__ == "__main__":
    main()
