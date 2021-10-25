# Defined in Section 4.6.6

import torch

from torch import nn, optim
from torch.nn import functional as F
from torch.utils.data import Dataset, DataLoader
from torch.nn.utils.rnn import pad_sequence
from collections import defaultdict
from vocab import Vocab
from utils import load_sentence_polarity
import sys

class CnnDataset(Dataset):
    def __init__(self, data):
        self.data = data
    def __len__(self):
        return len(self.data)
    def __getitem__(self, i):
        return self.data[i]

def collate_fn(examples):
    inputs = [torch.tensor(ex[0]) for ex in examples]
    targets = torch.tensor([ex[1] for ex in examples], dtype=torch.long)
    # 对batch内的样本进行padding，使其具有相同长度
    inputs = pad_sequence(inputs, batch_first=True)
    return inputs, targets

class CNN(nn.Module):
    def __init__(self, vocab_size, embedding_dim, filter_size, num_filter, num_class):
        super(CNN, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.conv1d = nn.Conv1d(embedding_dim, num_filter, filter_size, padding=1)
        self.activate = F.relu
        self.linear = nn.Linear(num_filter, num_class)
    def forward(self, inputs):
        embedding = self.embedding(inputs)
        convolution = self.activate(self.conv1d(embedding.permute(0, 2, 1)))
        pooling = F.max_pool1d(convolution, kernel_size=convolution.shape[2])
        outputs = self.linear(pooling.squeeze(dim=2))
        log_probs = F.log_softmax(outputs, dim=1)
        return log_probs

def TrainModel():
    #tqdm是一个Pyth模块，能以进度条的方式显示迭代的进度
    from tqdm.auto import tqdm


    #超参数设置
    embedding_dim = 128
    hidden_dim = 256
    num_class = 2
    batch_size = 32
    num_epoch = 100
    filter_size = 3
    num_filter = 100

    #加载数据
    train_data, test_data, vocab = load_sentence_polarity()
    train_dataset = CnnDataset(train_data)
    test_dataset = CnnDataset(test_data)
    train_data_loader = DataLoader(train_dataset, batch_size=batch_size, collate_fn=collate_fn, shuffle=True)
    test_data_loader = DataLoader(test_dataset, batch_size=1, collate_fn=collate_fn, shuffle=False)

    #加载模型
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = CNN(len(vocab), embedding_dim, filter_size, num_filter, num_class)
    model.to(device) #将模型加载到CPU或GPU设备

    #训练过程
    nll_loss = nn.NLLLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001) #使用Adam优化器

    model.train()
    for epoch in range(num_epoch):
        total_loss = 0
        for batch in tqdm(train_data_loader, desc=f"Training Epoch {epoch}"):
            inputs, targets = [x.to(device) for x in batch]
            log_probs = model(inputs)
            loss = nll_loss(log_probs, targets)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Loss: {total_loss:.2f}")

    #测试过程
    acc = 0
    for batch in tqdm(test_data_loader, desc=f"Testing"):
        inputs, targets = [x.to(device) for x in batch]
        with torch.no_grad():
            output = model(inputs)

            predict=output.argmax(dim=1)
            acc += (predict== targets).sum().item()


    torch.save(model,'Model_cnn.pt')




    #输出在测试集上的准确率
    print(f"Acc: {acc / len(test_data_loader):.2f}")

def get_embemdding(sentences):
    from nltk.corpus import sentence_polarity
    vocab = Vocab.build(sentence_polarity.sents())
    # vocab.convert_tokens_to_ids()
    ids = [vocab.convert_tokens_to_ids(x) for x in sentences]

    embemdding = [torch.tensor(ex) for ex in ids]
    # 对batch内的样本进行padding，使其具有相同长度
    inputs = pad_sequence(embemdding, batch_first=True)
    return inputs
def Predict(sentences):
    # test_data_loader = DataLoader(test_dataset, batch_size=1, collate_fn=collate_fn, shuffle=False)
    # sentence=sentence_polarity.sents()
    input=get_embemdding(sentences)
    model = torch.load('Model_cnn.pt')
    model.eval()
    with torch.no_grad():
        output = torch.argmax(model(input),dim=1)
        rt=[]
        for x in output:
            if (x.item() == 0):
                # print('pos')
                rt.append('pos')
            else:
                # rt.append('neg')
                print("neg")
        return rt


def get_pos_neg_sentence():
    from nltk.corpus import sentence_polarity
    neg = [sentence for sentence in sentence_polarity.sents(categories='neg')[:4000]]
    pos = [sentence for sentence in sentence_polarity.sents(categories='pos')[:4000]]
    return pos,neg

if __name__ =='__main__':


    # TrainModel()

    pos_1=['the', 'rock', 'is', 'destined', 'to', 'be', 'the', '21st', "century's", 'new', '"', 'conan', '"', 'and', 'that', "he's", 'going', 'to', 'make', 'a', 'splash', 'even', 'greater', 'than', 'arnold', 'schwarzenegger', ',', 'jean-claud', 'van', 'damme', 'or', 'steven', 'segal', '.']
    neg_1=['simplistic', ',', 'silly', 'and', 'tedious', '.']
    res=Predict([pos_1,neg_1])
    print(res)
    pass


