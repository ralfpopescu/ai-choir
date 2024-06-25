import subprocess
import os
import gdown

default_models = [
    {"fileId": "https://drive.google.com/uc?id=1Cv-7LaBFUC5tf8yfLuQO3SRRYPbvZApQ", "path": "./models/female-1"},
    {"fileId": "https://drive.google.com/uc?id=15Ho6G7E2qDB4XfQqyE2MP3uxWVeIyr1g", "path": "./models/female-2"},
    {"fileId": "https://drive.google.com/uc?id=1mj49EiJNFwqOJeJusTiL_zoCV1R7PGAn", "path": "./models/female-3"},
    {"fileId": "https://drive.google.com/uc?id=12tZ4ftvYDaVoeoceFOq5XnAWe1cJrYCt", "path": "./models/female-4"},
    {"fileId": "https://drive.google.com/uc?id=1MXYYJfFcykXEpmR3g-koc18PdxD4LpIC", "path": "./models/male-1"},
    {"fileId": "https://drive.google.com/uc?id=19xYv3wENuEXAhV-3LBbwqMSQ2gsDGKJt", "path": "./models/male-2"},
    {"fileId": "https://drive.google.com/uc?id=1EhulXaigTfnjw3RTFUZsKVVhD7zyxwWC", "path": "./models/male-3"},
]

def download_file(id, output):
    gdown.download(id=id, output=output)

for model in default_models:
   gdown.download(model["fileId"], f'{model["path"]}/model.pth')