# HG2Vec
This is the implemention of the paper "HG2Vec: ImprovedWord Embeddings from Dictionary and Thesaurus Based Heterogeneous Graph". Our paper is accepted by COLING 2022. Here is the link: [https://aclanthology.org/2022.coling-1.279/](https://aclanthology.org/2022.coling-1.279/) <br />
HG2Vec is a language model that learns word embeddings utilizing only dictionaries and thesauri. Our model reaches the state-of-art on multiple word similarity and relatedness benchmarks.<br />

## Running Environment:

pytorch <br />
einops <br />
numpy <br />
networkx <br />
pandas <br />
tqdm <br />
pickle <br />
csv <br />

## Directory Structures:

./input/: the folder for input dictionaries and thesauri <br />
./data/: the folder that contains id and pairs for datasets <br />
./path/: the folder contains generated paths for training <br />
./eval/: the folder contains evaluation datasets <br />

## Training:

We already include the prepossessed paths in our repo. To reproduce the results, simply run <br />
```
sh run_demo.sh 
```

However, if you want to generate the graph and paths again, you can run
```
sh data_prepossessing.sh
```

## Special Thanks:
Special thanks to Heqiong Xi, who helps the data propressessing part of this project.

# Vector Processor

This folder contains scripts to train and evaluate the HG2Vec model.

## Project Structure

The scripts are designed to work with the following project structure:

```
HG2VecMulti/
├── data/
│   ├── input/
│   │   ├── id_info.csv
│   │   ├── strong-pairs.pkl
│   │   ├── weak-pairs.pkl
│   │   ├── syn-pairs.pkl
│   │   ├── ant-pairs.pkl
│   │   └── eval/
│   │       ├── en/
│   │       │   └── english evaluation files
│   │       └── fr/
│   │           └── french evaluation files
│   └── output/
│       ├── log/
│       └── ckpt/
└── tools/
    └── processors/
        └── vector_processor/
            ├── dataset.py
            ├── model.py
            ├── evaluate.py
            ├── main.py
            ├── train.sh
            └── run_demo.sh
```

## Running the Scripts

You can run the scripts from the vector_processor directory:

```bash
cd tools/processors/vector_processor
./run_demo.sh
```

Or from the project root directory:

```bash
cd HG2VecMulti
./tools/processors/vector_processor/run_demo.sh
```

The run_demo.sh script will run both English and French evaluations sequentially. Output files will be stored in `data/output/` directory.

## Training Parameters

The model can be trained with different parameters using the train.sh script:

```bash
./train.sh -p 1.0 -n 3.5 -s 0.6 -w 0.4 -y 1.0 -a 1.0 -l 0.003 -g en
```

Parameters:
- p: beta_pos (positive sampling)
- n: beta_neg (negative sampling)
- s: beta_strong (strong pairs)
- w: beta_weak (weak pairs) 
- y: beta_syn (synonym pairs)
- a: beta_ant (antonym pairs)
- l: learning rate
- g: language (en for English, fr for French)

## Language Support

The model supports both English and French evaluations. To run with a specific language:

```bash
# For English
./train.sh -p 1.0 -n 3.5 -s 0.6 -w 0.4 -y 1.0 -a 1.0 -l 0.003 -g en

# For French
./train.sh -p 1.0 -n 3.5 -s 0.6 -w 0.4 -y 1.0 -a 1.0 -l 0.003 -g fr
```

You can also evaluate an existing model against a specific language:

```bash
python evaluate.py path/to/model.txt --lang fr
```

