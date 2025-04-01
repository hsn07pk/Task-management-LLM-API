# PWP SPRING 2025
# PROJECT NAME
# Group information
* Syed Abdullah Hassan syehassa24@student.oulu.fi
* Muhammad Hassan Sohail. hassan.sohail@student.oulu.fi
* Uswah Batool.	 uswah.batool@student.oulu.fi
* Mathéo Morin. matheo.morin@student.oulu.fi
	



__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint, instructions on how to setup and run the client, instructions on how to setup and run the axiliary service and instructions on how to deploy the api in a production environment__


# PostgreSQL Docker Setup 

## Prerequisites
Ensure you have Docker installed on your system. You can check by running:

```sh
docker --version
```

## Step 1: Run PostgreSQL Container
Start a PostgreSQL container using the official PostgreSQL image:

```sh
docker-compose up -d
```
This will download a PostSQL instance and run the docker container, also copy the setup database script and run that script inside that container and create the db & populate it with data. 

## Step 2: Verify the Database and check it's data

```sh
docker exec -it my_postgres_db bash
```
You will be inside the docker instance, now you need to go inside the DB

```sh
psql -U admin -d task_management_db
```
Running this command inside the docker container will take you inside the DB: task_management_db

Now you can run to see all the tables
```sh
\dt
```

You can run any of these commands to see the data inside those tables. 
```sh
SELECT * FROM "USER";
SELECT * FROM TEAM;
SELECT * FROM PROJECT;
SELECT * FROM TASK;
SELECT * FROM CATEGORY;
SELECT * FROM TEAM_MEMBERSHIP;
```

You can run to stop the db instance

```sh
docker stop my_postgres_db
```


You can run to remove the db container instance

```sh
docker rm my_postgres_db
```


# The Models and Flask App

The models in python are in the file models.py with all the classes present in the db and their helper functions and a app.py that calls the functions when you run the app.py flask app and call the http://127.0.0.1:5000/test. When the test endpoint is called it tried to add some users and then update and also delete that user just to show that the helper functions are working. And it returns the remaining users.


To run the test cases we need to run 


```sh
pytest --html=reports/report.html --self-contained-html

```
