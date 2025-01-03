import pandas as pd
import numpy as np
import argparse
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
import os 
import sys
from datasets import (
    Dataset
)
from transformers import (
    PreTrainedTokenizerFast,
    FalconForSequenceClassification,
)
from tqdm import tqdm
from torch.utils.data import DataLoader, Dataset, DistributedSampler

from sklearn.metrics import (
    roc_auc_score, 
    recall_score, 
    precision_score, 
    f1_score,
    matthews_corrcoef,
    average_precision_score
)

from utils import get_full_aa_sub

class AntibodyRepertoireDataset(Dataset):
    def __init__(self, sequences):
        self.sequences = sequences

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self,index):
        return self.sequences[index]


def setup(rank, world_size):
    dist.init_process_group("nccl", rank=rank, world_size=world_size)
    torch.cuda.set_device(rank)

def cleanup():
    dist.destroy_process_group()


def predict_gpu(
    input_path: str,
    output_file: str,
    tokenizer_path: str,
    model_path: str,
    local_rank: int = 0,
    world_size: int = 1
): 
    setup(local_rank,
          world_size)

    if input_path.endswith('.csv'):
        # LOAD DATASET
        dataset_to_predict = pd.read_csv(input_path)

        available_columns = dataset_to_predict.columns
        dataset_to_predict['fabcon_sequence'] = 'Ḣ' + dataset_to_predict['sequence_vh']
        original_columns = dataset_to_predict.copy()
        
        # DEDUPLICATE UNIQUE SEQUENCES
        dataset_to_predict_deduplicated = dataset_to_predict.drop_duplicates(subset=['fabcon_sequence'])
        
        if 'label' in available_columns:
            dataset_to_predict_deduplicated = dataset_to_predict_deduplicated[['fabcon_sequence','label']].copy()
            dataset_to_predict_deduplicated['label'] = dataset_to_predict_deduplicated['label'].astype(int)
        else:
            dataset_to_predict_deduplicated = dataset_to_predict_deduplicated[['fabcon_sequence']].copy()
    
    # Similar modification for .tsv and .parquet files
    elif input_path.endswith('.tsv') or input_path.endswith('.parquet'):
        if input_path.endswith('.tsv'):
            dataset_to_predict = pd.read_csv(input_path, sep='\t')
        else:
            dataset_to_predict = pd.read_parquet(input_path)
        available_columns = dataset_to_predict.columns

        if 'sequence_vh' in available_columns:
            dataset_to_predict['fabcon_sequence'] = 'Ḣ' + dataset_to_predict['sequence_vh']
            original_columns = dataset_to_predict.copy()
            
            # DEDUPLICATE UNIQUE SEQUENCES
            dataset_to_predict_deduplicated = dataset_to_predict.drop_duplicates(subset=['fabcon_sequence'])

        elif 'sequence_alignment' in available_columns and 'germline_alignment_d_mask' in available_columns:
            dataset_to_predict['sequence_vh'] = dataset_to_predict.apply(
                lambda row: get_full_aa_sub(str(row['sequence_alignment']), str(row['germline_alignment_d_mask'])), 
                axis=1
            )
            dataset_to_predict['fabcon_sequence'] = 'Ḣ' + dataset_to_predict['sequence_vh']
            original_columns = dataset_to_predict.copy()
            
            # DEDUPLICATE UNIQUE SEQUENCES
            dataset_to_predict_deduplicated = dataset_to_predict.drop_duplicates(subset=['fabcon_sequence'])
        else: 
            raise NameError('tsv file must have sequence_alignment and germline_alignment_d_mask columns, or sequence_vh column with fully backfilled') 

    tokenizer = PreTrainedTokenizerFast.from_pretrained(tokenizer_path)

    def collate_fn(text, tokenizer=tokenizer):
        # pads to max length in batch
        tokenized_input = tokenizer(
            text,
            return_tensors='pt',
            padding=True,
            max_length=256
        )
        tokenized_input['text'] = text
        return tokenized_input
    
    model = FalconForSequenceClassification.from_pretrained(model_path).to(local_rank)
    model = DDP(model, device_ids=[local_rank])

    sequences = dataset_to_predict_deduplicated['fabcon_sequence'].unique().tolist()

    dataset = AntibodyRepertoireDataset(sequences)
    sampler = DistributedSampler(dataset, num_replicas=world_size, rank=local_rank)

    dataloader = DataLoader(dataset, batch_size=16, sampler=sampler,
                            collate_fn=collate_fn)
    sequences = []
    human_probabilities = []
    with torch.no_grad():
        for batch in tqdm(dataloader):
            inputs = {
                'input_ids': batch['input_ids'].to(local_rank),
                'attention_mask': batch['attention_mask'].to(local_rank)
            }

            o = model(**inputs).logits
            probs = torch.softmax(o.cpu(), dim=1).detach().numpy()  
            
            probs = probs[:, -1] 
            # sequences are stored in batch['text']
            # probabilities are stored in probs
            human_probabilities.extend(probs)
            sequences.extend(batch['text'])
    
    output_df = pd.DataFrame({
        'sequence_vh': sequences,
        'human_probability': human_probabilities
    })

    merged_df = original_columns.merge(
        output_df,
        left_on='fabcon_sequence',
        right_on='sequence_vh',
        how='left'
    )

    # Define conditions
    conditions = [
        merged_df['human_probability'] > 0.99
    ]

    # Define choices for each condition
    choices = ['human']

    # Apply conditions to create 'prediction' column
    merged_df['prediction'] = np.select(
        conditions, choices, default=""
    )

    # Save output file
    if output_file.endswith('.csv'):
        merged_df.to_csv(output_file, index=None)
    elif output_file.endswith('.tsv'):
        merged_df.to_csv(output_file, index=None, sep="\t")
    elif output_file.endswith('.parquet'):
        merged_df.to_parquet(output_file, index=None)
    else:  
        sys.exit('File extension not recognised. Please choose one of .csv, .tsv, or .parquet')
        
    if 'label' in available_columns:
        labels = merged_df['label'].values
        probs = merged_df['human_probability'].values
        probs_binary = [1 if x > 0.5 else 0 for x in probs]
        auc = roc_auc_score(labels, probs)
        aupr = average_precision_score(labels, probs)
        f1 = f1_score(labels, probs_binary)
        precision = precision_score(labels, probs_binary)
        recall = recall_score(labels, probs_binary)
        mcc = matthews_corrcoef(labels, probs_binary)
        
        print('roc_auc:', auc, 'average_precision_score', aupr, 'f1:', f1, 'precision:', precision, 'recall:', recall, 'mcc', mcc)

    cleanup()

