{%- for user, properties in salt['pillar.get']('redash:users').items() %}

redash user {{ user }}:
  redash.user_present:
    - email: {{ user }}
    - name: {{ properties['name'] }}

{%- endfor %}

{%- for group, properties in salt['pillar.get']('redash:groups').items() %}

redash group {{ group }}:
{%- if not properties.get('absent', False) %}
  redash.group_present:
    - name: {{ group }}
    {%- set datasources = properties.get('datasources', {}) %}
    {%- set members = properties.get('members', []) %}
    {%- if datasources %}
    - datasources: {{ datasources }}
    {%- endif %}
    {%- if members %}
    - members: {{ properties['members'] }}
    {%- endif %}
    {%- if members or datasources %} 
    - require:
    {%- for datasource in datasources %}
      - redash: redash datasource {{ datasource }}
    {%- endfor %}
    {%- for member in members %}
      - redash: redash user {{ member }}
    {%- endfor %} 
    {%- endif %}
{%- else %}
  redash.group_absent:
    - name: {{ group }}
{%- endif %}

{%- endfor %}


{%- for datasource, properties in salt['pillar.get']('redash:datasources').items() %}

redash datasource {{ datasource }}:
{%- if not properties.get('absent', False) %}
  redash.datasource_present:
    - name: {{ datasource }}
    - type: {{ properties['type'] }}
    - options: {{ properties['options'] }}
{%- else %}
  redash.datasource_absent:
    - name: {{ datasource }}
{%- endif %}

{%- endfor %}

{%- for query, properties in salt['pillar.get']('redash:queries').items() %}

{%- if properties.get('namespaced', False) %}
{%- set name = properties['datasource'] + ' - ' + query %}
{%- else %}
{%- set name = query %}
{%- endif %}

redash query {{ name }}:
  redash.query_present:
    - name: {{ name }}
    - datasource: {{ properties['datasource'] }}
    - description: {{ properties['description'] }}
    - query: |
        {{ properties['query'] | indent(8) }}
    - publish: {{ properties.get('publish', True) }}
    {%- if properties.get('schedule', None) %}
    - schedule: {{ properties['schedule'] }}
    {%- endif %}
    - require:
      - redash: {{ properties['datasource'] }}

{%- endfor %}
