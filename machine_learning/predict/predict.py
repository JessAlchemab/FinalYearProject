import pandas as pd
import numpy as np
import argparse
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
import os 
from datasets import (
    Dataset
)
from transformers import (
    PreTrainedTokenizerFast,
    FalconForSequenceClassification,
)
from tqdm import tqdm
from torch.utils.data import DataLoader, Dataset, DistributedSampler
from aws_handler import download_s3_object, upload_file_to_s3

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

def main(
    input_path: str,
    output_file: str,
    output_format: str,
    tokenizer_path: str,
    model_path: str,
    local_rank: int = 0,
    world_size: int = 1
):
    setup(local_rank,
          world_size)

    if input_path.endswith('.csv'):
        #LOAD DATASET
        dataset_to_predict=pd.read_csv(input_path)

        available_columns=dataset_to_predict.columns
        dataset_to_predict['fabcon_sequence']='Ḣ'+dataset_to_predict['sequence_vh']
        original_columns = dataset_to_predict.copy()
        if 'label' in available_columns:
            dataset_to_predict=dataset_to_predict[['fabcon_sequence','label']].copy()
            dataset_to_predict['label'] = dataset_to_predict['label'].astype(int)
        else:
            dataset_to_predict=dataset_to_predict[['fabcon_sequence']].copy()
    
    # output from pipeline is tsv files
    elif input_path.endswith('.tsv') or input_path.endswith('.parquet'):
        if input_path.endswith('.tsv'):
            dataset_to_predict=pd.read_csv(input_path, sep='\t')
        else:
            dataset_to_predict=pd.read_parquet(input_path)
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
            dataset_to_predict['fabcon_sequence']='Ḣ'+dataset_to_predict['sequence_vh']
            original_columns = dataset_to_predict.copy()

    # dataset_to_predict['sequence']='Ḣ'+dataset_to_predict['sequence_vh']
    
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

    sequences = dataset_to_predict['fabcon_sequence'].unique().tolist()

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

    # Apply conditions to create 'human_viral_prediction' column
    merged_df['prediction'] = np.select(
        conditions, choices, default=""
    )
    # file_path = input_path.split("/")[:-1].join("/")

    if "csv" in output_format:
        merged_df.to_csv(f"{output_file}.csv", index=None)
    elif "tsv" in output_format:
        merged_df.to_csv(f"{output_file}.tsv", index=None, sep="\t")
    elif "parquet" in output_format:
        merged_df.to_parquet(f"{output_file}.parquet", index=None)

    if 'label' in available_columns:
        labels=merged_df['label'].values
        probs=merged_df['human_probability'].values
        probs_binary=[1 if x>0.5 else 0 for x in probs]
        auc=roc_auc_score(labels, probs)
        aupr=average_precision_score(labels, probs)
        f1=f1_score(labels,probs_binary)
        precision=precision_score(labels,probs_binary)
        recall=recall_score(labels,probs_binary)
        mcc = matthews_corrcoef(labels, probs_binary)
        
        print('roc_auc:',auc,'average_precision_score',aupr,'f1:',f1,'precision:',precision,'recall:',recall,'mcc',mcc)

    cleanup()

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
    parser.add_argument('--output_file', type=str, required=False, default='autoantibody_annotated', help='output file name without extensions. Can be full path or just file name')
    parser.add_argument('--output_format', type=str, required=True, default='tsv', choices=['tsv', 'csv', 'parquet'], help='output file format. tsv or csv or parquet.')
    parser.add_argument('--tokenizer_path', type=str, default='./fabcon-small/', help='Path to the tokenizer for your model')
    parser.add_argument('--model_path', type=str, required=True, help='Path to the model')
    # parser.add_argument('--file_source', type=str, default='local', choices=['local', 'aws'], help='Source of the input file: local or aws')

    args = parser.parse_args()

    world_size = int(os.environ['LOCAL_WORLD_SIZE'])
    rank = int(os.environ['LOCAL_RANK'])


    # if args.file_source == 'local':
    main(args.input_path, 
        args.output_file, 
        args.output_format,
        args.tokenizer_path, 
        args.model_path,
        rank,
        world_size
        )
    
    # else:
        # download s3 file to specified path, might need to change path later but for now /app/files
        # file_name = args.input_path.split("/")[-1]
        # download_s3_object(args.input_path, '/app/files')
        # input_local_path=f"/app/files/{file_name}"
        # output_local_path=f"/app/files/autoantibody_annotated_{file_name}"
        # output_s3_path=f"s3://alchemab-scratch/jess_scratch/autoantibody_classifier/outputs/autoantibody_annotated_{file_name}"
        # main(input_local_path, 
        #     output_local_path, 
        #     args.tokenizer_path, 
        #     args.model_path,
        #     rank,
        #     world_size
        #     )
        # # upload filled in tsv or csv to specified s3 path
        # upload_file_to_s3(output_local_path, output_s3_path)