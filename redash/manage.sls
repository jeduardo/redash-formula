{% for datasource, properties in salt['pillar.get']('redash:datasources').items() %}

create datasource {{ datasource }}:
  redash.datasource_present:
    - name: {{ datasource }}
    - type: {{ properties['type'] }}
    - options: {{ properties['options'] }}

{% endfor %}

{% for query, properties in salt['pillar.get']('redash:queries').items() %}
{% if properties.get('namespaced', False) %}
{% set name = properties['datasource'] + ' - ' + query %}
{% else %}
{% set name = query %}
{% endif %}

create query {{ name }}:
  redash.query_present:
    - name: {{ name }}
    - datasource: {{ properties['datasource'] }}
    - description: {{ properties['description'] }}
    - query: |
        {{ properties['query'] | indent(8) }}
    - publish: {{ properties.get('publish', True) }}
    {% if properties.get('schedule', None) %}
    - schedule: {{ properties['schedule'] }}
    {% endif %}
    - require:
      - redash: {{ properties['datasource'] }}

{% endfor %}