# def predict_cpu(
#     input_path: str,
#     output_file: str,
#     tokenizer_path: str,
#     model_path: str
# ): 
#     if input_path.endswith('.csv'):
#         dataset_to_predict = pd.read_csv(input_path)

#         available_columns = dataset_to_predict.columns
#         dataset_to_predict['fabcon_sequence'] = 'Ḣ'+dataset_to_predict['sequence_vh']
#         original_columns = dataset_to_predict.copy()
        
#         # DEDUPLICATE UNIQUE SEQUENCES
#         dataset_to_predict_deduplicated = dataset_to_predict.drop_duplicates(subset=['fabcon_sequence'])
        
#         if 'label' in available_columns:
#             dataset_to_predict_deduplicated = dataset_to_predict_deduplicated[['fabcon_sequence','label']].copy()
#             dataset_to_predict_deduplicated['label'] = dataset_to_predict_deduplicated['label'].astype(int)
#         else:
#             dataset_to_predict_deduplicated = dataset_to_predict_deduplicated[['fabcon_sequence']].copy()
    
#     elif input_path.endswith('.tsv') or input_path.endswith('.parquet'):
#         if input_path.endswith('.tsv'):
#             dataset_to_predict = pd.read_csv(input_path, sep='\t')
#         else:
#             dataset_to_predict = pd.read_parquet(input_path)
#         available_columns = dataset_to_predict.columns

#         if 'sequence_vh' in available_columns:
#             dataset_to_predict['fabcon_sequence'] = 'Ḣ'+dataset_to_predict['sequence_vh']
#             original_columns = dataset_to_predict.copy()
            
#             # DEDUPLICATE UNIQUE SEQUENCES
#             dataset_to_predict_deduplicated = dataset_to_predict.drop_duplicates(subset=['fabcon_sequence'])

#         elif 'sequence_alignment' in available_columns and 'germline_alignment_d_mask' in available_columns:
#             dataset_to_predict['sequence_vh'] = dataset_to_predict.apply(
#             lambda row: get_full_aa_sub(str(row['sequence_alignment']), str(row['germline_alignment_d_mask'])), 
#             axis=1
#             )
#             dataset_to_predict['fabcon_sequence'] = 'Ḣ'+dataset_to_predict['sequence_vh']
#             original_columns = dataset_to_predict.copy()
            
#             # DEDUPLICATE UNIQUE SEQUENCES
#             dataset_to_predict_deduplicated = dataset_to_predict.drop_duplicates(subset=['fabcon_sequence'])
#         else: 
#             raise NameError('tsv file must have sequence_alignment and germline_alignment_d_mask columns, or sequence_vh column with fully backfilled') 
    
#     tokenizer = PreTrainedTokenizerFast.from_pretrained(tokenizer_path)

