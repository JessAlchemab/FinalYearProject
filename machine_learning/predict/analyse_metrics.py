import pandas as pd
import numpy as np
from pathlib import Path
from aws_handler import upload_metrics_to_rds
import argparse
import json

def analyze_antibody_data(file_path):
    """
    Analyze antibody sequencing data from a parquet or tsv file.
    
    Args:
        file_path (str): Path to the input file
        
    Returns:
        dict: Dictionary containing the computed metrics
    """
    # Read the file based on extension
    path = Path(file_path)
    if path.suffix == '.parquet':
        df = pd.read_parquet(file_path)
    elif path.suffix in ['.tsv', '.txt']:
        df = pd.read_csv(file_path, sep='\t')
    else:
        raise ValueError("File must be .parquet or .tsv/.txt")
    
    metrics = {}
    
    # Store total number of rows
    metrics['total_rows'] = len(df)
    
    # V gene metrics
    if 'v_call' in df.columns:
        metrics['IGHV4_34_percentage'] = (df['v_call'].str.contains('IGHV4-34', na=False) * 100).mean()
        metrics['IGHV3_30_percentage'] = (df['v_call'].str.contains('IGHV3-30', na=False) * 100).mean()
    else:
        metrics['IGHV4_34_percentage'] = None
        metrics['IGHV3_30_percentage'] = None
    
    # Constant region metrics
    if 'c_call' in df.columns:
        metrics['IGHG_percentage'] = (df['c_call'].str.startswith('IGHG', na=False) * 100).mean()
        
        # Individual IGHG subclass percentages
        for subclass in ['IGHG1', 'IGHG2', 'IGHG3', 'IGHG4']:
            metrics[f'{subclass}_percentage'] = (df['c_call'] == subclass).mean() * 100
    else:
        metrics['IGHG_percentage'] = None
        for subclass in ['IGHG1', 'IGHG2', 'IGHG3', 'IGHG4']:
            metrics[f'{subclass}_percentage'] = None
    
    # CDR3 length
    if 'cdr3_aa' in df.columns:
        metrics['average_cdr3_length'] = df['cdr3_aa'].str.len().mean()
    else:
        metrics['average_cdr3_length'] = None
    
    # Mu count
    if 'mu_count_total' in df.columns:
        metrics['average_mu_count'] = df['mu_count_total'].mean()
    else:
        metrics['average_mu_count'] = None
    
    # Prediction percentage
    if 'prediction' in df.columns:
        metrics['human_prediction_percentage'] = (df['prediction'] == 'human').mean() * 100
    else:
        metrics['human_prediction_percentage'] = None
    
    # Human probability histogram data
    if 'human_probability' in df.columns:
        # Create bins from 0 to 1 with step size 0.05
        bins = np.arange(0, 1.05, 0.05)
        
        # Create histogram data
        hist_data = pd.cut(df['human_probability'], 
                          bins=bins, 
                          right=False,
                          labels=[f"{bins[i]:.2f}-{bins[i+1]:.2f}" for i in range(len(bins)-1)])
        
        metrics['probability_histogram'] = json.dumps(hist_data.value_counts().to_dict())
    else:
        metrics['probability_histogram'] = None
    
    return metrics

def format_metrics(metrics):
    """
    Format metrics for pretty printing
    """
    formatted = "Analysis Results:\n"
    formatted += f"Total rows: {metrics['total_rows']}\n\n"
    
    # V gene metrics
    formatted += "V Gene Metrics:\n"
    formatted += f"IGHV4-34: {metrics['IGHV4_34_percentage']:.2f}%\n" if metrics['IGHV4_34_percentage'] is not None else "IGHV4-34: N/A\n"
    formatted += f"IGHV3-30: {metrics['IGHV3_30_percentage']:.2f}%\n" if metrics['IGHV3_30_percentage'] is not None else "IGHV3-30: N/A\n\n"
    
    # Constant region metrics
    formatted += "Constant Region Metrics:\n"
    formatted += f"Total IGHG: {metrics['IGHG_percentage']:.2f}%\n" if metrics['IGHG_percentage'] is not None else "Total IGHG: N/A\n"
    for subclass in ['IGHG1', 'IGHG2', 'IGHG3', 'IGHG4']:
        key = f'{subclass}_percentage'
        formatted += f"{subclass}: {metrics[key]:.2f}%\n" if metrics[key] is not None else f"{subclass}: N/A\n"
    formatted += "\n"
    
    # Other metrics
    formatted += "Other Metrics:\n"
    formatted += f"Average CDR3 length: {metrics['average_cdr3_length']:.2f}\n" if metrics['average_cdr3_length'] is not None else "Average CDR3 length: N/A\n"
    formatted += f"Average mu count: {metrics['average_mu_count']:.2f}\n" if metrics['average_mu_count'] is not None else "Average mu count: N/A\n"
    formatted += f"Human prediction percentage: {metrics['human_prediction_percentage']:.2f}%\n" if metrics['human_prediction_percentage'] is not None else "Human prediction percentage: N/A\n"
    
    # Histogram data
    if metrics['probability_histogram'] is not None:
        formatted += "\nHuman Probability Distribution:\n"
        for bin_range, count in sorted(metrics['probability_histogram'].items()):
            formatted += f"{bin_range}: {count}\n"
    
    return formatted

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Analyze antibody sequencing data from parquet or TSV files.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--file_path', 
                       help='Path to the input file (parquet or TSV format)')
    parser.add_argument('--rds_table', help='RDS table to add metrics to')
    parser.add_argument('--hash_id', help='hash id from zeus to use as primary key')
    parser.add_argument('--output', '-o',
                       help='Path to save output as JSON (optional)',
                       default=None)
    parser.add_argument('--quiet', '-q',
                       action='store_true',
                       help='Suppress printed output')
    
    args = parser.parse_args()
    try:
        metrics = analyze_antibody_data(args.file_path)
        if not args.quiet:
            print(format_metrics(metrics))
        upload_metrics_to_rds(metrics, args.hash_id, args.rds_table)
    except Exception as e:
        print(f"Error analyzing file: {str(e)}")