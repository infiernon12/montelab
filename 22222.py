import torch

ckpt = torch.load('epoch_50_ckpt.pth', map_location='cpu')
print("Keys:", ckpt.keys() if isinstance(ckpt, dict) else "Not a dict")

if isinstance(ckpt, dict) and 'model' in ckpt:
    print("\nEpoch:", ckpt.get('epoch', 'N/A'))
    print("Best AP:", ckpt.get('best_ap', 'N/A'))