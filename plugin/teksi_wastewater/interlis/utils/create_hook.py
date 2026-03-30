#!/usr/bin/env python3
import logging
import os
import re
from argparse import ArgumentParser, BooleanOptionalAction
from pathlib import Path

import psycopg
import yaml
from pirogue import MultipleInheritance, SimpleJoins, SingleInheritance
from pum import HookBase
# from triggers.set_defaults_and_triggers import set_defaults_and_triggers
# from view.catchment_area_views import (
#     vw_tww_catchment_area,
#     vw_tww_catchment_area_totals,
# )
# from view.maintenance_views import (
#     mvw_tww_channel,
#     vw_tww_channel_maintenance,
#     vw_tww_ws_maintenance,
# )
# from view.vw_tww_additional_ws import vw_tww_additional_ws
# from view.vw_tww_damage_channel import vw_tww_damage_channel
# from view.vw_tww_infiltration_installation import vw_tww_infiltration_installation
# from view.vw_tww_log_card import vw_tww_log_card
# from view.vw_tww_measurement_series import vw_tww_measurement_series
# from view.vw_tww_overflow import vw_tww_overflow
# from view.vw_tww_reach import vw_tww_reach
# from view.vw_tww_wastewater_structure import vw_tww_wastewater_structure
# from view.vw_wastewater_structure import vw_wastewater_structure

logger = logging.getLogger(__name__)


class Hook(HookBase): #maybe remove HookBase
    def run_hook(
        self,
        # connection: psycopg.Connection,
        SRID: int = 2056,
        modification_agxx: bool = False,
        webgis: bool = False,
        modification_ci: bool = False,
        lang_code: str = "en",
        hook_yaml: Path = None,
        # added: bools pre and post to define which ones we have
        hook_type: str = None, # defines if it is a pre or post hook
    ):
        """
        Creates the schema tww_app for TEKSI Wastewater & GEP
        :param SRID: the EPSG code for geometry columns. Overridden by modification_yaml
        :param modification_agxx: bool of whether to load agxx modification. Overridden by modification_yaml
        :param webgis: bool of whether to load web modification. Overridden by modification_yaml
        :param modification_ci: bool of whether to load ci modification. Overridden by modification_yaml
        :param lang_code: language code for use in modification views. Overridden by modification_yaml
        :param modification_yaml: Path of yaml containing app parametrisation
        """
        self.cwd = Path(__file__).parent.resolve()
        # UNCOMMENT LATER
        # self._connection = connection

        self.parameters = self.load_yaml(hook_yaml)
        self.abspath = self.cwd if not hook_yaml else ""

 

        self.variables_sql = {}
        self.variables_py = {}

        # Wo macht es Sinn, zwischen pre und post zu unterscheiden?

        # if pre:
        # for param in self.parameters.pre_hook.parameters: # Hier genaue Struktur zum Callen rausfinden
        #     if param["type_sql"] :

                    # die variablen übernehmen, die im hook.yaml übernommen werden

                # gleiches für type_py und post

# ADDED 23/03: Loop über die Parameter in hook.yaml, um die Variablen für die sql- resp py-files zu befüllen.
        
        for name, param in self.parameters['parameters'].items():

            # Idea to handle path, maybe better further down
            # if param.get("type") == "path" and param.get("default") != None:
            #     py_type = Path(param.get("default"))
            
            self.variables_py[name] = {
                "value": param.get("default"),
                "type": param.get("type"),
            }

            if param.get("py_only") == False: # FRAGE: Brauchts noch mehr sql-parameter?
                if param.get("type") in ("int", "float"):
                    sql_type = "number"
                elif param.get("type") == "bool":
                    sql_type = "boolean"
                elif param.get("type") == "identifier":  # Table/Column names
                    sql_type = "identifier"
                elif param.get("type") == "str":  # String/Number literals
                    sql_type = "literal"
                else:
                    sql_type = "text"
                # Add parameter entry
                self.variables_sql[name] = {
                    "value": param.get("default"),
                    "type": sql_type,
                }

        if hook_type == "pre":
            self.files = self.parameters["prefiles"]

        elif hook_type == "post":
            self.files = self.parameters["postfiles"]

        else:
            raise ValueError(f"Hook type '{hook_type}' is not supported.")
            

            

