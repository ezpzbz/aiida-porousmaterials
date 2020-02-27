"""PorousMaterials Output Parse"""
import os
import re

from aiida.common import NotExistent, OutputParsingError
from aiida.engine import ExitCode
from aiida.orm import Dict, SinglefileData
from aiida.parsers.parser import Parser
from aiida_porousmaterials.utils import parse_base_output


class PorousMaterialsParser(Parser):
    """
    Parsing the PorousMaterials output.
    """

    def parse(self, **kwargs):
        """
        Receives in input a dictionary of retrieved nodes.
        Does all the logic here.
        """
        try:
            output_folder = self.retrieved
        except NotExistent:
            return self.exit_codes.ERROR_NO_RETRIEVED_FOLDER

        output_folder_name = self.node.process_class.OUTPUT_FOLDER

        if output_folder_name not in output_folder._repository.list_object_names():  # pylint: disable=protected-access
            return self.exit_codes.ERROR_NO_OUTPUT_FILE

        output_parameters = {}
        ev_output_file = {}

        output_files = output_folder._repository.list_object_names(self.node.process_class.OUTPUT_FOLDER)  # pylint: disable=protected-access

        for fname in output_files:
            output_abs_path = os.path.join(
                output_folder._repository._get_base_folder().abspath,  # pylint: disable=protected-access
                self.node.process_class.OUTPUT_FOLDER,
                fname
            )
            ev_output_file[fname[:-4]] = SinglefileData(file=output_abs_path)
            dict_key1 = fname[:-4].split("_")[-1]
            dict_key2 = fname[:-4].split("_")[-2]
            if dict_key1 not in output_parameters.keys():
                output_parameters[dict_key1] = {}
            output_parameters[dict_key1][dict_key2 + "_probe"] = parse_base_output(output_abs_path)

        self.out("ev_output_file", ev_output_file)
        self.out("output_parameters", Dict(dict=output_parameters))

        return ExitCode(0)


# EOF
