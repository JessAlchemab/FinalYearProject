from Bio.Seq import Seq
import re

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