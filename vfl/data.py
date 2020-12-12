from os import error

import torch
import torchvision
from torchvision import transforms
from torch.utils.data import DataLoader


class Crop(object):
   def __init__(self, top, left, height, width):
        assert (isinstance(top, int) and isinstance(left, int) \
                and isinstance(width, int) and isinstance(height, int), 
                "The params should be all integers"
        )
        self.width = int(width)
        self.height = int(height)
        self.top = int(top)        
        self.left = int(left)

   def __call__(self, img):
       width, height = img.size
       return transforms.functional.crop(img, self.top, self.left, self.height, self.width)


class OneHot(object):
   def __init__(self, size):
        assert isinstance(size, int),  "The size should be an integer"
        self.size = size

   def __call__(self, label):
       onehot = torch.zeros(10)
       onehot[label] = 1
       return onehot



def get_dataloader(side, seed=61, train=True):
    if side.upper() == "A":
        transform = transforms.Compose([
            Crop(0, 0, 28, 14),
            transforms.ToTensor(),
            transforms.Lambda(lambda x: torch.flatten(x)),
        ])
    elif side.upper() == "B":
        transform = transforms.Compose([
            Crop(0, 14, 28, 14),
            transforms.ToTensor(),
            transforms.Lambda(lambda x: torch.flatten(x)),
        ])
    elif side.upper() == "ALL":
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Lambda(lambda x: torch.flatten(x)),
        ])
    else:
        raise error(f"'{side}' side is not available")

    data = torchvision.datasets.MNIST(
        root="../data/", 
        transform=transform, 
        target_transform=OneHot(10),
        train=train, 
        download=True
    )

    return DataLoader(
        data, 
        batch_size=128,
        shuffle=True, 
        drop_last=True,
        generator=torch.Generator().manual_seed(seed)
    )



