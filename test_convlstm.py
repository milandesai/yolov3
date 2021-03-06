import torch
import convlstm

SEQ_LEN = 16
BATCH_SIZE = 8
IN_CHANS = 256
HIDDEN_CHANS = 150
HEIGHT = 32
WIDTH = 32
KERNEL_SIZE=5
LAYERS = 3
DROPOUT = 0.5

size = SEQ_LEN * BATCH_SIZE * IN_CHANS * HEIGHT * WIDTH
data = torch.arange(size).reshape(SEQ_LEN, BATCH_SIZE, IN_CHANS, HEIGHT, WIDTH).float().cuda()
lstm = convlstm.ConvLSTM(IN_CHANS, HIDDEN_CHANS, KERNEL_SIZE, LAYERS, dropout=DROPOUT).cuda()
out = lstm(data)[0]

assert(tuple(out.size()) == (SEQ_LEN, BATCH_SIZE, HIDDEN_CHANS, HEIGHT, WIDTH))
print(out.mean())
