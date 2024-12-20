![TEKSI wastewater Module](https://github.com/teksi/Home/blob/master/Ressources/Logos/modules/EN/210910-teksi-waste-logos-en-01_45pp.png?raw=true)

## Welcome to the TEKSI wastewater Module GitHub Home page 👋
TEKSI wastewater module (project name: QGEP) is a selection of tools and a database implementation that allows you to:

* manage and map your sewer network data with all its components in compliance with Swiss standards
* indicate the characteristics of networks objects in the form of attributes such as diameter, material, depth, damages, construction year, etc.
* produce plans and extract statistics from the database such as network values, total length of pipes, identification of future interventions, etc.
* export geodata in compliance with Swiss standards [VSA-DSS Release 2020.1](https://www.vsa.ch/models/?dir=2020_1)


TEKSI wastewater module is a complete open source module based on a PostgreSQL - PostGIS data model compatible with the swiss norm SIA405 AND VSA-DSS. The data are accessed and edited with a dedicated QGIS project.
The project is maintained by the [TEKSI community](https://www.teksi.ch)

[TEKSI](https://www.teksi.ch) is a non profit Swiss association set up to support open source professional GIS projects aiming to ease the management of public infrastructures. [TEKSI GitHub Home page](https://github.com/TEKSI)

## How to start
* [TEKSI wastewater features](https://qgep.github.io/docs/en/features-guide/index.html)
* Quick demo : TO DO
* [Installation Guide](https://qgep.github.io/docs/en/installation-guide/index.html)
* [How to contribute](https://qgep.github.io/docs/en/contributor-guide/index.html)

## Issues, features, ideas
* [Issues and features](https://github.com/qgep/qgep/issues)
* [Disscussions and ideas](https://github.com/qgep/qgep/discussions)

## Source code for contributions / GitHub Repository organisation
* [Datamodel](https://github.com/qgep/datamodel)
* [QGIS Project](https://github.com/qgep/qgep)
* [Documentation](https://github.com/qgep/docs)
* [QGIS Plugin](https://github.com/qgep/qgepplugin)

## TEKSI ressources on GitHub and other projects
* [TEKSI GitHub Home page](https://github.com/TEKSI)
* [TEKSI Module for drinking water network management (QWAT Project)](https://github.com/QWAT)


## Website
You can discover more about [TEKSI](https://www.teksi.ch)


TEKSI Wastewater Release 2024.0 is now available!

Migration path from QGEP to TEKSI Wastewater is also established. <!---  // skip-keyword-check -->

## Information for Developers

### Local development

1. Open OSGeo4W Shell and run `pip install debugpy`.
2. Clone this repository to your local machine.
3. Open QGIS, go to the _Environment_ section in `Settings > Options - System` and add the following custom variables:

   | Apply  | Variable                 | Value                   |
   | :----- | :----------------------- | :---------------------- |
   | APPEND | QGIS_PLUGINPATH          | {repositoryPath}/plugin |
   | APPEND | QGIS_PLUGIN_USE_DEBUGGER | debugpy                 |

4. Install QGIS plugin _Plugin Reloader_. This will allow you to reload the plugin without restarting QGIS.
5. Follow the _prerequisites_ and _Usage (GUI)_ from https://github.com/wapaAdmin/tww2ag6496/blob/main/docs/en/admin-guide/interlis-io/index.rst

### Local development with VS Code

1. Ensure prerequisites are met according to the [admin guide](docs/en/admin-guide/interlis-io/index.rst).
2. Install [Visual Studio Code](https://code.visualstudio.com/) and the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python).
3. Install QGIS LTR
4. Install Docker
5. Install debugpy by running task `Install dependencies` or run `pip install debugpy` in the OSGeo4W Shell on Windows or your python env for qgis.
6. Launch QGIS with task `Launch QGIS`.
7. Wait for QGIS to start and open the plugin in QGIS.
7. Ensure __Developer mode__ is enabled in the plugin settings. This will start the debug server.
8. Attach the debugger with Debug: Start Debugging (F5) with configuration `Python: Remote Attach`