# pyhton kwargs

        # self.execute("CREATE SCHEMA tww_app;")
        # self.execute("CREATE SCHEMA tww_app_pg2xtf;")
        # self.execute("CREATE SCHEMA tww_app_xtf2pg;")
        # self.run_sql_files_in_folder(self.cwd / "sql_functions")

# Modifications werden nicht hier geladen, sondern weiter unten (IDEE Stand 30.3.)
        # self.app_modifications = [
        #     entry
        #     for entry in self.parameters.get("modification_repositories")
        #     if entry.get("active")
        # ]
        # self.simple_joins_yaml = self.parameters.get("simple_joins_yaml")
        # self.multiple_inherintances = self.parameters.get("multiple_inherintances")

        # self.single_inherintances = self.load_yaml(self.cwd / "single_inherintances.yaml")

# # UNCOMMENT LATER
#         if self.app_modifications:
#             for modification in self.app_modifications:
#                 logger.debug(
#                     f"""*****
# Running modification {modification.get('id')}
# ****
#                 """
#                 )
#                 self.load_modification(
#                     modification_config=modification,
#                 )

#         for entry in self.parameters.get("modification_repositories"):
#             if entry.get("reset_vl", False):
#                 self.manage_vl(entry)
# END UNCOMMENT LATER

        # Defaults and Triggers
        # Has to be fired before view creation otherwise it won't work and will only fail in CI
        # UNCOMMENT LATER MAYBE
        # set_defaults_and_triggers(self._connection, self.single_inherintances)

# region collapsable block1
        # for key in self.single_inherintances:
        #     logger.debug(f"creating view vw_{key}")
        #     SingleInheritance(
        #         connection=self._connection,
        #         parent_table="tww_od." + self.single_inherintances[key],
        #         child_table="tww_od." + key,
        #         view_name="vw_" + key,
        #         view_schema="tww_app",
        #         pkey_default_value=True,
        #         inner_defaults={"identifier": "obj_id"},
        #     ).create(commit=False)

        # for key in self.multiple_inherintances:
        #     MultipleInheritance(
        #         connection=self._connection,
        #         definition=self.load_yaml(self.abspath / self.multiple_inherintances[key]),
        #         drop=True,
        #         variables=variables_pirogue,
        #     ).create(commit=False)

        # for key, value in self.extra_definitions.items():
        #     if value:
        #         self.extra_definitions[key] = self.abspath / value

        # vw_wastewater_structure(
        #     connection=self._connection,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["vw_wastewater_structure"])
        #         if self.extra_definitions.get("vw_wastewater_structure")
        #         else {}
        #     ),
        # )
        # vw_tww_wastewater_structure(
        #     connection=self._connection,
        #     srid=SRID,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["vw_tww_wastewater_structure"])
        #         if self.extra_definitions.get("vw_tww_wastewater_structure")
        #         else {}
        #     ),
        # )
        # vw_tww_infiltration_installation(
        #     connection=self._connection,
        #     srid=SRID,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["vw_tww_infiltration_installation"])
        #         if self.extra_definitions.get("vw_tww_infiltration_installation")
        #         else {}
        #     ),
        # )
        # vw_tww_reach(
        #     connection=self._connection,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["vw_tww_reach"])
        #         if self.extra_definitions.get("vw_tww_reach")
        #         else {}
        #     ),
        # )
        # mvw_tww_channel(
        #     connection=self._connection,
        #     srid=SRID,
        #     lang_code=lang_code,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["mvw_tww_channel"])
        #         if self.extra_definitions.get("mvw_tww_channel")
        #         else {}
        #     ),
        # )
        # vw_tww_channel_maintenance(
        #     connection=self._connection,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["vw_tww_channel_maintenance"])
        #         if self.extra_definitions.get("vw_tww_channel_maintenance")
        #         else {}
        #     ),
        # )
        # vw_tww_ws_maintenance(
        #     connection=self._connection,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["vw_tww_ws_maintenance"])
        #         if self.extra_definitions.get("vw_tww_ws_maintenance")
        #         else {}
        #     ),
        # )
        # vw_tww_damage_channel(
        #     connection=self._connection,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["vw_tww_damage_channel"])
        #         if self.extra_definitions.get("vw_tww_damage_channel")
        #         else {}
        #     ),
        # )
        # vw_tww_additional_ws(
        #     srid=SRID,
        #     connection=self._connection,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["vw_tww_additional_ws"])
        #         if self.extra_definitions.get("vw_tww_additional_ws")
        #         else {}
        #     ),
        # )
        # vw_tww_measurement_series(
        #     connection=self._connection,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["vw_tww_measurement_series"])
        #         if self.extra_definitions.get("vw_tww_measurement_series")
        #         else {}
        #     ),
        # )
        # vw_tww_overflow(
        #     connection=self._connection,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["vw_tww_overflow"])
        #         if self.extra_definitions.get("vw_tww_overflow")
        #         else {}
        #     ),
        # )
        # vw_tww_log_card(
        #     srid=SRID,
        #     connection=self._connection,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["vw_tww_log_card"])
        #         if self.extra_definitions.get("vw_tww_log_card")
        #         else None
        #     ),
        # )
        # vw_tww_catchment_area(
        #     connection=self._connection,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["vw_tww_catchment_area"])
        #         if self.extra_definitions.get("vw_tww_catchment_area")
        #         else None
        #     ),
        # )
        # vw_tww_catchment_area_totals(
        #     connection=self._connection,
        #     extra_definition=(
        #         self.load_yaml(self.extra_definitions["vw_tww_catchment_area_totals"])
        #         if self.extra_definitions.get("vw_tww_catchment_area_totals")
        #         else None
        #     ),
        # )

