# predict.py  -  Single-tile inference helper
import os
import numpy as np
import torch
from model import UNet

THRESHOLD = 0.45

def load_model(checkpoint_path, device=None):
    """Load U-Net model from checkpoint."""
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = UNet(n_channels=1, n_classes=1, bilinear=True).to(device)
    state = torch.load(checkpoint_path, map_location=device, weights_only=False)
    if isinstance(state, dict) and 'model_state_dict' in state:
        model.load_state_dict(state['model_state_dict'])
    else:
        model.load_state_dict(state)
    model.eval()
    return model, device

def predict_tile(model, tile_np, device, threshold=THRESHOLD):
    """Run inference on a single 512x512 float32 tile (values in [0,1]).
    Returns (prob_map, binary_mask)."""
    tensor = torch.from_numpy(tile_np).unsqueeze(0).unsqueeze(0).float().to(device)
    with torch.no_grad():
        logits = model(tensor)
        prob = torch.sigmoid(logits).squeeze().cpu().numpy()
    mask = (prob >= threshold).astype(np.uint8) * 255
    return prob, mask
