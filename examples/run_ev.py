# -*- coding: utf-8 -*-
""" Sample run script for PorousMaterials Plugin"""
from __future__ import print_function
import os
import sys
import click

from aiida.common import NotExistent
from aiida.orm import Code
from aiida.plugins import DataFactory
from aiida.engine import run
from aiida_porousmaterials.calculations import PorousMaterialsCalculation


# Reading the structure and convert it to structure data.
SinglefileData = DataFactory('singlefile')
CifData = DataFactory('cif')

# Creating the command prompt input options using click
@click.command('cli')
@click.argument('codelabel')
@click.option('--submit', is_flag=True, help='If true, actually submits the clac to the daemon.')

def main(codelabel, submit):
    """hhghghghg
    """
    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print("The code '{}' does not exist".format(codelabel))
        sys.exit(1)

    framework = SinglefileData(file=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'files', 'FIQCEN_clean.cssr'))
    voronoi_nodes = SinglefileData(file=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'files', 'FIQCEN_clean_voro_accessible.xyz'))

    parameters = Dict(dict={
        'data_path': "/storage/brno9-ceitec/home/pezhman/projects/noble_gas_epfl/xe_kr/data",
        'ff':'UFF.csv',
        'cutoff':12.5,
        'mixing':'Lorentz-Berthelot',
        'framework':framework.filename,
        'frameworkname':framework.filename[:-5],
        'adsorbate':"Xe",
        'output_filename':"Ev_" + framework.filename[:-5] + ".csv",
        'input_template' : 'ev_lj_1comp_template',
        'ev_setting' : [99,95,90,80,50], # if not defined the default is [90,80,50]
    })

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
        "structure": framework,
        "parameters": parameters,
        "voronoi_nodes": voronoi_nodes,
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
