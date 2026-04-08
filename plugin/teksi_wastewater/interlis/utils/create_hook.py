#!/usr/bin/env python3
import logging
import os
import re
from argparse import ArgumentParser, BooleanOptionalAction
from pathlib import Path
import importlib.util


import psycopg
import yaml
from pirogue import MultipleInheritance, SimpleJoins, SingleInheritance
from pum.sql_content import SqlContent
from typing import Any



logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Hook class
# ------------------------------------------------------------



class Hook():
    def run_hook(
        self,
        connection: psycopg.Connection,
        SRID: int = 2056,
        hook_yaml: Path = None,
        hook_type: str = None, # defines if it is a pre or post hook
    ):
        """
        Creates a hook that allows to run python and sql files before or after importing or exporting files.
        :param SRID: the EPSG code for geometry columns. Overridden by hook_yaml
        :param hook_yaml: Path of yaml containing the parameters and paths to executable files of the hook
        :param hook_type: Determines whether the pre - or posthook files are executed. Allowed values: "pre", "post"
        """
        self.cwd = Path(__file__).parent.resolve()
        self._connection = connection

        self.parameters = self.load_yaml(hook_yaml)
        self.abspath = self.cwd if not hook_yaml else ""

 

        self.variables_sql = {}
        self.variables_py = {}

        
        # ----------------------------------------------------
        # Collect variables from YAML
        # ----------------------------------------------------

        for name, param in self.parameters['parameters'].items():

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
                
        # ----------------------------------------------------
        # Determine which files should be executed
        # ----------------------------------------------------

        if hook_type == "pre":
            self.files = self.parameters["prefiles"]

        elif hook_type == "post":
            self.files = self.parameters["postfiles"]

        else:
            raise ValueError(f"Hook type '{hook_type}' is not supported.")
        
        self.execute_files()
            

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

    def execute_files(
        self,
    ):
        """Parses the variables and runs all files that are given in self.files."""
        sql_vars = self.parse_sql_variables({**self.variables_sql})
        py_vars = self.parse_py_variables({**self.variables_py})

        for file in self.files:
            logger.debug(f"Running file {file}")
            if file.endswith(".sql"):
                self.run_sql_file(file, sql_vars)
            elif file.endswith(".py"):
                self.run_py_file(file, py_vars)

            else:
                raise ValueError(f"File type '{file}' is invalid. The type should be .py or .sql.")

    def run_py_file(self, py_file: str, py_vars: dict = None):
        """
        Execute a Python hook file that defines run(context).

        Args:
            py_file: Path to the .py hook file
            py_vars: Parsed Python variables (name -> value)
        """

        py_file = Path(py_file)

        if not py_file.exists():
            raise FileNotFoundError(f"Python hook not found: {py_file}")

        if py_file.suffix != ".py":
            raise ValueError(f"Not a Python file: {py_file}")

        # --------------------------------------------------
        # Build execution context
        # --------------------------------------------------
        context = {
            **py_vars,
            "hook": self,          # optional: access to self.execute(), logging, etc.
        }

        # --------------------------------------------------
        # Load module from file path
        # --------------------------------------------------
        spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load Python hook: {py_file}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # --------------------------------------------------
        # Enforce explicit entry point
        # --------------------------------------------------
        if not hasattr(module, "run"):
            raise AttributeError(
                f"Python hook '{py_file}' must define a run(context) function"
            )

        run_fn = module.run

        if not callable(run_fn):
            raise TypeError(
                f"'run' in {py_file} exists but is not callable"
            )

        # --------------------------------------------------
        # Execute hook logic
        # --------------------------------------------------
        run_fn(context)


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
        #self.execute(sql)
        SqlContent(sql).execute(
            connection=self._connection, parameters=variables, commit=False
        )

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
                var_type = meta["type"].lower()
                raise ValueError(f"Unknown type '{var_type}' for variable '{key}'.") 
            
        return formatted_vars
    

    def parse_py_variables(self, variables: dict) -> dict:
        """
        Parses and validates Python variables defined in YAML.
        Returns a dict[name -> parsed Python value].
        """

        parsed: dict[str, object] = {}

        TYPE_MAPPING = {
            "int": int,
            "float": float,
            "bool": bool,
            "str": str,
            "path": Path,
        }

        for name, meta in variables.items():
            raw_value = meta.get("value")
            type_name = meta.get("type")

            if type_name not in TYPE_MAPPING:
                raise ValueError(
                    f"Unsupported python type '{type_name}' for variable '{name}'"
                )

            expected_type = TYPE_MAPPING[type_name]

            try:
                if expected_type is Path:
                    parsed[name] = None if raw_value is None else Path(raw_value)
                else:
                    parsed[name] = expected_type(raw_value)

            except Exception as e:
                raise ValueError(
                    f"Failed to parse python variable '{name}' "
                    f"with value '{raw_value}' as type '{type_name}'"
                ) from e

        return parsed



# if __name__ == "__main__":
#     parser = ArgumentParser()
#     parser.add_argument("-p", "--pg_service", help="postgres service")
#     parser.add_argument(
#         "-s", "--srid", help="SRID EPSG code, defaults to 2056", type=int, default=2056
#     )
#     parser.add_argument(
#         "-d",
#         "--drop-schema",
#         help="Drops cascaded any existing tww_app schema",
#         default=False,
#         action=BooleanOptionalAction,
#     )
#     parser.add_argument(
#         "-a",
#         "--modification_agxx",
#         action="store_true",
#         default=False,
#         help="load AG-64/96 modification on app schema",
#     )
#     parser.add_argument(
#         "-c",
#         "--modification_ci",
#         action="store_true",
#         default=False,
#         help="load ci modification",
#     )
#     parser.add_argument(
#         "-w",
#         "--webgis",
#         action="store_true",
#         default=False,
#         help="load webGIS modification",
#     )
#     parser.add_argument(
#         "-l",
#         "--lang_code",
#         help="language code",
#         type=str,
#         default="en",
#         choices=["en", "fr", "de", "it", "ro"],
#     )
#     parser.add_argument("-m", "--modification_yaml", help="path to modification yaml", type=Path)
#     args = parser.parse_args()

#     with psycopg.connect(service=args.pg_service) as connection:
#         if args.drop_schema:
#             connection.execute("DROP SCHEMA IF EXISTS tww_app CASCADE;")
#         hook = Hook()
#         hook.run_hook(
#             connection=connection,
#             SRID=args.srid,
#             modification_agxx=args.modification_agxx,
#             modification_ci=args.modification_ci,
#             webgis=args.webgis,
#             modification_yaml=args.modification_yaml,
#             lang_code=args.lang_code,
#         )