# endregion

        # for _, yaml_path in self.simple_joins_yaml.items():
        #     SimpleJoins(
        #         definition=self.load_yaml(self.abspath / yaml_path), connection=self._connection
        #     ).create(commit=False)

        # sql_directories = [
        #     "view/varia",
        #     "view/catchment_area",
        #     "view/gep_views",
        #     "view/swmm_views",
        #     "view/network",
        # ]

        # for directory in sql_directories:
        #     abs_dir = self.cwd / directory
        #     self.run_sql_files_in_folder(abs_dir)

        # # run post_all
        # self.run_sql_files_in_folder(self.cwd / "post_all")

    @staticmethod
    def load_yaml(file: Path) -> dict[str]:
        """Safely loads a YAML file and ensures it returns a dictionary."""
        file = Path(file)
        if not file.exists():
            raise FileNotFoundError(f"The file {file} does not exist.")

        logger.debug(f"loading yaml {file}")
        with open(file) as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}

    def load_modification(
        self,
        modification_config: dict = None,
        executable_files: list = None,
    ):
        """
        initializes the TWW app schema for usage of a modification
        Args:
            modification_config: modification configuration set
        """

        # # load definitions from config
        # template_path = modification_config.get("template", None)
        # if template_path:
        #     curr_dir = self.abspath / os.path.dirname(template_path)
        #     modification_config = self.load_yaml(self.abspath / template_path)
        # else:
        

        
        sql_vars = self.parse_sql_variables({**self.variables_sql})
        py_vars = self.parse_py_variables({**self.variables_py})

        # Ist hier Idee, dass wir das alles in py statt sql umschreiben oder immer noch sql?
        # nein, die Idee ist, dass sowohl sql als auch py geht. deshalb über alle files iterieren. 
        # for file in bla
        for file in self.files:
            logger.debug(f"Running file {file}")
            # file_name = curr_dir / file.get("file")
            # Idee: If endswith sql, then self.run_sql_file. If endswith py, then self.run_py_file
            if file.endswith(".sql"):
                self.run_sql_file(file, sql_vars)
            elif file.endswith(".py"):
                self.run_py_file(file, py_vars)

        # if template_path:
        #     for key, value in modification_config.get("extra_definitions", {}).items():
        #         if not self.extra_definitions[key]:
        #             self.extra_definitions[key] = curr_dir / value
        #             logger.debug(
        #                 f"altered {key} extra definition to {self.extra_definitions[key]}"
        #             )

            # for key, value in modification_config.get("simple_joins_yaml", {}).items():
            #     if not self.simple_joins_yaml[key]:
            #         self.simple_joins_yaml[key] = curr_dir / value
            #         logger.debug(
            #             f"altered {key} simpleJoin definition to {self.simple_joins_yaml[key]}"
            #         )

            # for key, value in modification_config.get("multiple_inherintances", {}).items():
            #     if self.multiple_inherintances[key]:
            #         self.multiple_inherintances[key] = curr_dir / value
            #         logger.debug(
            #             f"altered {key} multipleInheritance definition to {self.multiple_inherintances[key]}"
            #         )
