
.ifndef melee.library.included; .include "melee"; .endif
melee.module prim

.if module.included == 0
melee GX

r13.xOrthoCObj = -0x4880

prim.xParamsH  = 0x00  # --- required
prim.xParamsL  = 0x04  # --- required
prim.xCIBase   = 0x08  # - optional: prim.mCIndexed
prim.xPIBase   = 0x0C  # - optional: prim.mPIndexed
prim.xMtx      = 0x10  # - optional: prim.mOtherMTX
prim.xColor    = 0x14  # - optional: prim.mOneColor
prim.xVerts    = 0x18  # - record from prev input
prim.xDefault  = 0x1C  # - static desc, for reverting to default

# --- symbols                    rParamsH rParamsL - (from r4, r5)
prim.mCullMode = 0xC0000000  # + C0000000 00000000
prim.mNoColor  = 0x20000000  # + 20000000 00000000
prim.mAlphaBuf = 0x10000000  # + 10000000 00000000
prim.mLineSize = 0x0FFF0000  # + 0FFF0000 00000000
prim.mZCompLoc = 0x00002000  # + 00002000 00000000
prim.mZCompare = 0x00001000  # + 00001000 00000000
prim.mZBuffer  = 0x00000800  # + 00000800 00000000
prim.mZLogic   = 0x00000700  # + 00000700 00000000
prim.mCIndexed = 0x00000080  # + 00000080 00000000 +rCIBase (from r6)  color
prim.mCIndex16 = 0x00000040  # + 00000040 00000000
prim.mPIndexed = 0x00000020  # + 00000020 00000000 +rPIBase (from r7)  position
prim.mPIndex16 = 0x00000010  # + 00000010 00000000
prim.mIRecache = 0x00000008  # + 00000008 00000000
prim.mPrimType = 0x00000007  # + 00000007 00000000
prim.mFixPoint = 0xFF000000  # + 00000000 FF000000
prim.mOtherMTX = 0x00800000  # + 00000000 00800000 +rMTX    (from r8)
prim.mOneColor = 0x00400000  # + 00000000 00400000 +rColor  (from r9)
prim.mNoZCoord = 0x00200000  # + 00000000 00200000
prim.mNoAChan  = 0x00100000  # + 00000000 00100000
prim.mRGBComp  = 0x00080000  # + 00000000 00080000
prim.mRGBType  = 0x00070000  # + 00000000 00070000
prim.mBMode    = 0x00003000  # + 00000000 00003000
prim.mBMSource = 0x00000700  # + 00000000 00000700
prim.mBMDest   = 0x00000070  # + 00000000 00000070
prim.mBMLogic  = 0x0000000F  # + 00000000 0000000F
prim.mFixPoint_Enable = 0x80
prim.mFixPoint_Type   = 0x60
prim.mFixPoint_Frac   = 0x1F
# masks for separating fixed point params from parent mask



# prim.mCullMode
# +C0000000  00000000 = Cull Mode
#  +8 = cull backface
#  +4 = cull frontface

# prim.mNoColor
# +20000000  00000000 = Disable Color buffer Update
#  false = allow colors
#  true  = disable updates to the color buffer with this polygon
#  - logic is inverted for this syntax to preserve backwards compatibility with older versions

# prim.mAlphaBuf
# +10000000  00000000 = Alpha buffer Update
#  false = skip
#  true  = enable updates to the alpha buffer with this polygon

# prim.mLineSize
# +0FFF0000  00000000 = Line Width/Point Size
#  n = 1/16 native pixel increments

# prim.mZCompLoc
# +00002000  00000000 = Z Compare Location
#  false = z buffer compares after texturing (slower, handles alpha correctly for textures)
#  true  = z buffer compares before texturing (faster, may cause issues for textures)

# prim.mZCompare
# +00001000  00000000 = Z Buffer Compare
#  false = z buffer is ignored by this polygon
#  true  = z buffer enables compare

# prim.mZBuffer
# +00000800  00000000 = Z Buffer Update
#  false = z buffer is unchanged by this polygon
#  true  = z buffer enables update

# prim.mZLogic
# +00000700  00000000 = Z Buffer Comparison Logic
#  +4 = greater than
#  +2 = equal to
#  +1 = less than

# prim.mCIndexed
# +00000080  00000000 = Set Indexed Colors (from r6)
#  false = r6 is ignored; colors are input with the vertex directly from gx fifo
#  true  = r6 specifies the base of an array of vertex colors
#  - inidexed colors are fed to GX using an ID instead of an actual color

# prim.mCIndex16
# +00000040  00000000 = Indexed Colors are 16-bit
#  false = Color IDs are bytes
#  true  = Color IDs are hwords

