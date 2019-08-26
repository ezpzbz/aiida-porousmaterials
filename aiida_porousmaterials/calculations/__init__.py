# -*- coding: utf-8 -*-
""" PorousMaterials Calculation Plugin """
from __future__ import absolute_import
import os

# Importing system modules

# Importing AiiDA modules
from aiida.orm import Dict, FolderData, SinglefileData
from aiida.common import CalcInfo, CodeInfo
from aiida.engine import CalcJob
from aiida.plugins import DataFactory

CifData = DataFactory('cif')
from aiida_porousmaterials.utils import PorousMaterialsInput

# Coding the class
class PorousMaterialsCalculation(CalcJob):
    """This is PorousMaterialsCalculation as the subclass
    of AiiDA CalcJob to prepare input for the PorousMaterials
    suite of Julia codes.
    Please refer to : https://github.com/SimonEnsemble/PorousMaterials.jl
    """
    # Defaults
    # TODO: Double thinking about these defaults.
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

        # Input parameters
        # TODO: I should decide to choose one or make the
        # code flexible so both can be used on the users choice.
        # Let's do it with Cif for now.
        spec.input('structure', valid_type=CifData,required=True,help='Framework input file as CIF')
        # spec.input('framework', valid_type=StructureData,required=True,
                    # help='Framework input file as CSSR')
        spec.input('forcefiled', valid_type=SinglefileData, required=False,help='forcefiled parameters as csv file')
        spec.input('voronoi_nodes', valid_type=SinglefileData, required=False,help='Voronoi nodes calculated by Zeo++')
        spec.input('parameters', valid_type=Dict, required=False,help='parameters such as cutoff and mixing rules.')
        spec.input('input_folder', valid_type=FolderData, required=False,help='Folder which contains the needed structure and other required data for running calculations.')
        spec.input('settings', valid_type=Dict, required=False, help='Additional input parameters')


        # Output parameters
        spec.output('output_parameters', valid_type=Dict, required=True, help='dictionary of calculated Voronoi energies')

        # Exit codes
        # TODO: To-be-defined after make the code running.

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
        # What is the purpose of this here?
        # calcinfo.remote_symlink_list = []
        calcinfo.local_copy_list = []
        calcinfo.local_copy_list = [(self.inputs.structure.uuid,
                                     self.inputs.structure.filename,
                                     self.inputs.structure.filename)]

        if 'voronoi_nodes' in self.inputs:
            vn = self.inputs.voronoi_nodes
            vn_file_name = vn.filename
            calcinfo.local_copy_list.append(
                (vn.uuid, vn.filename,
                 vn.filename))
        else:
            vn_file_name = None

        calcinfo.retrieve_list = [self.OUTPUT_FOLDER]

        return calcinfo
