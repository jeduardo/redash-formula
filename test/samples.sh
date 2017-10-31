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
salt-call -l debug redash.add_group name='Test Group'

## Adding a member to a new group
salt-call -l debug redash.add_group_member name='Test Group' member='test@test.com'

## Removing a member from an existing group
salt-call -l debug redash.remove_group_member name='Test Group' member='test@test.com'

## Adding a datasource to an existing group
salt-call -l debug redash.add_group_datasource name='Test Group' datasource='Internal Redash PostgreSQL'

## Modifying the properties of an existing datasource
salt-call -l debug redash.alter_group_datasource name='Test Group' datasource='Internal Redash PostgreSQL' view_only=True

## Removing a datasource from an existing group
salt-call -l debug redash.remove_group_datasource datasource='Internal Redash PostgreSQL'

## Adding a user
salt-call -l debug redash.add_user email='test4@test.com' name='Test User 4'

## Updating a user
salt-call -l debug redash.alter_user email='test4@test.com' name='New Name 4'