# prim.mPIndexed
# +00000020  00000000 = Set Indexed Position Coords (from r7)
#  false = position coordinates are input with the vertex directly from fifo
#  true  = r7 specifies the base of an array of vertex position coordinates
#  - indexed positions are fed to GX using an ID instead of an actual set of coordinates

# prim.mPIndex16
# +00000010  00000000 = Indexed Position Coords are 16-bit
#  false = Position IDs are bytes
#  true  = Position IDs are hwords

# prim.mIRecache
# +00000008  00000000 = Indexed Data needs re-cache
#  false = read-only vertex data is read without the need for flushing and waiting for ppcsync
#  true  = flushes DC at array regions to prevent incoherence between CPU and GPU cache
#  - only required for indexed variables -- GPU can't read pending I/O from the CPU outside of fifo

# prim.mPrimType
# +00000007  00000000 = Primitive Type
#  0 = quads
#  1 = --
#  2 = triangles
#  3 = trianglestrip
#  4 = trianglefan
#  5 = lines
#  6 = linestrip
#  7 = points

# prim.mFixPoint
# +00000000  FF000000 = Use Fixed Points for Position Input
#  +80 = enable fixed points (small integer data type with a fractional mantissa)
#  +40 = use 16-bit integers instead of 8-bit integers (includes mantissa)
#  +20 = use signed integers instead of unsigned integers
#  +1F = mantissa bit size (abstract; can be larger than actual bit size)

# prim.mOtherMTX
# +00000000  00800000 = Use Custom MTX (input in r8)
# false = use current CObj mtx
# true  = interpret r8 as either a CObj, a JObj, or a MTX

# prim.mOneColor
# +00000000  00400000 = Use Constant Color (input in r9)
# false = r9 is ignored; colors are read for each individual vertex
# true  = r9 specifies a color to use for all vertices in this polygon

# prim.mNoZCoord
# +00000000  00200000 = Omit Z coord in Position input
#  false = XYZ are read as part of input position coordinates
#  true  = only XY are read as part of input coordinates

# prim.mNoAChan
# +00000000  00100000 = Omit Alpha channel in Color input
#  false = input color includes an alpha channel
#  true  = input color does not have an alpha channel

# prim.mRGBComp
# +00000000 00080000 = Enable Compressed Color Data Format (bool)
#  false = default to uncompressed RGBA
#  true  = use `mRGBType` to specify a custom format type

# prim.mRGBType
# +00000000  00070000 = Color Data Format
#  0 = RGB565  (16-bit) compressed RGB
#  1 = RGB8    (24-bit) Full RGB (no padding)
#  2 = RGBX8   (32-bit) Full RGB aligned for RGBA
#  3 = RGBA4   (16-bit) very compressed RGBA
#  4 = RGBA6   (24-bit) compressed RGBA
#  5 = RGBA8   (32-bit) Full RGBA

# prim.mBMode
# +00000000  00003000 = Blend Type
#  0 = None
#  1 = Blend -- blend using blending equation
#  2 = Logic -- blend using bitwise operation
#  3 = Subtract -- input subtracts from existing pixel

# prim.mBMSource
# +00000000  00000700 = Blend Source (TEV+Fog)
#  0 = zero -- 0.0
#  1 = one  -- 1.0
#  2 = source color
#  3 = inverted source color
#  4 = source alpha
#  5 = inverted source alpha
#  6 = destination alpha
#  7 = inverted destination alpha

# prim.mBMDest
# +00000000  00000070 = Blend Dest (Environmental Frame Buffer)
#  0 = zero -- 0.0
#  1 = one  -- 1.0
#  2 = source color
#  3 = inverted source color
#  4 = source alpha
#  5 = inverted source alpha
#  6 = destination alpha
#  7 = inverted destination alpha

# prim.mBMLogic
# +00000000  0000000F = Blend Logic
#  0 -- CLEAR;   dst = 0
#  1 -- AND;     dst = src & dst
#  2 -- REVAND;  dst = src & ~dst
#  3 -- COPY;    dst = src
#  4 -- INVAND;  dst = ~src & dst
#  5 -- NOOP;    dst = dst
#  6 -- XOR;     dst = src ^ dst
#  7 -- OR;      dst = src | dst
#  8 -- NOR;     dst = ~(src | dst)
#  9 -- EQUIV;   dst = ~(src ^ dst)
#  A -- INV;     dst = ~dst
#  B -- REVOR;   dst = src | ~dst
#  C -- INVCOPY; dst = ~src
#  D -- INVOR;   dst = ~src | dst
#  E -- NAND;    dst = ~(src & dst)
#  F -- SET;     dst = 1

.endif