#     def collate_fn(text, tokenizer=tokenizer):
#         tokenized_input = tokenizer(
#             text,
#             return_tensors='pt',
#             padding=True,
#             max_length=256
#         )
#         tokenized_input['text'] = text
#         return tokenized_input
    
#     device = torch.device('cpu')
#     model = FalconForSequenceClassification.from_pretrained(model_path).to(device)

#     sequences = dataset_to_predict_deduplicated['fabcon_sequence'].unique().tolist()

#     dataset = AntibodyRepertoireDataset(sequences)

#     dataloader = DataLoader(dataset, batch_size=16, 
#                             collate_fn=collate_fn, shuffle=False)
    
#     sequences = []
#     human_probabilities = []
#     with torch.no_grad():
#         for batch in tqdm(dataloader):
#             inputs = {
#                 'input_ids': batch['input_ids'].to(device),
#                 'attention_mask': batch['attention_mask'].to(device)
#             }

#             o = model(**inputs).logits
#             probs = torch.softmax(o.cpu(), dim=1).detach().numpy()  
            
#             probs = probs[:, -1] 
#             human_probabilities.extend(probs)
#             sequences.extend(batch['text'])
    
#     output_df = pd.DataFrame({
#         'sequence_vh': sequences,
#         'human_probability': human_probabilities
#     })

#     merged_df = original_columns.merge(
#         output_df,
#         left_on='fabcon_sequence',
#         right_on='sequence_vh',
#         how='left'
#     )

#     # Define conditions
#     conditions = [
#         merged_df['human_probability'] > 0.99
#     ]

#     # Define choices for each condition
#     choices = ['human']

#     # Apply conditions to create 'prediction' column
#     merged_df['prediction'] = np.select(
#         conditions, choices, default=""
#     )

#     if output_file.endswith('.csv'):
#         merged_df.to_csv(output_file, index=None)
#     elif output_file.endswith('.tsv'):
#         merged_df.to_csv(output_file, index=None, sep="\t")
#     elif output_file.endswith('.parquet'):
#         merged_df.to_parquet(output_file, index=None)
#     else:  
#         sys.exit('File extension not recognised. Please choose one of .csv, .tsv, or .parquet')
        
#     if 'label' in available_columns:
#         labels = merged_df['label'].values
#         probs = merged_df['human_probability'].values
#         probs_binary = [1 if x>0.5 else 0 for x in probs]
#         auc = roc_auc_score(labels, probs)
#         aupr = average_precision_score(labels, probs)
#         f1 = f1_score(labels,probs_binary)
#         precision = precision_score(labels,probs_binary)
#         recall = recall_score(labels,probs_binary)
#         mcc = matthews_corrcoef(labels, probs_binary)
        
#         print('roc_auc:',auc,'average_precision_score',aupr,'f1:',f1,'precision:',precision,'recall:',recall,'mcc',mcc)
def main(
    input_path: str,
    output_file: str,
    # run_mode: str,
    # output_format: str,
    tokenizer_path: str,
    model_path: str,
    local_rank: int = 0,
    world_size: int = 1
):
    # if run_mode == "gpu":
        predict_gpu(
            input_path,
            output_file,
            tokenizer_path,
            model_path,
            local_rank,
            world_size
        )
    # else:
    #     predict_cpu(
    #         input_path,
    #         output_file,
    #         tokenizer_path,
    #         model_path
    #     )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Human Sequence Prediction', 
                                     usage="""torchrun --nproc_per_node=[NUMBER_OF_GPUS] predict.py \
                                     --input_path [PATH_TO_INPUT_TSV_OR_CSV] \
                                     --output_file [OUTPUT FILE NAME] \
                                     --tokenizer_path [PATH_TO_TOKENIZER] \
                                     --model_path [PATH_TO_MODEL] \
                                     --file_source [BOOLEAN]
                                     """)
    parser.add_argument('--input_path', type=str, required=True, help='.csv format file with columns: sequence_vh, label (1 for viral 0 otherwise, optional)')
    parser.add_argument('--output_file', type=str, required=True, help='output file name with extensions. Can be full path or just file name')
    parser.add_argument('--tokenizer_path', type=str, default='./fabcon-small/', help='Path to the tokenizer for your model')
    parser.add_argument('--model_path', type=str, required=True, help='Path to the model')
    # parser.add_argument('--run_mode', type=str, required=True, help='mode. Either cpu or gpu')

    args = parser.parse_args()

    world_size = int(os.environ['LOCAL_WORLD_SIZE'])
    rank = int(os.environ['LOCAL_RANK'])


    main(args.input_path, 
        args.output_file, 
        # args.run_mode,
        args.tokenizer_path, 
        args.model_path,
        rank,
        world_size
        )