JSONB Mapping
=============

Complex mappings are represented by row-level SQL projection functions.

A projection function converts a source row into a canonical JSONB effect
document. The document can be compared for diff generation or passed to a
generic persistence function.

Effect kinds
------------

``update_attribute``
   Updates one canonical attribute.

``ensure_row_exists``
   Ensures a row exists without overwriting existing attribute values.

``delete_row``
   Deletes a row identified by its identity fields.

Example
-------

.. code-block:: json

   {
     "version": 1,
     "source": {
       "model": "agxx",
       "class": "GepKnoten",
       "object_id": "ch123456AG987654"
     },
     "effects": [
       {
         "kind": "update_attribute",
         "tww_class_id": "agxx_wastewater_node",
         "tww_identity": {
           "fk_wastewater_node": "ch123456AG987654"
         },
         "tww_attribute_id": "ag64_function",
         "value_id": 1234
       }
     ]
   }