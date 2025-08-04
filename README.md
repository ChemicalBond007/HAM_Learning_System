# HAM_Learning_System
> First of all, this is a playful project that is very fast-developed. So __do not__ try to use this in production field.

## System Requirement
The developing environment of the Web app is on Ubuntu, so we recommend using a Linux Server to run the demo.

## Software Requirement
To prepare for the demo, you should have python (preferably >= 3.11) installed and package requirements meet (They are listed in the ```./ham_radio_app/requirements.txt```) to ensure that the demo runs properly.

### Install MongoDB
However, quite a lot of servers don't have MongoDB installed. So we provided the following solution that you may try.
1. Update your system packages
```bash
sudo apt-get update
```
2. Import the MongoDB Public GPG Key
```bash
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
```
3. For Ubuntu 22.04, we provide the following solution
```bash
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
```
Other version's information should be available at [relevant sites](https://repo.mongodb.org/apt/).

4. Now, you can install the MongoDB
```bash
sudo apt-get update
sudo apt-get install -y mongodb-org
```

## How can I start the demo?

### First step to do
Meet the basic requirements !!!

### What's next?
Start the MongoDB.
```bash
sudo systemctl start mongod
```
The following bash command may also be useful for docker containers or WSL users.
```bash
sudo mongod --config /etc/mongod.conf --fork
```
You may check the status by using the following command:
```bash
mongosh
```
You may also want the MongoDB to start automatically:
```bash
sudo systemctl enable mongod
```
Sometimes you may want to verify its status:
```bash
sudo systemctl status mongod
```

### It seems that I've done with MongoDB setup
You may think like this, but it's not always true. For security reasons, you may be willing to create an administrative user to secure your database. (Although it is optional)

### Configure your paramenters
Open the ```.env``` file to satisfy your local environment.

### Start the demo
Navigate to ```./ham_radio_app``` and initialise your database by running:
```bash
python ./import_data.py
```
This should initialise your database system.  
You can then run the following bash command:
```bash
flask run
```
This should start the flask server.  
For now, you've started this Web app successfully.   
Congratulations!