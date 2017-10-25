==============
redash-formula
==============

A saltstack formula created to manage `Redash
<https://www.redash.io>`_ on a single machine or in a machine cluster.


Available states
================

.. contents::
    :local:

``manage``
------------

Used to apply management configuration over a Redash deployment, creating
datasources and queries as needed.

Implementation roadmap
======================

- User management
	- List users (DONE)
	- Modify users
	- Remove users
- Group management 
	- List groups (DONE)
	- Modify groups (DONE)
		- Add/Remove users (DONE)
		- Add/Remove permissions (NOT POSSIBLE)
	- Remove groups (DONE)
	- Add/Remove datasources 
- Datasource management 
	- List datasources (DONE)
	- Add datasources (DONE)
	- Remove datasources (DONE)
- Query management (DONE)
	- Add queries (DONE)
	- Modify queries (DONE)
	- Archive (delete) queries (DONE)
- Alert destination management
	- Create alert destinations
	- Remove alert destinations
- Alert
	- Create new alerts
	- Modify alerts
	- Remove alerts
- Dashboard management
	- Create dashboard
	- Modify dashboard
	- Remove dashboard