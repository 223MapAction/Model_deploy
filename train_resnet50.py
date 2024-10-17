import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from torch.utils.data import Dataset, DataLoader, random_split
from torch.optim import lr_scheduler
import time
import copy
import logging
import pandas as pd
from PIL import Image
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define parameters
data_dir = '/data'  # Replace with your dataset path
annotations_file = 'annotations.csv'  # Your single annotations file
batch_size = 32
num_epochs = 10
feature_extract = False  # If True, only update the reshaped layer params
val_split = 0.2  # 20% of data for validation

# Check for GPU availability
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
logger.info("Using device: %s", device)

class MultiLabelDataset(Dataset):
    def __init__(self, annotations, img_dir, transform=None):
        self.annotations = annotations
        self.img_dir = img_dir
        self.transform = transform
        self.tags = self.get_unique_tags()

    def __len__(self):
        return len(self.annotations)

    def __getitem__(self, idx):
        img_name = os.path.join(self.img_dir, os.path.basename(self.annotations.iloc[idx]['image']))
        image = Image.open(img_name).convert('RGB')
        tags = self.annotations.iloc[idx]['choice'].split(',')
        
        if self.transform:
            image = self.transform(image)
        
        label = torch.zeros(len(self.tags))
        for tag in tags:
            label[self.tags.index(tag.strip())] = 1
        
        return image, label

    def get_unique_tags(self):
        all_tags = [tag.strip() for tags in self.annotations['choice'] for tag in tags.split(',')]
        return sorted(list(set(all_tags)))

def train_model(model, dataloaders, criterion, optimizer, scheduler, num_epochs=25):
    since = time.time()
    best_model_wts = copy.deepcopy(model.state_dict())
    best_f1 = 0.0

    for epoch in range(num_epochs):
        logger.info('Epoch {}/{}'.format(epoch + 1, num_epochs))
        logger.info('-' * 10)

        for phase in ['train', 'val']:
            if phase == 'train':
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            all_preds = []
            all_labels = []

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)

                    if phase == 'train':
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                preds = (torch.sigmoid(outputs) > 0.5).float()
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

            if phase == 'train':
                scheduler.step()

            epoch_loss = running_loss / len(dataloaders[phase].dataset)
            epoch_f1 = calculate_f1_score(np.array(all_preds), np.array(all_labels))

            logger.info('{} Loss: {:.4f} F1: {:.4f}'.format(phase, epoch_loss, epoch_f1))

            if phase == 'val' and epoch_f1 > best_f1:
                best_f1 = epoch_f1
                best_model_wts = copy.deepcopy(model.state_dict())

            if phase == 'val':
                epoch_save_path = f'/cv_model/ResNet50_epoch_{epoch + 1}.pth'
                torch.save(model.state_dict(), epoch_save_path)
                logger.info(f"Model checkpoint saved to {epoch_save_path}")

        logger.info("")

    time_elapsed = time.time() - since
    logger.info('Training complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))
    logger.info('Best val F1: {:.4f}'.format(best_f1))

    model.load_state_dict(best_model_wts)
    return model

def calculate_f1_score(y_pred, y_true):
    tp = np.sum((y_pred == 1) & (y_true == 1), axis=0)
    fp = np.sum((y_pred == 1) & (y_true == 0), axis=0)
    fn = np.sum((y_pred == 0) & (y_true == 1), axis=0)
    
    precision = tp / (tp + fp + 1e-7)
    recall = tp / (tp + fn + 1e-7)
    f1 = 2 * (precision * recall) / (precision + recall + 1e-7)
    return np.mean(f1)

def set_parameter_requires_grad(model, feature_extracting):
    if feature_extracting:
        for param in model.parameters():
            param.requires_grad = False

# Data augmentation and normalization for training and validation
data_transforms = {
    'train': transforms.Compose([
        transforms.RandomResizedCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
    'val': transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

# Load and preprocess the data
logger.info("Loading and preprocessing data")
annotations_df = pd.read_csv(os.path.join(data_dir, annotations_file))

# Create full dataset
full_dataset = MultiLabelDataset(annotations_df, data_dir, transform=data_transforms['train'])

# Split into train and validation sets
train_size = int((1 - val_split) * len(full_dataset))
val_size = len(full_dataset) - train_size
train_dataset, val_dataset = random_split(full_dataset, [train_size, val_size])

# Apply different transforms to validation set
val_dataset.dataset.transform = data_transforms['val']

dataloaders = {
    'train': DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0),
    'val': DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
}

num_tags = len(full_dataset.tags)

# Initialize the model
logger.info("Initializing the model")
model_ft = models.resnet50(weights='IMAGENET1K_V1')
set_parameter_requires_grad(model_ft, feature_extract)
num_ftrs = model_ft.fc.in_features
model_ft.fc = nn.Sequential(
    nn.Linear(num_ftrs, 512),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(512, num_tags)
)

model_ft = model_ft.to(device)

# Define loss function
criterion = nn.BCEWithLogitsLoss()

# Observe that all parameters are being optimized
optimizer_ft = torch.optim.Adam(model_ft.parameters(), lr=0.001)

# Decay LR by a factor of 0.1 every 7 epochs
exp_lr_scheduler = lr_scheduler.StepLR(optimizer_ft, step_size=7, gamma=0.1)

if __name__ == '__main__':
    # Train and evaluate
    logger.info("Starting training process")
    model_ft = train_model(model_ft, dataloaders, criterion, optimizer_ft, exp_lr_scheduler,
                           num_epochs=num_epochs)

    # Save the trained model
    os.makedirs('/cv_model', exist_ok=True)
    torch.save(model_ft.state_dict(), '/cv_model/ResNet50_TCM1.pth')
    logger.info("Model saved to cv_model/ResNet50_TCM1.pth")
