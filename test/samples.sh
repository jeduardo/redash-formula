#!/bin/bash

# Sample commands for using the redash module

## Listing datasources
salt-call redash.list_datasources

## Creating a datasource
salt-call redash.add_datasource name="Test DS" type="pg" options='{"dbname": "postgres", "host": "postgres", "port": 5432, "user": "postgres"}'

## Removing a datasource
salt-call redash.remove_datasource id=15

## Changing a datasource
salt-call redash.alter_datasource id=15 name="Test DS" type="pg" options='{"dbname": "postgres-alter", "host": "postgres", "port": 5432, "user": "postgres"}'
