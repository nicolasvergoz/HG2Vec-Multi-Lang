#!/bin/sh

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

# Parse command line options
while getopts p:n:s:w:y:a:l:g: flag
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
    esac
done

# Validate language
if [ "$LANG" != "en" ] && [ "$LANG" != "fr" ]; then
    echo "Error: Language '$LANG' not supported. Please use 'en' or 'fr'."
    exit 1
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

time python main.py --emb_dimension 300 --output_per_epoch=True --num_workers 8 --window 5 --beta_pos $POS \
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