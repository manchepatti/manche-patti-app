#!/bin/bash

# Print message
echo "Installing wkhtmltopdf..."

# Download wkhtmltopdf for Ubuntu 20.04 (works with Render)
curl -L -o wkhtml.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.focal_amd64.deb

# Install the downloaded package
dpkg -i wkhtml.deb

# Fix missing dependencies
apt-get update && apt-get install -f -y
