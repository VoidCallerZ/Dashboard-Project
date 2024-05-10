#!/bin/bash

#Install Dashboard package
wget https://github.com/VoidCallerZ/Dashboard-Project/raw/main/Dashboard.zip
unzip Dashboard.zip
rm Dashboard.zip

#Install Google Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt install -f
rm google-chrome-stable_current_amd64.deb

#Fetch Chrome version
chrome_version=$(google-chrome --version | cut -d ' ' -f 3)

#Install Chromedriver
wget https://storage.googleapis.com/chrome-for-testing-public/$chrome_version/linux64/chromedriver-linux64.zip
unzip chromedriver-linux64.zip
sudo mv chromedriver-linux64/chromedriver /usr/bin
sudo chown root:root /usr/bin/chromedriver
sudo chmod 0755 /usr/bin/chromedriver
rm chromedriver-linux64.zip
rm chromedriver-linux64 -r

#Install dependencies
sudo apt update
sudo apt install -y xdotool python3 python3-pip
sudo pip install -r requirements.txt

#Make run_dashboard.sh exectable
sudo chmod +x run_dashboard.sh

#Setup auto start on boot
mkdir ~/.config/autostart

content="[Desktop Entry]
Type=Application
Name=PWA Dashboard Application
Exec=/home/rick/Documents/run_dashboard.sh"

echo "$content" > ~/.config/autostart/dashboard.desktop