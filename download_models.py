import subprocess
import os
import gdown

default_models = [
    {"fileId": "1Cv-7LaBFUC5tf8yfLuQO3SRRYPbvZApQ", "path": "./models/female-1"},
    {"fileId": "15Ho6G7E2qDB4XfQqyE2MP3uxWVeIyr1g", "path": "./models/female-2"},
    {"fileId": "1mj49EiJNFwqOJeJusTiL_zoCV1R7PGAn", "path": "./models/female-3"},
    {"fileId": "12tZ4ftvYDaVoeoceFOq5XnAWe1cJrYCt", "path": "./models/female-4"},
    {"fileId": "1MXYYJfFcykXEpmR3g-koc18PdxD4LpIC", "path": "./models/male-1"},
    {"fileId": "19xYv3wENuEXAhV-3LBbwqMSQ2gsDGKJt", "path": "./models/male-2"},
    {"fileId": "1EhulXaigTfnjw3RTFUZsKVVhD7zyxwWC", "path": "./models/male-3"},
]

def download_file(id, output):
    print(id)
    if not os.path.exists(output):
        os.makedirs(os.path.dirname(output), exist_ok=True)
        gdown.download(id=id, output=output)
    else:
         print(f"{output} model available.")

for model in default_models:
   download_file(model["fileId"], f'{model["path"]}/model.pth')