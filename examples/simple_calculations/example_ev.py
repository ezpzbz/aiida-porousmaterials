""" Sample run script for PorousMaterials Plugin"""
import os
import sys
import click
import pytest

from aiida.common import NotExistent
from aiida.orm import Code, Dict
from aiida.plugins import DataFactory
from aiida.engine import run, run_get_pk
from aiida_porousmaterials.calculations import PorousMaterialsCalculation

# Reading the structure and convert it to structure data.
SinglefileData = DataFactory('singlefile')  # pylint: disable=invalid-name
CifData = DataFactory('cif')  # pylint: disable=invalid-name


def example_ev(julia_code, submit=True):
    """
    Example to prepare and run a Sinlge Component
    """

    pwd = os.path.dirname(os.path.realpath(__file__))
    framework = CifData(file=os.path.join(pwd, 'files', 'HKUST1.cif')).store()
    acc_voronoi_nodes = SinglefileData(file=os.path.join(pwd, 'files', 'HKUST1.voro_accessible')).store()
    data_path = os.path.join(pwd, 'data')
    parameters = Dict(
        dict={
            'data_path': data_path,
            'ff': 'UFF.csv',
            'cutoff': 12.5,
            'mixing': 'Lorentz-Berthelot',
            'framework': framework.filename,
            'frameworkname': framework.filename[:-4],
            'adsorbate': "Xe",
            'temperature': 298.0,
            'output_filename': "Ev_" + framework.filename[:-4] + ".csv",
            'input_template': 'ev_vdw_kh_1comp_template',
            'ev_setting': [99, 95, 90, 80, 50],  # if not defined the default is [90,80,50]
        }
    )

    builder = PorousMaterialsCalculation.get_builder()
    builder.structure = {framework.filename[:-4]: framework}
    builder.parameters = parameters
    builder.acc_voronoi_nodes = {framework.filename[:-4]: acc_voronoi_nodes}
    builder.code = julia_code
    builder.metadata.options.resources = { #pylint: disable = no-member
        'num_machines': 1,
        'num_mpiprocs_per_machine': 1,
    }
    builder.metadata.options.max_wallclock_seconds = 1 * 30 * 60  #pylint: disable = no-member
    builder.metadata.options.withmpi = False  #pylint: disable = no-member

    if submit:
        print('Testing PorousMaterials Ev for single component...')
        res, pk = run_get_pk(builder)
        print('Voronoi Energy is: ', res['output_parameters'].dict.HKUST1['Ev_probe']['Ev_minimum'])
        print('calculation pk: ', pk)
        print('OK, calculation has completed successfully')
        pytest.base_calc_pk = pk
    else:
        print('Generating test input ...')
        builder.metadata.dry_run = True  #pylint: disable = no-member
        builder.metadata.store_provenance = False  #pylint: disable = no-member
        run(builder)
        print('submission test successful')
        print("In order to actually submit, add '--submit'")
    print('-----------')


@click.command('cli')
@click.argument('codelabel')
@click.option('--submit', is_flag=True, help='Actually submit calculation')
def cli(codelabel, submit):
    """Click interface"""
    try:
        code = Code.get_from_string(codelabel)
    except NotExistent:
        print("The code '{}' does not exist".format(codelabel))
        sys.exit(1)
    example_ev(code, submit)


if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter

# EOF
