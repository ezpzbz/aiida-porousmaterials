# -*- coding: utf-8 -*-
"""PorousMaterials Output Parse"""
from __future__ import absolute_import
import os

from aiida.common import NotExistent, OutputParsingError
from aiida.engine import ExitCode
from aiida.orm import Dict
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
        fname = self.node.inputs.parameters['output_filename']
        output_abs_path = os.path.join(
            output_folder._repository._get_base_folder().abspath,  # pylint: disable=protected-access
            self.node.process_class.OUTPUT_FOLDER,
            fname)

        if 'ev_setting' in self.node.inputs.parameters.get_dict():
            ev_setting = self.node.inputs.parameters['ev_setting']
        else:
            ev_setting = [90, 80, 50]

        output_parameters = parse_base_output(output_abs_path, ev_setting)

        self.out("output_parameters", Dict(dict=output_parameters))

        return ExitCode(0)


# EOF
