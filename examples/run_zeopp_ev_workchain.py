# -*- coding: utf-8 -*-
""" Sample run script for VoronoiEnergyWorkChain"""
from __future__ import print_function
from __future__ import absolute_import
import os
import sys

from aiida.common import NotExistent
from aiida.orm import Code, Dict
from aiida.plugins import DataFactory
from aiida.engine import submit
from aiida_porousmaterials.workflows.voronoi_energy import VoronoiEnergyWorkChain

# Reading the structure and convert it to structure data.
ParameterData = DataFactory("dict")  # pylint: disable=invalid-name
SinglefileData = DataFactory('singlefile')  # pylint: disable=invalid-name
CifData = DataFactory('cif')  # pylint: disable=invalid-name

structure = CifData(file=os.path.abspath("./HKUST1.cif"))  # pylint: disable=invalid-name
structure.label = structure.filename.lower()[:-4]

# Reading code information from system argv
if len(sys.argv) != 3:
    print("Usage: test.py <zeopp_code_name> <julia_code_name>")
    sys.exit(1)

zeopp_codename = sys.argv[1]  # pylint: disable=invalid-name
julia_codename = sys.argv[2]  # pylint: disable=invalid-name

try:
    zeopp_code = Code.get_from_string(zeopp_codename)  # pylint: disable=invalid-name
except NotExistent:
    print("The code '{}' does not exist".format(zeopp_codename))  # pylint: disable=invalid-name
    sys.exit(1)

try:
    julia_code = Code.get_from_string(julia_codename)  # pylint: disable=invalid-name
except NotExistent:
    print("The code '{}' does not exist".format(julia_codename))
    sys.exit(1)

zeopp_atomic_radii_file = SinglefileData(file=os.path.abspath("./UFF.rad"))  # pylint: disable=invalid-name

general_calc_params = Dict( # pylint: disable=invalid-name
    dict={
        "zeopp": {
            "pld_min": 3.90,
            "lcd_max": 15.0,
            "visvoro_ha": False,
            "visvoro_accuracy": "DEF",
            "accuracy_high": "DEF",
            "probe_radius": 1.98,
        },
        "porousmaterials": {
            "pld_based": False,
        },
    })

pm_parameters = Dict( # pylint: disable=invalid-name
    dict={
        'data_path': "/storage/brno9-ceitec/home/pezhman/projects/noble_gas_epfl/xe_kr/data",
        'ff': 'UFF.csv',
        'cutoff': 12.5,
        'mixing': 'Lorentz-Berthelot',
        'framework': structure.filename[:-4] + '.cssr',
        'frameworkname': structure.filename[:-4],
        'adsorbate': "Xe",
        'output_filename': "Ev_" + structure.filename[:-4] + ".csv",
        'input_template': 'ev_lj_1comp_template',
        'ev_setting': [99, 95, 90, 80, 50],  # if not defined the default is [90,80,50]
    })

zeopp_options = { # pylint: disable=invalid-name
    "resources": {
        "num_machines": 1,
        "tot_num_mpiprocs": 1,
    },
    # "max_memory_kb" : 2000000,
    "max_wallclock_seconds": 1 * 30 * 60,
    "withmpi": False,
}

julia_options = { # pylint: disable=invalid-name
    "resources": {
        "num_machines": 1,
        "tot_num_mpiprocs": 1,
    },
    # "max_memory_kb": 200000,
    "max_wallclock_seconds": 2 * 60 * 60,
    "withmpi": False,
}

submit(VoronoiEnergyWorkChain,
       structure=structure,
       zeopp_code=zeopp_code,
       julia_code=julia_code,
       pm_parameters=pm_parameters,
       zeopp_atomic_radii=zeopp_atomic_radii_file,
       general_calc_params=general_calc_params,
       zeopp_options=zeopp_options,
       julia_options=julia_options,
       metadata={
           "label": "VoronoiEnergyWorkChain",
           "description": "Test for <{}>".format(structure.label)
       })
# EOF
