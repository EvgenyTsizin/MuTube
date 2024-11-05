#!/bin/bash

# Clone the repository
git clone https://github.com/simsim314/one-click-dense-pose.git

# Navigate into the repository directory
cd one-click-dense-pose

# Install the required Python packages
pip install -r requirements.txt

# Download the necessary models
sh download-models.sh

