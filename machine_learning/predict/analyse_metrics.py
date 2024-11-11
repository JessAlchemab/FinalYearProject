# Script to get metrics from the output airr file and put them into dynamodb
import pandas as pd
import argparse
from aws_handler import upload_metrics_to_dynamodb

def calculate_metrics(file_path: str):
    # Load file based on extension
    if file_path.endswith('.parquet'):
        df = pd.read_parquet(file_path)
    elif file_path.endswith('.tsv'):
        df = pd.read_csv(file_path, sep='\t')
    else:
        raise ValueError("File must be either a parquet or TSV format.")
    
    # Initialize results dictionary
    results = {}
    igg_subclasses = ['IGHG1', 'IGHG2', 'IGHG3', 'IGHG4']
    # Total number of rows
    total_rows = len(df)
    results['total_rows'] = total_rows

    # Check for the presence of each column and calculate each metric if available
    if 'v_call' in df.columns:
        # Percentage of rows where 'v_call' contains 'IGHV3-34'
        results['v_call_IGHV3-34_percent'] = (
            df['v_call'].str.contains('IGHV3-34', na=False).mean() * 100
        )
        
        # Percentage of rows where 'v_call' contains 'IGHV3-30'
        results['v_call_IGHV3-30_percent'] = (
            df['v_call'].str.contains('IGHV3-30', na=False).mean() * 100
        )
    else:
        results['v_call_IGHV3-34_percent'] = None
        results['v_call_IGHV3-30_percent'] = None

    if 'c_call' in df.columns:
        # Percentage of rows where 'c_call' starts with 'IGHG'
        results['c_call_IGHG_start_percent'] = (
            df['c_call'].str.startswith('IGHG', na=False).mean() * 100
        )
        
        # Percentage of rows where 'c_call' equals 'IGHG1', 'IGHG2', 'IGHG3', or 'IGHG4'
        for igg_type in igg_subclasses:
            results[f'c_call_{igg_type}_percent'] = (
                (df['c_call'] == igg_type).mean() * 100
            )
    else:
        results['c_call_IGHG_start_percent'] = None
        for igg_type in igg_subclasses:
            results[f'c_call_{igg_type}_percent'] = None

    if 'cdr3_aa' in df.columns:
        # Average length of strings in 'cdr3_aa'
        results['cdr3_aa_avg_length'] = df['cdr3_aa'].dropna().str.len().mean()
    else:
        results['cdr3_aa_avg_length'] = None

    if 'mu_count_total' in df.columns:
        # Average of 'mu_count_total'
        results['mu_count_total_avg'] = df['mu_count_total'].dropna().mean()
    else:
        results['mu_count_total_avg'] = None

    # Display results
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate specific metrics from a parquet or TSV file.")
    parser.add_argument("file_path", type=str, help="Path to the input parquet or TSV file")
    parser.add_argument("db_name", type=str, help="Name of dynamoDB table to add metrics too")
    parser.add_argument("hash_id", type=str, help="Hash ID output by Zeus")
    args = parser.parse_args()
    metrics = calculate_metrics(args.file_path)
    upload_metrics_to_dynamodb(metrics, args.db_name, args.hash_id)