# # Noch überlegen, wo es separate py und sql funktionen braucht
#     def manage_vl(
#         self,
#         config: dict = None,
#     ):
#         """
#         manages activation/deactivation of tww value list of a modification
#         Args:
#             config:  configuration set
#         """

#         # load definitions from config
#         template_path = config.get("template", None)
#         is_active = config.get("active", False)
#         sql_vars = {"activate": {"value": is_active, "type": "literal"}}
#         sql_vars = self.parse_variables(sql_vars)
#         if template_path:
#             curr_dir = os.path.dirname(template_path)
#             config = self.load_yaml(template_path)
#         else:
#             curr_dir = ""

#         for sql_file in config.get("reset_vl_files", None):
#             file_name = curr_dir / sql_file.get("file")
#             self.run_sql_file(file_name, sql_vars)

    def run_py_file(self, file_path: str, variables: dict = None):
        pass

    def run_sql_file(self, file_path: str, variables: dict = None):
        with open(file_path) as f:
            sql = f.read()
        self.run_sql(sql, variables)

    def run_sql(self, sql: str, variables: dict = None):
        if variables is None:
            variables = {}
        if (
            re.search(r"\{[A-Za-z-_]+\}", sql) and variables
        ):  # avoid formatting if no variables are present
            try:
                sql = psycopg.sql.SQL(sql).format(**variables).as_string(self._connection)

            except IndexError:
                logger.critical(sql)
                raise
        self.execute(sql)

    # def run_sql_files_in_folder(self, directory: str):
    #     files = os.listdir(directory)
    #     files.sort()
    #     sql_vars = self.parse_variables(self.variables_sql)
    #     for file in files:
    #         filename = os.fsdecode(file)
    #         if filename.lower().endswith(".sql"):
    #             logger.debug(f"Running {filename}")
    #             self.run_sql_file(os.path.join(directory, filename), sql_vars)

    def parse_sql_variables(self, variables: dict) -> dict:
        """Parse sql variables based on their defined types in the YAML."""
        formatted_vars = {}

        for key, meta in variables.items():
            if isinstance(meta, dict) and "value" in meta and "type" in meta:
                value, var_type = meta["value"], meta["type"].lower()

                if var_type == "number":  # Directly insert SQL without escaping
                    if isinstance(value, float) or isinstance(value, int):
                        formatted_vars[key] = psycopg.sql.SQL(f"{value}")
                    else:  # avoid injection
                        raise ValueError(f"Value '{value}' is not float or int.")
                elif var_type == "identifier":  # Table/Column names
                    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", value):  # avoid injection
                        raise ValueError(f"Identifier '{value}' contains invalid characters.")
                    formatted_vars[key] = psycopg.sql.Identifier(value)
                elif var_type == "literal":  # String/Number literals
                    formatted_vars[key] = psycopg.sql.Literal(value)
                else:
                    raise ValueError(f"Unknown type '{var_type}' for variable '{key}'")
            else:
                raise ValueError(f"Unknown type '{var_type}' for variable '{key}'.")
        return formatted_vars
    

    def parse_py_variables(self, variables: dict) -> dict:
        """Parse py variables based on their defined types in the YAML."""
        formatted_vars = {}
