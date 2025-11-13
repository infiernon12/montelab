import torch
import numpy as np
from yolox.exp import get_exp

# Create model with 2 classes
exp = get_exp(None, 'yolox-s')
exp.num_classes = 2
model = exp.get_model()
model.eval()

# Test with dummy input
dummy = torch.randn(1, 3, 640, 640)
with torch.no_grad():
    output = model(dummy)

print('Output shape:', output.shape)
print('Expected format: [batch, num_predictions, 5+num_classes]')
print('5 + num_classes =', 5 + exp.num_classes, '(expected last dim)')
print('Last dimension breakdown:')
print('  [0:4] = bbox (x, y, w, h)')
print('  [4:5] = objectness')
print('  [5:7] = class probabilities (2 classes)')
