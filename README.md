## Overview

The solution is structured in two folders, CSVProcessor and StorePeople.

CSVProcessor is the first program of the code challenge. It contains the program (csvprocessor.py) that reads data from a csv (full name and email of people), validate it and send it to a  a message broker (RabbitMQ for the broker and Redis as the result backend) using Celery.

StorePeople is the second program of the code challenge. It contains the Celery worker, that reads the jobs from the broker, updates the status of the jobs in the result backend and executes the jobs (according to the tasks.py file), storing in the database the full names and emails, considering the uniqueness of the emails. It uses SQLAlchemy to communicate with the PostgreSQL database and Alembic for the database migrations.

Both programs are dockerized and the StorePeople docker-compose.yml file contains also the services of PostgreSQL, Redis, and RabbitMQ.



## Deploy and usage

First of all, go to the StorePeople folder and run:
```
 docker-compose build
```
Afterwards run the following command to execute the Alembic migrations :
 ```
docker-compose run -e PYTHONPATH=. storepeople ./wait-for-it.sh -t 10 postgres:5432 -- alembic upgrade head
```
The wait-for-it is used to wait for the database to be ready because [it could not be](https://docs.docker.com/compose/startup-order/). 
Then run the folllowing comand to start the PostgresSQL database (exposed in port 5434), the Redis result backend (port 6378) , the RabbitMQ broker (port 5673) and the Celery worker that will execute the tasks: 
```
docker-compose up 
 ```

Then go to the CSVProcessor folder and edit the environment variables in docker-compose.yml file that specifies the connection to the Redis result backend (BACKEND_CONN) and the RabbitMQ broker (BROKER_CONN). If all the deploy is in one single machine you could use the docker0 interface (Docker for Linux) or the host.docker.internal dns name (Docker for Windows or Mac) to specifiy the conection from the csvprocessor docker container to the host machine.

After editing those variables run:
```
docker-compose up 
 ```
 This will build the image and create the folder called data in the host machine, which will be a bind mount for the csv_files folder and logs folder in the docker container. This way you can add the csv files to process in /data/csv_files and finally run:
 ```
docker-compose run csvprocessor python csvprocessor.py -csv csv_files/<name_of_csv>
 ```
 This command will execute the csvprocessor.py in the container csvprocessor.
 
## Future Work
#### Unit Tests
Adding unit tests should be a must for production.
#### Enabling SSL in RabbitMQ
This would be necessary to guarantee a more secure and private transfer of data
#### Use the result backend
The result backend could be useful for checking the status of the tasks in the broker.
#### Validation of Data
The program CSVProcessor is only processing the data in utf-8. A python library such as chardet could be used to guess the encoding of the code an try to process the file in a different encoding.

Furthermore, it only accepts the rows of the CSV  when the full name is not empty and the email is valid according to this python [regex](https://emailregex.com/) which is a bit more strict that the definied by the RFC 5322 (for example, it doesn't allow a domain without a dot). Anyway, the domain existance  could also be checked using the DNS  and also if there is a SMTP server and the e-mail address exists (for example using something like [this](https://github.com/syrusakbary/validate_email)) .