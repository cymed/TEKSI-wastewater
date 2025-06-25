.. datamodel:

Datamodel
=======

The datamodel complete description can be found `here <https://teksi.github.io/wastewater/_static/datamodel/>`_

Generation of obj_id
^^^^^^^^^^^^^^^^^^^^

All TEKSI Object IDs except label positions are generated on the database. They consist of three sub_parts:

.. list-table::
   :widths: 20 50
   :header-rows: 0

   * - OID prefix (8 digits)
     - see :ref:`add_oid_prefix` for more information
   * - class shortcut (2 digits)
     - TEKSI-specific shortcut differentiate INTERLIS classes
   * - OID Postfix (6 digits)
     - when < 1 million entries, base10 encoded Postfix. After that, the postfix is  base36 encoded starting at 99999a

On Import, the corresponding sequences are automatically updated