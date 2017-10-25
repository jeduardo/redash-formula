#!/bin/bash

# Sample commands for running the test redash instance

## Bring the entire system up
docker-compose up

## Access the embedded psql metadata database
docker-compose exec postgres psql -U postgres

# Sample commands for using the redash module

## Listing datasources
salt-call redash.list_datasources
salt-call redash.list_datasources name='My fancy datasource'

## Creating a datasource
salt-call redash.add_datasource name="Test DS" type="pg" options='{"dbname": "postgres", "host": "postgres", "port": 5432, "user": "postgres"}'

## Removing a datasource
salt-call redash.remove_datasource name='My fancy datasource'

## Changing a datasource
salt-call redash.alter_datasource id=15 name="Test DS" type="pg" options='{"dbname": "postgres-alter", "host": "postgres", "port": 5432, "user": "postgres"}'

## Listing queries
salt-call redash.list_queries
salt-call redash.list_queries name='My fancy query'

## Creating a query
salt-call -l debug redash.add_query name='Console Query' datasource='Test Datasource' description='Test Query' query='select version()'

## Changing a query
salt-call -l debug redash.alter_query name='Console Query 2' datasource='Internal Redash PostgreSQL' description='Updated query' query='select 1'

## Archiving a query
salt-call -l debug redash.archive_query name='Console Query 2'

## Adding a new group
salt-call -l debug redash.add_group name='Test Members' members="['test@test.com']"

## Changing the members of a group
salt-call -l debug redash.alter_group name='Test Members' members="['j.eduardo@gmail.com', 'test2@test2.com']"