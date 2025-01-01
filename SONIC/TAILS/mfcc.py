from functools import partial
import logging
import torch
from torchaudio.transforms import MFCC
import torch.nn.functional as F
from tqdm.auto import tqdm
import SONIC.CREAM as CREAM
from functools import partial

N_MFCC = 104  # Number of MFCC coefficients

def mfcc_embedding(waveform: torch.Tensor, device: torch.device) -> torch.Tensor:
    """
    Compute MFCC embeddings for the given waveform.
    Parameters:
        waveform (torch.Tensor): Input waveform.
        device (torch.device): Device to use for computation.
    Returns:
        torch.Tensor: MFCC embedding.
    """
    mfcc = MFCC(n_mfcc=N_MFCC, melkwargs={'n_fft': 2048, 'hop_length': 512, 'n_mels': 128}).to(device)
    waveform = waveform.to(device)
    mfcc_full = mfcc(waveform)
    embedding = mfcc_full.mean(dim=-1)
    return embedding

def get_embeddings(audio_dir: str, batch_size: int = 32) -> list:
    """
    Compute MFCC embeddings for all audio files in the given directory.
    Parameters:
        audio_dir (str): Path to the directory containing audio files.
        batch_size (int): Number of audio files to process in parallel.
    Returns:
        list: List of tuples containing the audio file path and MFCC embedding.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    mfcc_fn = partial(mfcc_embedding, device=device)
    dataloader = CREAM.dataset.init_dataset(audio_dir, batch_size=batch_size, transform=mfcc_fn)
    embeddings = []
    logging.info("Computing MFCC embeddings")
    logging.info(f"Using device: {device}")
    for i, batch in tqdm(enumerate(dataloader), desc="Extracting embeddings", total=len(dataloader)):
        logging.info(f"Processing batch {i + 1}/{len(dataloader)}")
        for audio_path, mfcc in zip(*batch):
            embeddings.append((audio_path, mfcc.cpu().numpy()))
            logging.info(f"Computed MFCC embedding for {audio_path}")

    return embeddings