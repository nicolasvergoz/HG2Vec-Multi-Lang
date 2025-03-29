#!/bin/sh

# Record start time
START_DATETIME=$(date "+%Y-%m-%d %H:%M:%S")
START_SECONDS=$(date +%s)

echo "=== Starting execution at $START_DATETIME ==="
echo

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Get the project root directory (3 levels up from script location)
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Default parameters
LANG="en"
POS="1.0"
NEG="3.5"
STRONG="0.6"
WEAK="0.4"
SYN="1.0"
ANT="1.0"
LR="0.003"
NUM_WORKERS=8

# Auto-detect number of available CPU cores
if command -v nproc >/dev/null 2>&1; then
    TOTAL_CORES=$(nproc)
elif [ "$(uname)" = "Darwin" ] && command -v sysctl >/dev/null 2>&1; then
    TOTAL_CORES=$(sysctl -n hw.ncpu)
else
    TOTAL_CORES=$NUM_WORKERS  # Fallback to default if detection fails
fi

# Reserve cores for system based on total available
if [ "$TOTAL_CORES" -gt 3 ]; then
    # If more than 3 cores, reserve 2 cores for system
    AUTO_WORKERS=$((TOTAL_CORES - 2))
elif [ "$TOTAL_CORES" -eq 2 ]; then
    # If only 2 cores, reserve 1 core for system
    AUTO_WORKERS=1
else
    # If only 1 core, use it
    AUTO_WORKERS=1
fi

# Use detected number if available, otherwise use default
NUM_WORKERS=$AUTO_WORKERS

# Parse command line options
while getopts p:n:s:w:y:a:l:g:c: flag
do
    case "${flag}" in 
        p) POS=${OPTARG};;
        n) NEG=${OPTARG};;
        s) STRONG=${OPTARG};;
        w) WEAK=${OPTARG};;
        y) SYN=${OPTARG};;
        a) ANT=${OPTARG};;
        l) LR=${OPTARG};;
        g) LANG=${OPTARG};;
        c) NUM_WORKERS=${OPTARG};;  # Allow manual override through command line
    esac
done

# Validate language
if [ "$LANG" != "en" ] && [ "$LANG" != "fr" ]; then
    echo "Error: Language '$LANG' not supported. Please use 'en' or 'fr'."
    exit 1
fi

# Ask for user confirmation about number of workers
echo "Detected $TOTAL_CORES CPU cores. Planning to use $NUM_WORKERS workers."
read -p "Do you want to proceed with $NUM_WORKERS workers? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    read -p "Enter the number of workers you want to use: " CUSTOM_WORKERS
    if [ -n "$CUSTOM_WORKERS" ] && [ "$CUSTOM_WORKERS" -gt 0 ]; then
        NUM_WORKERS=$CUSTOM_WORKERS
        echo "Using $NUM_WORKERS workers as specified."
    else
        echo "Invalid input. Using default of $NUM_WORKERS workers."
    fi
fi

# Change to script directory
cd "$SCRIPT_DIR"

# Create parameter string for file naming
PARAMETERS="${POS}_${NEG}_${STRONG}_${WEAK}_${SYN}_${ANT}_${LR}_${LANG}"

# Create output directories with absolute paths
OUTPUT_DIR="$PROJECT_ROOT/data/output/$PARAMETERS/"
LOG_DIR="$PROJECT_ROOT/data/output/log/"
CKPT_DIR="$PROJECT_ROOT/data/output/ckpt/$PARAMETERS/"

mkdir -p $OUTPUT_DIR
mkdir -p $LOG_DIR
mkdir -p $CKPT_DIR

# Define paths
LOG_PATH="$LOG_DIR$PARAMETERS.txt"
FIGURE_PATH="$LOG_DIR$PARAMETERS.png"
CKPT_PATH="$CKPT_DIR/hg2vec.ckpt"
OUTPUT_PATH="$OUTPUT_DIR/hg2vec.txt"

# Run the training
echo "Running ${LANG} training with parameters: POS=$POS NEG=$NEG STRONG=$STRONG WEAK=$WEAK SYN=$SYN ANT=$ANT LR=$LR"
echo "Using $NUM_WORKERS worker(s)"

time python main.py --emb_dimension 300 --output_per_epoch=True --num_workers $NUM_WORKERS --window 5 --beta_pos $POS \
--beta_neg $NEG --beta_strong $STRONG --beta_weak $WEAK --beta_syn $SYN --beta_ant $ANT --batch_size 16 \
--epochs 5 --lr $LR --output_vector_path=$OUTPUT_PATH --output_ckpt_path=$CKPT_PATH \
--neg_size 5 --strong_size 5 --weak_size 5 --syn_size 5 --ant_size 5 --lang $LANG \
--input_vector_folder="$PROJECT_ROOT/data/output/edges/" \
--input_id_info="$PROJECT_ROOT/data/output/preprocessed/id_info.csv" \
--strong_file="$PROJECT_ROOT/data/output/preprocessed/strong-pairs.pkl" \
--weak_file="$PROJECT_ROOT/data/output/preprocessed/weak-pairs.pkl" \
--syn_file="$PROJECT_ROOT/data/output/preprocessed/syn-pairs.pkl" \
--ant_file="$PROJECT_ROOT/data/output/preprocessed/ant-pairs.pkl"

# Run evaluation
python evaluate.py "$OUTPUT_PATH" --lang $LANG

# Calculate and display execution time
END_DATETIME=$(date "+%Y-%m-%d %H:%M:%S")
END_SECONDS=$(date +%s)
DURATION=$((END_SECONDS - START_SECONDS))
DAYS=$((DURATION / 86400))
HOURS=$(( (DURATION % 86400) / 3600 ))
MINUTES=$(( (DURATION % 3600) / 60 ))
SECONDS=$((DURATION % 60))

echo
echo "=== Execution completed at $END_DATETIME ==="
echo "=== Total time: ${DAYS}d ${HOURS}h ${MINUTES}m ${SECONDS}s ==="