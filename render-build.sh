<<<<<<< HEAD
#!/bin/bash

echo "👷 Installing wkhtmltopdf..."
curl -L -o wkhtml.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.focal_amd64.deb
dpkg -i wkhtml.deb || true
apt-get update && apt-get install -f -y
=======
#!/bin/bash

echo "👷 Installing wkhtmltopdf..."
curl -L -o wkhtml.deb https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.focal_amd64.deb
dpkg -i wkhtml.deb || true
apt-get update && apt-get install -f -y
>>>>>>> f524e1591a8dbdefaba05cbc083bec0ddc16b284
