This is a Catalog python program 

to run this program you will need Vagrant and VirtualBox Download VirtualBox: https://www.virtualbox.org/wiki/Download_Old_Builds_5_1

Download Vagrant: https://www.vagrantup.com/downloads.html

Download VM configurations https://github.com/udacity/fullstack-nanodegree-vm

To access Vagrant run the following commands:

```
vagrant up
```

```vagrant ssh```

To run the application
1. Run the database setup using the command
```
python database_setup.py
```
2. Run the seeder to populate the database using the command
```
python seeder.py
```
3.Run the application using the command
```
python application.py
```

access the application on 
```
http://localhost:5000/catalog
```
