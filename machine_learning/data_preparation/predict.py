import pandas as pd
import numpy as np
import argparse
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

from datasets import (
    load_from_disk,
    DatasetDict, 
    Dataset
)
from transformers import (
    PreTrainedTokenizerFast,
    FalconForSequenceClassification,
    Trainer,
)

from sklearn.metrics import (
    roc_auc_score, 
    recall_score, 
    precision_score, 
    f1_score,
    matthews_corrcoef,
    average_precision_score
)

from utils import get_full_aa_sub

def setup(rank, world_size):
    # initialize the process group
    dist.init_process_group("nccl", rank=rank, world_size=world_size)
    torch.cuda.set_device(rank)

def main(
    input_path: str,
    output_path: str,
    HF_dataset_path: str,
    tokenizer_path: str,
    model_path: str,
    # local_rank: int
    # vh_column: str = typer.Option("sequence_vh", help ="Column in input file which contains the heavy chain sequence")
):
    
    # dist.init_process_group(backend='nccl')
    # torch.cuda.set_device(local_rank)
    if input_path.endswith('.csv'):
        #LOAD DATASET
        dataset_to_predict=pd.read_csv(input_path)
        original_columns = dataset_to_predict.copy()

        available_columns=dataset_to_predict.columns
        
        if 'label' in available_columns:
            dataset_to_predict=dataset_to_predict[['sequence_vh','label']].copy()
            dataset_to_predict['label'] = dataset_to_predict['label'].astype(int)
        else:
            dataset_to_predict=dataset_to_predict[['sequence_vh']].copy()
    
    # output from pipeline is tsv files
    elif input_path.endswith('.tsv'):
        dataset_to_predict=pd.read_csv(input_path, sep='\t')  
        available_columns=dataset_to_predict.columns
        if 'sequence_vh' in available_columns:
            raise NameError('tsv file already has sequence_vh column. Please remove it to continue')
        elif 'sequence_alignment' not in available_columns and 'germline_alignment_d_mask' not in available_columns:
            raise NameError('tsv file must have sequence_alignment and germline_alignment_d_mask columns') 
        else: 
            dataset_to_predict['sequence_vh'] = dataset_to_predict.apply(
            lambda row: get_full_aa_sub(str(row['sequence_alignment']), str(row['germline_alignment_d_mask'])), 
            axis=1
            )
            original_columns = dataset_to_predict.copy()


    #PREPARE DATASET INTO HF FORMAT
    dataset_to_predict['sequence']='Ḣ'+dataset_to_predict['sequence_vh']
    # Dataset is a HuggingFace dataset object that can be converted from Pandas.
    dd = DatasetDict({
        "test": Dataset.from_pandas(dataset_to_predict)
    })
    
    tokenizer = PreTrainedTokenizerFast.from_pretrained(tokenizer_path)
    model = FalconForSequenceClassification.from_pretrained(model_path).eval()
    # model = FalconForSequenceClassification.from_pretrained(model_path).to(local_rank)
    # model = DDP(model, device_ids=[local_rank])
    dd = dd.map(
    
        # The lambda calls the Fabcon tokenizer to convert amino acids into token IDs (i.e. integers)
        lambda row: tokenizer(row['sequence'],
                            return_tensors='pt',
                            max_length=256, ## FAbCon and AntiBERTa2 can only accept up to 256 tokens
                        padding=True),
        
        # tokenize 32 sequences at a time
        batched=True,
        batch_size=32,
        
        # we want to remove columns in the Dataset object because they're not needed by the Falcon/Fabcon model.
        # for Fabcon we only need input_ids, attention_mask, and label
        remove_columns=['sequence_vh', 'sequence'] #'label', 
    ).remove_columns("token_type_ids")
    
    #SAVE NEW HF DATASET
    dd.save_to_disk(HF_dataset_path)

    tokenized_dataset=load_from_disk(HF_dataset_path)

    trainer = Trainer(
            model=model,
            tokenizer=tokenizer
        )
    
    trainer_prediction_output=trainer.predict(test_dataset=tokenized_dataset['test'])
    
    #Calculating probs of being a viral sequence
    probs = torch.softmax(torch.from_numpy(trainer_prediction_output.predictions), dim=1).detach().numpy()
    probs = probs[:, -1]
    
    dataset_to_predict['viral_prob']=probs
    dataset_to_predict['human_prob'] = 1 - dataset_to_predict['viral_prob']

    # Define conditions
    conditions = [
        dataset_to_predict['viral_prob'] > 0.95,
        dataset_to_predict['human_prob'] > 0.95
    ]

    # Define choices for each condition
    choices = ['viral', 'human']

    # Apply conditions to create 'human_viral_prediction' column
    dataset_to_predict['human_viral_prediction'] = np.select(
        conditions, choices, default=""
    )


    if ".csv" in output_path:
        final_output = pd.merge(
            original_columns,
            dataset_to_predict[['sequence_vh', 'viral_prob', 'human_prob', 'human_viral_prediction']],
            on='sequence_vh',
            how='left'
        )
        final_output.to_csv(output_path,index=None)
    elif ".tsv" in output_path:
        # original_columns['sequence_vh'] = original_columns.apply(
        #     lambda row: get_full_aa_sub(str(row['sequence_alignment']), str(row['germline_alignment_d_mask'])), 
        #     axis=1
        # )
        final_output = pd.merge(
            original_columns,
            dataset_to_predict[['sequence_vh', 'viral_prob', 'human_prob', 'human_viral_prediction']],
            on='sequence_vh',
            how='left'
        )
        final_output.to_csv(output_path,index=None,sep="\t")
    
    if 'label' in available_columns:
        labels=list(trainer_prediction_output.label_ids)
        probs_binary=[1 if x>0.5 else 0 for x in probs]
        auc=roc_auc_score(labels, probs)
        aupr=average_precision_score(labels, probs)
        f1=f1_score(labels,probs_binary)
        precision=precision_score(labels,probs_binary)
        recall=recall_score(labels,probs_binary)
        mcc = matthews_corrcoef(labels, probs_binary)
        
        print('roc_auc:',auc,'average_precision_score',aupr,'f1:',f1,'precision:',precision,'recall:',recall,'mcc',mcc)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Viral Sequence Prediction', 
                                     usage="""torchrun --nproc_per_node=[NUMBER_OF_GPUS] predict.py \
                                     --input_path ... \
                                     --output_path ... \
                                     --HF_dataset_path ... \
                                     --tokenizer_path ... \
                                     --model_path ... \
                                     --local_rank 1""")
    parser.add_argument('--input_path', type=str, required=True, help='.csv format file with columns: sequence_vh, label (1 for viral 0 otherwise, optional)')
    parser.add_argument('--output_path', type=str, required=True, help='Output file')
    parser.add_argument('--HF_dataset_path', type=str, default='./hf_dataset/', help='Folder to save a Hugging Face dataset created from csv file sequences')
    parser.add_argument('--tokenizer_path', type=str, default='./fabcon-small/', help='Path to the tokenizer for your model')
    parser.add_argument('--model_path', type=str, required=True, help='Path to the model')
    # parser.add_argument('--local_rank', type=int, default=-1, help='Local rank for distributed training')

    args = parser.parse_args()
    main(args.input_path, 
         args.output_path, 
         args.HF_dataset_path, 
         args.tokenizer_path, 
         args.model_path,
        #  args.local_rank
         )