# Todo: fix parse_py_variables
        for key, meta in variables.items():
            if isinstance(meta, dict) and "default" in meta and "type" in meta:
                value, var_type = meta["default"], meta["type"].lower()

                if var_type == "int":  
                    formatted_vars[key] = int(value)
                if var_type == "float":  
                    formatted_vars[key] = float(value)
                if var_type == "str":
                    formatted_vars[key] = str(value)
                if var_type == "bool": 
                    formatted_vars[key] = bool(value)
                else:
                    raise ValueError(f"Unknown type '{var_type}' for variable '{key}'")
            else:
                raise ValueError(f"Unknown type '{var_type}' for variable '{key}'.")
        return formatted_vars

         
#     # Changed: adapted for py- instead of sql-files

#     def manage_vl(
#         self,
#         config: set = None,
#     ):
#         """
#         Manages activation/deactivation of tww value list of a modification
#         Args:
#             config: configuration set
#         """

#         # load definitions from config
#         template_path = config.get("template", None)
#         is_active = config.get("active", False)

#         py_vars = {"activate": {"value": is_active, "type": "literal"}}
#         py_vars = self.parse_variables(py_vars)

#         if template_path:
#             curr_dir = os.path.dirname(template_path)
#             config = self.load_yaml(template_path)
#         else:
#             curr_dir = ""

#         for py_file in config.get("reset_vl_files", None):
#             file_name = curr_dir / py_file.get("file")
#             self.run_py_file(file_name, py_vars)


#     def run_py_file(self, file_path: str, variables: dict = None):
#         with open(file_path) as f:
#             code = f.read()
#         self.run_py(code, variables)


#     def run_py(self, code: str, variables: dict = None):
#         """
#         Executes Python code with optional variable injection.
#         """
#         if variables is None:
#             variables = {}

#         # Inject variables into execution context
#         exec_context = {k: v["value"] for k, v in variables.items()}

#         try:
#             exec(code, exec_context)
#         except Exception as e:
#             logger.critical(f"Error executing Python code from file: {e}")
#             raise


#     def run_py_files_in_folder(self, directory: str):
#         files = os.listdir(directory)
#         files.sort()
#         py_vars = self.parse_variables(self.variables_py)

#         for file in files:
#             filename = os.fsdecode(file)
#             if filename.lower().endswith(".py"):
#                 logger.debug(f"Running {filename}")
#                 self.run_py_file(os.path.join(directory, filename), py_vars)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-p", "--pg_service", help="postgres service")
    parser.add_argument(
        "-s", "--srid", help="SRID EPSG code, defaults to 2056", type=int, default=2056
    )
    parser.add_argument(
        "-d",
        "--drop-schema",
        help="Drops cascaded any existing tww_app schema",
        default=False,
        action=BooleanOptionalAction,
    )
    parser.add_argument(
        "-a",
        "--modification_agxx",
        action="store_true",
        default=False,
        help="load AG-64/96 modification on app schema",
    )
    parser.add_argument(
        "-c",
        "--modification_ci",
        action="store_true",
        default=False,
        help="load ci modification",
    )
    parser.add_argument(
        "-w",
        "--webgis",
        action="store_true",
        default=False,
        help="load webGIS modification",
    )
    parser.add_argument(
        "-l",
        "--lang_code",
        help="language code",
        type=str,
        default="en",
        choices=["en", "fr", "de", "it", "ro"],
    )
    parser.add_argument("-m", "--modification_yaml", help="path to modification yaml", type=Path)
    args = parser.parse_args()

    with psycopg.connect(service=args.pg_service) as connection:
        if args.drop_schema:
            connection.execute("DROP SCHEMA IF EXISTS tww_app CASCADE;")
        hook = Hook()
        hook.run_hook(
            connection=connection,
            SRID=args.srid,
            modification_agxx=args.modification_agxx,
            modification_ci=args.modification_ci,
            webgis=args.webgis,
            modification_yaml=args.modification_yaml,
            lang_code=args.lang_code,
        )
