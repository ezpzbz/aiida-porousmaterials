""" PorousMaterials Calculation Plugin """
import os
import six

from aiida.common import CalcInfo, CodeInfo
from aiida.engine import CalcJob
from aiida.orm import Dict, FolderData, SinglefileData
from aiida.plugins import DataFactory
from aiida_porousmaterials.utils import PorousMaterialsInput

CifData = DataFactory('cif')  # pylint: disable=invalid-name


# Coding the class
class PorousMaterialsCalculation(CalcJob):
    """This is PorousMaterialsCalculation as the subclass
    of AiiDA CalcJob to prepare input for the PorousMaterials
    suite of Julia codes.
    Please refer to : https://github.com/SimonEnsemble/PorousMaterials.jl
    """
    # Defaults
    INPUT_FILE = 'input.jl'
    OUTPUT_FOLDER = 'Output'
    PROJECT_NAME = 'aiida'
    DEFAULT_PARSER = 'porousmaterials'

    @classmethod
    def define(cls, spec):
        """
        The important section to define the class, inputs and outputs.
        """
        super(PorousMaterialsCalculation, cls).define(spec)

        spec.input_namespace(
            'structure', valid_type=CifData, required=True, dynamic=True, help='Framework input file as CIF'
        )

        spec.input_namespace(
            'acc_voronoi_nodes',
            valid_type=SinglefileData,
            required=True,
            dynamic=True,
            help='Accessible Voronoi nodes calculated by Zeo++'
        )

        spec.input('parameters', valid_type=Dict, required=True, help='parameters such as cutoff and mixing rules.')
        spec.input('settings', valid_type=Dict, required=False, help='Additional input parameters')
        spec.input('metadata.options.parser_name', valid_type=six.string_types, default=cls.DEFAULT_PARSER, non_db=True)

        # Output parameters
        spec.outputs.dynamic = True
        spec.output(
            'output_parameters', valid_type=Dict, required=True, help='dictionary of calculated Voronoi energies'
        )
        spec.output_namespace('ev_output_file', valid_type=SinglefileData, required=False, dynamic=True)
        # Exit codes
        spec.exit_code(
            100, 'ERROR_NO_RETRIEVED_FOLDER', message='The retrieved folder data node could not be accessed.'
        )
        spec.exit_code(101, 'ERROR_NO_OUTPUT_FILE', message='The retrieved folder does not contain an output file.')

        # Default output node
        spec.default_output_node = 'output_parameters'

    def prepare_for_submission(self, folder):
        """
        This is the routine to be called when you want to create
        the input files and related stuff with a plugin.

        :param folder: a aiida.common.folders.Folder subclass where
                           the plugin should put all its files.
        """
        parameters = self.inputs.parameters.get_dict()

        # get settings
        if 'setting' in self.inputs:
            settings = self.inputs.settings.get_dict()
        else:
            settings = {}

        # Writing the input
        inp = PorousMaterialsInput(parameters)

        with open(folder.get_abs_path(self.INPUT_FILE), "w") as fobj:
            fobj.write(inp.render())

        # create code information
        codeinfo = CodeInfo()
        codeinfo.cmdline_params = settings.pop('cmdline', []) + [self.INPUT_FILE]
        codeinfo.code_uuid = self.inputs.code.uuid

        # Create calc information
        calcinfo = CalcInfo()
        calcinfo.stdin_name = self.INPUT_FILE
        calcinfo.uuid = self.uuid
        calcinfo.cmdline_params = codeinfo.cmdline_params
        calcinfo.codes_info = [codeinfo]

        # file list
        calcinfo.local_copy_list = []

        if 'structure' in self.inputs:
            for name, fobj in self.inputs.structure.items():
                calcinfo.local_copy_list.append((fobj.uuid, fobj.filename, name + '.cif'))

        if 'acc_voronoi_nodes' in self.inputs:
            for name, fobj in self.inputs.acc_voronoi_nodes.items():
                calcinfo.local_copy_list.append((fobj.uuid, fobj.filename, name + '.voro_accessible'))

        calcinfo.retrieve_list = [self.OUTPUT_FOLDER]

        return calcinfo


# EOF
