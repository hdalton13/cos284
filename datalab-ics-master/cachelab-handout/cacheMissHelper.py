"""
cacheMissHelper.py

I wrote this to aid in debugging the ICS Cache Lab transpose function; it
visualizes what parts of the matrices are hitting and missing, so you can
find patterns and discover ways to optimize your code.
Feel free to contact me if you have issues with this script!
-John
john_pugsley@taylor.edu

Usage example:
$ clear && make clean && make
$ ./test-trans -M 64 -N 64
$ ./csim-ref -v -s 5 -E 1 -b 5 -t trace.f0 > traceAnalysis64
$ python3 cacheMissHelper.py traceAnalysis64 64 64
"""

import sys

# Config based on the current format of the lab: these could potentially need to change
# if parts of the lab change.
BYTES_PER_ELEMENT = 4 # number of bytes for the datatype in the matrices
SKIP_LAST_LINE = True # make true if the last line is 'hits:___ misses:___ evictions:___'
SOURCE_MATRIX_LOWER = True # if the soure matrix resides lower in memory than the destination

# Parse command line args
try:
    fileName = sys.argv[1]
    M = int(sys.argv[2])
    N = int(sys.argv[3])
except:
    print("Usage: python3 cacheMissHelper.py <trace_file_name> <M> <N>")
    print()
    print("    Usage example:")
    print("    $ clear && make clean && make")
    print("    $ ./test-trans -M 64 -N 64")
    print("    $ ./csim-ref -v -s 5 -E 1 -b 5 -t trace.f0 > traceAnalysis64")
    print("    $ python3 cacheMissHelper.py traceAnalysis64 64 64")
    exit()

# Read from provided file
with open(fileName, "r") as file:
    if SKIP_LAST_LINE:
        rawIn = file.readlines()[:-1]
    else:
        rawIn = file.readlines()

# Parse raw input into addr:result pairs
addrsWithResults = {}
duplicateAddrs = []
for line in rawIn:
    # line example 'S 18e08c,1 miss \n'
    lineList  = line.split()
    addrStr = lineList[1].split(",")[0]
    addr = int(addrStr, 16)
    hitOrMiss = lineList[2]
    if addr in addrsWithResults:
        duplicateAddrs.append(addrStr)
        if hitOrMiss == "miss" and addrsWithResults[addr] != "miss":
            addrsWithResults[addr] = "miss"
    else:
        addrsWithResults[addr] = hitOrMiss

# If any duplicates found, warn the user
numDuplicates = len(duplicateAddrs)
if numDuplicates > 0:
    print()
    s = "" if numDuplicates == 1 else "s"
    es = "" if s == "" else "es"
    print(f"Warning: your transpose function references {numDuplicates} memory location{s} muliple times! Memory address{es}:")
    if numDuplicates <= 10:
        print(", ".join(duplicateAddrs))
    else:
        # use ellipsis if more than 10 elements (otherwise could flood with thousands of addresses)
        duplicateAddrs[6] = "..."
        print(", ".join(duplicateAddrs[:7]+duplicateAddrs[-3:]))
    print()
    input("Hit enter to see the maps anyway, or ctrl+C to quit => ")

# Find the sequential blocks of memory used
memBlocks = {}
for addr in addrsWithResults:

    matches = []
    for blockRef in memBlocks:
        block = memBlocks[blockRef]
        if addr >= block["low"] and addr <= block["high"]:
            matches.append(blockRef)
    
    if len(matches) == 0:
        block = {
            "low": addr - BYTES_PER_ELEMENT,
            "high": addr + BYTES_PER_ELEMENT,
            "range": 1,
        }
        memBlocks[addr] = block
    elif len(matches) == 1:
        block = matches[0]
        if addr == memBlocks[block]["low"]:
            memBlocks[block]["low"] = addr - BYTES_PER_ELEMENT
        if addr == memBlocks[block]["high"]:
            memBlocks[block]["high"] = addr + BYTES_PER_ELEMENT
        memBlocks[block]["range"] += 1
    elif len(matches) == 2:
        block0 = matches[0]
        block1 = matches[1]
        if memBlocks[block0]["high"] == memBlocks[block1]["low"]:
            memBlocks[block0]["high"] = memBlocks[block1]["high"]
            memBlocks[block0]["range"] += memBlocks[block1]["range"] + 1
            del memBlocks[block1]
        elif memBlocks[block1]["high"] == memBlocks[block0]["low"]:
            memBlocks[block1]["high"] = memBlocks[block0]["high"]
            memBlocks[block1]["range"] += memBlocks[block0]["range"] + 1
            del memBlocks[block0]
        else:
            raise RuntimeError("Hit an unexpected situation while parsing.")
    else:
        raise RuntimeError("Hit an unexpected situation while parsing.")

# Find the two matrix blocks and make sure the memory accesses cover the right range
matrices = []
sizes = []
for block in memBlocks:
    sizes.append(memBlocks[block]["range"])
    if memBlocks[block]["range"] == M*N:
        matrices.append(memBlocks[block])
if len(matrices) != 2:
    print(f"Error: your memory references don't cover the expected matrix sizes. For a {M}x{N} matrix, expecting two contiguous reference blocks of {M*N} elements; instead, found these block sizes: {sizes}. Execution terminated.")
    exit()

# Order the matrices
if (SOURCE_MATRIX_LOWER and matrices[0]["low"] > matrices[1]["low"]
    or not SOURCE_MATRIX_LOWER and matrices[0]["low"] < matrices[1]["low"]):
    matrices.reverse()

# Creating lists to load visuals from
symbols = [[],[]]
for i in range(2):
    for addr in range(matrices[i]["low"] + BYTES_PER_ELEMENT, matrices[i]["high"], 4):
        symbol = "m" if addrsWithResults[addr] == "miss" else "-"
        symbols[i].append(symbol)

# Print arrays
print()
print(" ### Source Matrix ###")
for i in range(N):
    for j in range(M):
        symbol = symbols[0][M*i+j]
        print(str(symbol).rjust(2), end="")
    print()

print()
print(" ### Destination Matrix ###")
for i in range(M):
    for j in range(N):
        symbol = symbols[1][N*i+j]
        print(str(symbol).rjust(2), end="")
    print()
