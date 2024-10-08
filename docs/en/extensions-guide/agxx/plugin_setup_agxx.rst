.. _plugin_setup_agxx

Plugin and Project Setup
=======================

In order to use the AG-64/AG-96 extension, the database must be initialized accordingly. See `initialize database extensions <../initialize_extensions.html>_` for further explanations.


.. _interlis_setup_agxx
Enable AG-64/AG-96 Interlis Imports and Exports
^^^^^^^^^^^^^^^^^^^^^^

In the plugin, there is a hidden functionality that allows importing and exporting AG-64/AG-96 interlis files. In order to activate it, one needs to open the TWW settings

 .. figure:: images/opensettingsdialog.png

In the tab *Developer options*, there is a Checkbox to enable the AG-64/96 extension

 .. figure:: images/enableextension.png

 When this checkbox is ticked, the data models AG-64/AG-96 are available in the interlis export.

.. _last_modification_agxx
Handling of last modification
^^^^^^^^^^^^^^^^^^^^^^

AG-64 and AG-96 have separated values for last_modification. In the plugin settings, there is a hidden combobox that allows altering which last_modification(s) should be updated.

 .. figure:: images/chooselastmodification.png

In the database, there is a table from which that value is taken on startup, so the setting does not need to be changed every time a project is opened.


 .. _project_setup_agxx
Project setup
^^^^^^^^^^^^^^^^^^^^^^

The attribute forms of AG-64/AG-96 are stored in a specific layer style automatically when starting the template .qgs project. In order to access them, right-click on the layer, select "styles" and cascade to ""AG-64/96"

 .. figure:: images/selectstyle.png

From there, you can copy/paste the forms if necessary
