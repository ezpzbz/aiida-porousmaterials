"""Basic PorousMaterials parser."""
import pandas as pd


def parse_base_output(output_abs_path):
    """
    Parse Ev PorousMaterials output file
    Any change on data (except unit conversion)
    is avoided here! Those data processing calculations
    should be done within a workchain and thourgh a
    calcfunction.
    """
    K_to_kJ_mol = 1.0 / 120.273  # pylint: disable=invalid-name

    with open(output_abs_path) as file:
        lines = file.readlines()
        density = float(lines[2])
        temperature = float(lines[4])

    df = pd.read_csv(output_abs_path, skiprows=5)  # pylint: disable=invalid-name
    results = {}
    results['energy_unit'] = 'kJ/mol'

    total_num_nodes = df.shape[0]
    minimum = df.Ev_K.min()
    maximum = df.Ev_K.max()
    df_min = df.loc[df.Ev_K == minimum]
    df_max = df.loc[df.Ev_K == maximum]

    results['Ev_minimum'] = minimum * K_to_kJ_mol
    results['Ev_maximum'] = maximum * K_to_kJ_mol

    # We may have several nodes with minim or maximum energy, so! More Code!
    results['minimum_nodes_props'] = {}
    results['maximum_nodes_props'] = {}
    results['header_nodes_props'] = ['Boltzmann_factor', 'Weighted_energy', 'radius', 'x', 'y', 'z']

    for index, row in df_min.iterrows():
        minimum_node_properties = []
        minimum_node_properties = [
            row.boltzmann_factor, row.weighted_energy_K * K_to_kJ_mol, row.Rv_A, row.x, row.y, row.z
        ]
        results['minimum_nodes_props']['node_' + str(index)] = minimum_node_properties

    for index, row in df_max.iterrows():
        maximum_node_properties = []
        maximum_node_properties = [
            row.boltzmann_factor, row.weighted_energy_K * K_to_kJ_mol, row.Rv_A, row.x, row.y, row.z
        ]
        results['maximum_nodes_props']['node_' + str(index)] = maximum_node_properties

    results['coordinate_system'] = 'Cartesian'
    results['framework_density'] = density
    results['framework_density_unit'] = 'kg/m3'
    results['temperature'] = temperature
    results['temperature_unit'] = 'Kelvin'
    results['radius_unit'] = 'Angstrom'
    results['total_number_of_accessible_Voronoi_nodes'] = total_num_nodes

    return results


# EOF
