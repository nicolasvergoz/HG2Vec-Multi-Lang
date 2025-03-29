#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Default input/output directories
INPUT_DIR="./data/output/pairs"
OUTPUT_DIR="./data/output/preprocessed"
TEMP_DIR="./data/temp/preprocessing"
PATH_DIR="./data/output/edges"
USE_DATASET_GENERATOR=false  # Default to use edge_generator.py

# Check if input directory is provided as argument
if [ "$1" != "" ]; then
    INPUT_DIR="$1"
fi

# Check if output directory is provided as argument
if [ "$2" != "" ]; then
    OUTPUT_DIR="$2"
fi

# Check if temp directory is provided as argument
if [ "$3" != "" ]; then
    TEMP_DIR="$3"
fi

# Check if path directory is provided as argument
if [ "$4" != "" ]; then
    PATH_DIR="$4"
fi

# Check if we should use the dataset generator
if [ "$5" = "dataset" ]; then
    USE_DATASET_GENERATOR=true
fi

echo "Using input directory: $INPUT_DIR"
echo "Using output directory: $OUTPUT_DIR"
echo "Using temp directory: $TEMP_DIR"
echo "Using path directory: $PATH_DIR"
if [ "$USE_DATASET_GENERATOR" = true ]; then
    echo "Using edge_generator_dataset.py (splitting by datasets)"
else
    echo "Using edge_generator.py (standard mode)"
fi

# Create directories if they don't exist
mkdir -p "$OUTPUT_DIR"
mkdir -p "$TEMP_DIR"
mkdir -p "$PATH_DIR"

# Function to check and find the appropriate file
find_input_file() {
    local base_name=$1
    local dir=$2
    
    # First try the standard name
    if [ -f "$dir/${base_name}.txt" ]; then
        echo "$dir/${base_name}.txt"
        return
    fi
    
    # Look for any K-value suffix (K0, K1, K5, etc.)
    local k_files=($dir/${base_name}-K*.txt)
    if [ ${#k_files[@]} -gt 0 ] && [ -f "${k_files[0]}" ]; then
        # Use the first K file found (if multiple exist)
        echo "${k_files[0]}"
        return
    fi
    
    # No matching files found
    echo "ERROR: Cannot find ${base_name}.txt or ${base_name}-K*.txt in $dir" >&2
    exit 1
}

# Find input files
STRONG_FILE=$(find_input_file "strong-pairs" "$INPUT_DIR")
WEAK_FILE=$(find_input_file "weak-pairs" "$INPUT_DIR")
SYN_FILE=$(find_input_file "syn-pairs" "$INPUT_DIR")
ANT_FILE=$(find_input_file "ant-pairs" "$INPUT_DIR")

echo "Using strong pairs file: $STRONG_FILE"
echo "Using weak pairs file: $WEAK_FILE"
echo "Using synonym pairs file: $SYN_FILE"
echo "Using antonym pairs file: $ANT_FILE"

# Read input files, generate Word2ID related files and the heterogeneous graph
python "$SCRIPT_DIR/id_generator.py" --input_strong_file "$STRONG_FILE" \
                                    --input_weak_file "$WEAK_FILE" \
                                    --input_syn_file "$SYN_FILE" \
                                    --input_ant_file "$ANT_FILE" \
                                    --output_file "$TEMP_DIR/edge.csv" \
                                    --output_folder "$TEMP_DIR/" \
                                    --output_id_info "$OUTPUT_DIR/id_info.csv" \
                                    --output_strong_file "$OUTPUT_DIR/strong-pairs.pkl" \
                                    --output_weak_file "$OUTPUT_DIR/weak-pairs.pkl" \
                                    --output_syn_file "$OUTPUT_DIR/syn-pairs.pkl" \
                                    --output_ant_file "$OUTPUT_DIR/ant-pairs.pkl"

# From the heterogeneous graph, sample paths for training
if [ "$USE_DATASET_GENERATOR" = true ]; then
    # Using edge_generator_dataset.py (splits by dataset)
    
    # First task: Process str_weak edges (normal mode)
    echo "Processing str_weak edges with dataset generator..."
    python "$SCRIPT_DIR/edge_generator_dataset.py" --input_file "$TEMP_DIR/edge_str_weak.csv" \
                                                  --output_directory "$PATH_DIR/" \
                                                  --output_name "_edge_str_weak.npy" \
                                                  --run_mode "normal"
    
    # Second task: Process syn_ant edges (polar mode)
    echo "Processing syn_ant edges with dataset generator..."
    python "$SCRIPT_DIR/edge_generator_dataset.py" --input_file "$TEMP_DIR/edge_syn_ant.csv" \
                                                  --output_directory "$PATH_DIR/" \
                                                  --output_name "_edge_syn_ant.npy" \
                                                  --run_mode "polar"
else
    # Using standard edge_generator.py (default)
    
    # First task: Process str_weak edges (normal mode)
    echo "Processing str_weak edges..."
    python "$SCRIPT_DIR/edge_generator.py" --input_file "$TEMP_DIR/edge_str_weak.csv" \
                                          --output_directory "$PATH_DIR/" \
                                          --output_name "_edge_str_weak.npy" \
                                          --run_mode "normal"
    
    # Second task: Process syn_ant edges (polar mode)
    echo "Processing syn_ant edges..."
    python "$SCRIPT_DIR/edge_generator.py" --input_file "$TEMP_DIR/edge_syn_ant.csv" \
                                          --output_directory "$PATH_DIR/" \
                                          --output_name "_edge_syn_ant.npy" \
                                          --run_mode "polar"
fi

