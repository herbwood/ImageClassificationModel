import torch
import torchvision.transforms as transforms
from model import VGG
from dataloader import Cifar10Dataset
import torch.nn.functional as F
from torch.utils.data import DataLoader
import argparse

parser = argparse.ArgumentParser(description="VGG Training")
parser.add_argument("--batch", "--batch-size", default=128, type=int,
                    metavar="B", help='mini-batch size')
parser.add_argument('--workers', '--num-workers', default=2, type=int, metavar='W',
                    help='number of data loading workers')

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def topkaccuracy(output, target, topk=(1,)):
    maxk = max(topk)
    batch_size = target.size(0)

    _, pred = output.topk(maxk, 1, True, True)
    pred = pred.t()
    correct = pred.eq(target.view(1, -1).expand_as(pred))

    res = []
    for k in topk:
        correct_k = correct[:k].reshape(-1).float().sum(0)
        res.append(correct_k.mul_(100.0 / batch_size))
    return res

def evalute_fn(model, test_loader):

    model.eval()
    test_loss, correct, prec1, prec5 = 0, 0, 0, 0

    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(DEVICE), target.to(DEVICE)

            with torch.set_grad_enabled(False):
                output = model(data)

                test_loss += F.cross_entropy(output, target, reduction='sum').item()
                pred = output.max(1, keepdim=True)[1]
                correct += pred.eq(target.view_as(pred)).sum().item()

                prec1 += topkaccuracy(output.data, target)[0]
                prec5 += topkaccuracy(output.data, target, topk=(5, ))[0]

    test_loss /= len(test_loader.dataset)
    test_accuracy = 100. * correct / len(test_loader.dataset)
    test_prec1 = prec1 / len(test_loader)
    test_prec5 = prec5 / len(test_loader)

    return test_loss, test_accuracy, test_prec1, test_prec5

def evaluate():
    args = parser.parse_args()

    model = VGG().to(DEVICE)
    state = torch.load("./model.pt")
    model.load_state_dict(state['model_state_dict'])

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
    ])

    test_dataset = Cifar10Dataset(train=False, transform=transform)

    test_loader = DataLoader(dataset=test_dataset,
                             batch_size=args.batch,
                             num_workers=args.workers,
                             shuffle=False)

    test_loss, test_accuracy, test_prec1, test_prec5 = evalute_fn(model, test_loader)

    print(f"Loss : {test_loss:.4f}")
    print(f"Accuracy {test_accuracy:.2f}%")
    print(f"Top-1 Accuracy : {test_prec1:.2f}%")
    print(f"Top-5 Accuracy : {test_prec5:.2f}%")

if __name__ == "__main__":
    # python evaluate.py --batch 128 --workers 2
    evaluate()