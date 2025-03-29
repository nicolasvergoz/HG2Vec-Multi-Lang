# HG2Vec Multi-Language

This is an implementation based on the paper "HG2Vec: ImprovedWord Embeddings from Dictionary and Thesaurus Based Heterogeneous Graph". Our paper is accepted by COLING 2022. Here is the link: [https://aclanthology.org/2022.coling-1.279/](https://aclanthology.org/2022.coling-1.279/)

HG2Vec is a language model that learns word embeddings utilizing only dictionaries and thesauri. The model reaches the state-of-art on multiple word similarity and relatedness benchmarks.

This repository contains an extension of the original [HG2Vec model](https://github.com/Qitong-Wang/HG2Vec) to support multiple languages.

## Running Environment

- pytorch
- einops
- numpy
- networkx
- pandas
- tqdm
- pickle
- csv

## Directory Structure

The project is organized into the following directories:

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
        ├── preprocessor/
        │   ├── data_prepossessing.sh
        │   ├── edge_generator.py
        │   ├── edge_generator_dataset.py
        │   └── id_generator.py
        └── vector_processor/
            ├── dataset.py
            ├── model.py
            ├── evaluate.py
            ├── main.py
            └── trainer.sh
```

## Processor Tools

The processors directory contains two main components:

### 1. Preprocessor

The preprocessor tools are responsible for preparing the data for training:

- **data_prepossessing.sh**: Main script to run the preprocessing pipeline
- **id_generator.py**: Converts word pairs into numerical IDs and generates related files
- **edge_generator.py**: Generates graph edges for training from preprocessed data
- **edge_generator_dataset.py**: Alternative edge generator that splits processing by datasets

To generate the graph and paths, run:
```
sh tools/processors/preprocessor/data_prepossessing.sh
```

### 2. Vector Processor

The vector processor tools are used to train and evaluate the HG2Vec model:

- **dataset.py**: Handles data loading and preparation for model training
- **model.py**: Defines the HG2Vec neural network architecture
- **evaluate.py**: Evaluates trained models on various benchmarks
- **main.py**: Main training script
- **trainer.sh**: Script to run training with specific parameters

#### Running the Vector Processor

You can run the vector processor from its directory:

```bash
cd tools/processors/vector_processor
./trainer.sh -p 1.0 -n 3.5 -s 0.6 -w 0.4 -y 1.0 -a 1.0 -l 0.003 -g en
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

#### Language Support

The model supports both English and French evaluations. To run with a specific language:

```bash
# For English
./trainer.sh -p 1.0 -n 3.5 -s 0.6 -w 0.4 -y 1.0 -a 1.0 -l 0.003 -g en

# For French
./trainer.sh -p 1.0 -n 3.5 -s 0.6 -w 0.4 -y 1.0 -a 1.0 -l 0.003 -g fr
```

You can also evaluate an existing model against a specific language:

```bash
python evaluate.py path/to/model.txt --lang fr
```

## Special Thanks
Special thanks to Heqiong Xi, who helps the data preprocessing part of this project.

