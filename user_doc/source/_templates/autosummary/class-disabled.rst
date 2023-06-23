{{ fullname | escape | underline}}

.. autoclass:: {{ fullname }}

   {% block methods %}
   .. automethod:: {{ fullname }}.__init__

   {% if methods %}
   .. rubric:: {{ _('Methods') }}

   .. autosummary::
   {% for item in methods %}
      ~{{ fullname }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes %}
   .. rubric:: {{ _('Attributes') }}

   .. autosummary::
   {% for item in attributes %}
      ~{{ fullname }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}