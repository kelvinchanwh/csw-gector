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
Our experiment used datasets based on the following datasets:
- All the public GEC datasets used in the paper can be downloaded from [here](https://www.cl.cam.ac.uk/research/nl/bea2019st/#data).
- Synthetically created datasets can be generated/downloaded [here](https://github.com/awasthiabhijeet/PIE/tree/master/errorify).

Once the above datasets are downloaded, the following code can be used to generate a dataset similar to that used in the paper.

## Training
### Training Data Augmentation
To perform data augmentation, simply run:
```.bash
python utils/substitute_gcm.py INPUT_INV_M2_FILE OUTPUT_CS_INCORR_PATH OUTPUT_CS_CORR_PATH SRC_LANG TGT_LANG SELECTION_METHOD
```

Arguments:
- `INPUT_INV_M2_FILE`: Inversed M2 file generated using ERRANT. This M2 file should indicate the edits required to generate a **incorrect** sentence from a **correct** sentence. The file can be generated using `errant_parallel -orig <correct_file> -cor <incorrect_file> -out <out_m2>`.
- `OUTPUT_CS_INCORR_PATH`: Output path for incorrect (errornous) CSW parallel text
- `OUTPUT_CS_CORR_PATH`: Output path for correct (error-free) CSW parallel text
- `SRC_LANG`: Source language used by the input M2 file. Language should be denoted using [ISO639-1](https://en.wikipedia.org/wiki/ISO_639) language codes for [supported languages](https://developers.google.com/translate/v2/using_rest#language-params)
- `TGT_LANG`: Target language for CSW component. Language should be denoted using [ISO639-1](https://en.wikipedia.org/wiki/ISO_639).
- `SELECTION_METHOD`: Method used to select component to translate for CSW. Possible selection methods include:
    - `ratio-token`: randomly select tokens from the sentence based on a reference corpus distribution
    - `cont-token`: randomly select a string of continuous tokens to match the ratio of code-switched text
    - `rand-phrase`: randomly select phrases from the sentence
    - `ratio-phrase`: select the phrase that has a length closest to the reference corpus distribution
    - `overlap-phrase`: select phrases which intersect with the least number of edit spans
    - `noun-token`: randomly selects a single token with a NOUN or PROPN POS tag based on SpaCy


### Train model
Before training the model, the data has to be preprocessed and converted to special format with the command:
```.bash
python utils/preprocess_data.py -s SOURCE_FILE -t TARGET_FILE -o OUTPUT_FILE
```


To train the model, simply run:
```.bash
python train.py --train_set TRAIN_SET_PATH --dev_set DEV_SET_PATH \
                --model_dir MODEL_DIR_PATH
```
There are a number of parameters that can be specified. Among them:
- `cold_steps_count` the number of epochs where we train only last linear layer
- `transformer_model {bert,distilbert,gpt2,roberta,transformerxl,xlnet,albert}` model encoder
- `tn_prob` probability of getting sentences with no errors; helps to balance precision/recall
- `pieces_per_token` maximum number of subwords per token; helps not to get CUDA out of memory

### Training parameters
All parameters that used for training and evaluating is exactly the same as GECTOR which can be found [here](https://github.com/grammarly/gector/blob/master/docs/training_parameters.md). 

## Evaluation
### CSW Lang-8 Dataset
To generate the CSW Lang-8 dataset (used as our test dataset) from the Lang-8 dataset, we can use the `filter_cs.py` script to filter out sentences containing CSW text.
```.bash
python data_gen/filter_cs.py <lang8_input_path.dat> -out <json_output_path.json>
```

We can then sort the sentences based on CSW language using `sort_lang.py`. The json files can then be converted to ERRANT style m2 files using `json_to_m2.py`.

```.bash
cd data_gen
mkdir l1s_cor
python sort_lang.py <json_output_path.json>
python json_to_m2.py l1s_cor/<language.json>
```

### Human Reannotated Dataset
To generate the human reannotated dataset from the CSW Lang-8 dataset, we need to install ERRANT:

```.bash
python3 -m venv errant_env
source errant_env/bin/activate
pip install -U pip setuptools wheel
pip install errant
python3 -m spacy download en_core_web_sm
```

We can then run the `create_human.py` script to generate the human reannotated dataset.
```.bash
cd data_gen
python create_human.py l1s_cor/<language.json> <language>.csw.test.id.m2 <output.m2>
```

The output of the `create_human.py` script is the m2 file used for human re-annotated dataset evaluation. 


### Model inference
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

### Model evaluation
For evaluation, we use [ERRANT](https://github.com/chrisjbryant/errant). 

```.bash
errant_compare -hyp <hyp_m2> -ref <ref_m2> 
```

## License

Similar to the original Lang-8 corpus, the CSW Lang-8 Dataset is distributed for research and
educational purposes only. The code for GECTOR is distributed under Apache 2.0 license.