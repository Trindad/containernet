from collections import OrderedDict
from torch import nn

class Model(nn.Module):
    def __init__(self):
        super().__init__()

        self.dense_layer = nn.Sequential(OrderedDict([
            ('dense1', nn.Linear(14*28, 128)), # 28x28 / 2 because each one will have half of the data
            ('relu1',  nn.ReLU()),
            ('drop1',  nn.Dropout(p=0.5)),

            ('dense2', nn.Linear(128, 64)),
            ('relu2',  nn.ReLU()),
            ('drop2',  nn.Dropout(p=0.5)),

            ('dense3', nn.Linear(64, 10)),
            ('softmax', nn.Softmax()),
        ]))

    def forward(self, x):
        return self.dense_layer(x) / 2