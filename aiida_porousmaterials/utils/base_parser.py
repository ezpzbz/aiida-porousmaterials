# -*- coding: utf-8 -*-
"""Basic PorousMaterials parser."""
from __future__ import absolute_import
import pandas as pd


def parse_base_output(output_abs_path):
    """Parse Ev PorousMaterials output file"""
    # Getting the density
    K_to_kJ_mol = 1.0 / 120.273  # pylint: disable=invalid-name

    with open(output_abs_path) as file:
        lines = file.readlines()
        density = float(lines[2])
        temperature = float(lines[4])

    df = pd.read_csv(output_abs_path, skiprows=5)  # pylint: disable=invalid-name
    results = {}
    results['Ev_unit'] = 'kJ/mol'

    total_num_nodes = df.shape[0]
    minimum = df.Ev_K.min()
    maximum = df.Ev_K.max()
    df_min = df.loc[df.Ev_K == minimum]
    df_max = df.loc[df.Ev_K == maximum]
    minimum_node_properties = [float(df_min.Rv_A), float(df_min.x), float(df_min.y), float(df_min.z)]
    maximum_node_properties = [float(df_max.Rv_A), float(df_max.x), float(df_max.y), float(df_max.z)]

    results['Ev_minimum'] = minimum * K_to_kJ_mol
    results['Ev_maximum'] = maximum * K_to_kJ_mol
    results['minimum_node_radius'] = minimum_node_properties[0]
    results['minimum_node_coord_x'] = minimum_node_properties[1]
    results['minimum_node_coord_y'] = minimum_node_properties[2]
    results['minimum_node_coord_z'] = minimum_node_properties[3]
    results['maximum_node_radius'] = maximum_node_properties[0]
    results['maximum_node_coord_x'] = maximum_node_properties[1]
    results['maximum_node_coord_y'] = maximum_node_properties[2]
    results['maximum_node_coord_z'] = maximum_node_properties[3]
    results['coordinates'] = 'Cartesian'
    results['density'] = density
    results['temperature'] = temperature
    results['node_radius_unit'] = 'angstrom'
    results['total_number_of_accessible_Voronoi_nodes'] = total_num_nodes

    return results


# EOF
