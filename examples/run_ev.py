# -*- coding: utf-8 -*-
""" Sample run script for PorousMaterials Plugin"""
from __future__ import print_function
import os
import sys
import click

from aiida.common import NotExistent
from aiida.orm import Code
from aiida.plugins import DataFactory

from aiida_porousmaterials import PorousMaterialsCalculation


# Reading the structure and convert it to structure data.
StructureData = DataFactory('structure')

# Creating the command prompt input options using click
@click_command('cli')
@click.argument('codelabel')
@click.option('--submit', is_flag=True, help='If true, actually submits the clac to the daemon.')

def main(codelabel, submit):
    """
    """
    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print("The code '{}' does not exist".format(codelabel))
        sys.exit(1)

    pwd = os.path.dirname(os.path.realpath(__file__))
    # TODO: Herein, we need to read, get_structure using ase and
    # then save as the StructureData.
    framework = StructureData(file=pwd + '/test_raspa_attach_file/IRMOF1.cif')

        parameters = {
            'data_path':,
            'ff':,
            'cutoff':,
            'mixing': 'Lorentz-Berthelot',
            'framework':
            'header': 'Ev(kJ/mol),Rv(A),x,y,z,Framework,Adsorbate,Accuracy',
            'adsorbates': ['Xe','Kr'],
            'accuracy': ['S50'],
        }

        # resources
        options = {
            "resources": {
                "num_machines": 1,
                "num_mpiprocs_per_machine": 1,
            },
            "max_wallclock_seconds": 1 * 30 * 60,  # 30 min
            "withmpi": False,
        }

        # collecting all the inputs
        inputs = {
            "framework": framework,
            "parameters": parameters,
            "code": code,
            "metadata": {
                "options": options,
                "dry_run": False,
                "store_provenance": True,
            }
        }

        if submit:
            run(PorousMaterialsCalculation, **inputs)
            #print(("submitted calculation; calc=Calculation(uuid='{}') # ID={}"\
            #        .format(calc.uuid,calc.dbnode.pk)))
        else:
            inputs["metadata"]["dry_run"] = True
            inputs["metadata"]["store_provenance"] = False
            run(PorousMaterialsCalculation, **inputs)
            print("submission test successful")
            print("In order to actually submit, add '--submit'")


    if __name__ == '__main__':
        main()  # pylint: disable=no-value-for-parameter

    # EOF
