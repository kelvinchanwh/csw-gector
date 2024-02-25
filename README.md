# Grammatical Error Correction for Code-Switched Sentences by Learners of English

This repository provides code for training and testing models for grammatical error correction on code-switching text. It is based on and forked from the GECTOR repository (https://github.com/grammarly/gector). Main contributions to the code can be found in the `utils` folder except for `utils/helpers.py` and `utils/preprocess_data.py`. The latter two files and the `train.py` and `predict.py` files are modified versions of the files in the GECTOR repository to adapt the code for code-switching. 

## Installation
The following command installs all necessary packages:
```.bash
pip install -r requirements.txt
```
The project was tested using Python 3.7.

Optionally, install ERRANT to evaluate the output of the model:
```.bash
pip install errant
```

## Datasets
All the public GEC datasets used in the paper can be downloaded from [here](https://www.cl.cam.ac.uk/research/nl/bea2019st/#data).<br>
Synthetically created datasets can be generated/downloaded [here](https://github.com/awasthiabhijeet/PIE/tree/master/errorify).<br>
To train the model data has to be preprocessed and converted to special format with the command:
```.bash
python utils/preprocess_data.py -s SOURCE -t TARGET -o OUTPUT_FILE
```

## Data Augmentation
To perform data augmentation, simply run:
```.bash
python utils/substitute_gcm.py INPUT_INV_M2_FILE OUTPUT_CS_INCORR_FILE OUTPUT_CS_CORR_FILE SRC_LANG TGT_LANG SELECTION_METHOD
```

Possible selection methods include:
- `frac-token`: randomly select tokens from the sentence based on a reference corpus distribution
- `contfrac-token`: randomly select a string of continuous tokens to match the ratio of code-switched text
- `random-phrase`: randomly select phrases from the sentence
- `frac-phrase`: select the phrase that has a length closest to the reference corpus distribution
- `intersect-phrase`: select phrases which intersect with the least number of edit spans
- `noun-token`: randomly selects a single token with a NOUN or PROPN POS tag based on SpaCy


## Train model
To train the model, simply run:
```.bash
python train.py --train_set TRAIN_SET --dev_set DEV_SET \
                --model_dir MODEL_DIR
```
There are a lot of parameters to specify among them:
- `cold_steps_count` the number of epochs where we train only last linear layer
- `transformer_model {bert,distilbert,gpt2,roberta,transformerxl,xlnet,albert}` model encoder
- `tn_prob` probability of getting sentences with no errors; helps to balance precision/recall
- `pieces_per_token` maximum number of subwords per token; helps not to get CUDA out of memory

## Training parameters
All parameters that we use for training and evaluating is exactly the same as GECTOR which can be found [here](https://github.com/grammarly/gector/blob/master/docs/training_parameters.md). 
<br>

## Model inference
To run your model on the input file use the following command:
```.bash
python predict.py --model_path MODEL_PATH [MODEL_PATH ...] \
                  --vocab_path VOCAB_PATH --input_file INPUT_FILE \
                  --output_file OUTPUT_FILE
```
Among parameters:
- `min_error_probability` - minimum error probability (as in the paper)
- `additional_confidence` - confidence bias (as in the paper)
- `special_tokens_fix` to reproduce some reported results of pretrained models

For evaluation use [ERRANT](https://github.com/chrisjbryant/errant).
