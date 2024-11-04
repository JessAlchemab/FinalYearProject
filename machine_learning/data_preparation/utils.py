import re
import matplotlib.pyplot as plt
import pandas as pd
import os
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    matthews_corrcoef,
)
from transformers import (
    TrainerCallback,
    Trainer,
)
import numpy as np
import random
import torch
from Bio.Seq import Seq

def plot_v_gene_distributions(df_train, df_val, df_test):
    # Compute value counts for each dataframe
    train_counts = df_train['v_gene'].value_counts()
    val_counts = df_val['v_gene'].value_counts()
    test_counts = df_test['v_gene'].value_counts()

    # Get unique v_gene values across all dataframes
    all_v_genes = pd.concat([train_counts, val_counts, test_counts]).index.unique()

    # Create a figure with subplots
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))
    fig.suptitle('Distribution of v_gene values across datasets', fontsize=16)

    # Plot histograms
    train_counts.reindex(all_v_genes, fill_value=0).plot(kind='bar', ax=ax1, title='Train Dataset')
    val_counts.reindex(all_v_genes, fill_value=0).plot(kind='bar', ax=ax2, title='Test Dataset')
    test_counts.reindex(all_v_genes, fill_value=0).plot(kind='bar', ax=ax3, title='Split Dataset')

    # Adjust layout and display
    plt.tight_layout()
    plt.show()

def binary_metrics(labels, predictions, probabilities,
                   positive_class: int = 1):
    """

    :param labels:
    :param predictions:
    :param probabilities:
    :param positive_class:
    :return:
    """
    return {
        'precision': precision_score(labels, predictions, pos_label=positive_class),
        'recall': recall_score(labels, predictions, pos_label=positive_class),
        'f1': f1_score(labels, predictions, pos_label=positive_class),
        'auc': roc_auc_score(labels, probabilities),
        'aupr': average_precision_score(labels, probabilities, pos_label=positive_class),
        'mcc': matthews_corrcoef(labels, predictions)
    }

def set_seed(seed: int = 42):
    """
    Set all seeds to make results reproducible (deterministic mode).
    When seed is None, disables deterministic mode.
    """
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    np.random.seed(seed)
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

class WeightedTrainer(Trainer):
    seq_weights = torch.tensor([0.53008299, 8.81034483]).cuda()
    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.get('labels')
        # forward pass
        outputs = model(**inputs)
        logits = outputs.get('logits')
        # compute custom loss
        loss_fct = torch.nn.CrossEntropyLoss(weight=self.seq_weights)
        loss = loss_fct(logits, labels)

        return (loss, outputs) if return_outputs else loss

class FocalTrainer(Trainer):
    # set some arbitrary values for now
    alpha = 1.5
    gamma = 1.5
    def compute_loss(self, model, inputs, return_outputs=False):
        labels = inputs.get('labels')
        # forward pass
        outputs = model(**inputs)
        logits = outputs.get('logits')

        bce = torch.nn.functional.cross_entropy(logits,labels,reduction='none')
        pt = torch.exp(-bce)
        loss = (self.alpha * (1 - pt)**self.gamma * bce).mean()

        return (loss, outputs) if return_outputs else loss

class MetricCallback(object):
    """
    A Callback object for binary classification problems
    """
    def __init__(self, label_names):
        self.label_names = label_names

    def compute_metrics(self, preds_out):
        predictions, labels = preds_out
        probs = torch.softmax(torch.from_numpy(predictions), dim=1).detach().numpy()
        probs = probs[:, -1]
        predictions = predictions.argmax(1)
        return binary_metrics(labels, predictions, probs)



# Callback to unfreeze the encoder during training
class UnfreezingCallback(TrainerCallback):
    def __init__(self, unfreeze_epoch, trainer, model_config):
        self.model_config = model_config
        self.trainer = trainer
        self.unfreeze_epoch = unfreeze_epoch
        self.current_epoch = 0
    def on_epoch_begin(self, args, state, control, **kwargs):
        if state.epoch >= self.unfreeze_epoch:
            self.current_epoch += 1
            self.unfreeze_model()

    # Unfreeze before saving to avoid unexpected behaviour
    def on_save(self, args, state, control, **kwargs):
        for name, param in self.trainer.model.named_parameters():
            param.requires_grad = True
    def unfreeze_model(self):
        for name, param in self.trainer.model.named_parameters():
            param.requires_grad = True


def get_full_aa_sub(aln_seq: str, germ_seq: str) -> str:
    
    """Method used by Jake which works better than frameshifting

    Parameters
    ----------
    aln_seq : str
        sequence_alignment value.
    germ_seq : str
        germline_alignment_d_mask value.
    
    Returns:
        str: amino acid sequence
    """
    ALIGNMENT_SEQUENCE_REPLACEMENT_PATTERN = re.compile("^\\.*")

    the_seq = ALIGNMENT_SEQUENCE_REPLACEMENT_PATTERN.sub("", aln_seq)
    cut_length = len(aln_seq) - len(the_seq)
    pasted = germ_seq[:int(cut_length)] + the_seq
    
    return str(Seq(pasted.replace(".", "").replace("-", "")).translate())