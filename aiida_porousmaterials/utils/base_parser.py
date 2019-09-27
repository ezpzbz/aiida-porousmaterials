# -*- coding: utf-8 -*-
"""Basic PorousMaterials parser."""
from __future__ import absolute_import
import pandas as pd


def parse_base_output(output_abs_path):
    """Parse Ev PorousMaterials output file"""
    df = pd.read_csv(output_abs_path)  # pylint: disable=invalid-name
    results = {}
    results['Ev_unit'] = 'kJ/mol'

    total_num_nodes = df.shape[0]
    minimum = df['Ev(kJ/mol)'].min()
    maximum = df['Ev(kJ/mol)'].max()
    df_min = df.loc[df['Ev(kJ/mol)'] == minimum]
    df_max = df.loc[df['Ev(kJ/mol)'] == maximum]
    minimum_node_properties = [float(df_min['Rv(A)']), float(df_min['x']), float(df_min['y']), float(df_min['z'])]
    maximum_node_properties = [float(df_max['Rv(A)']), float(df_max['x']), float(df_max['y']), float(df_max['z'])]

    results['Ev_minimum'] = minimum
    results['Ev_maximum'] = maximum
    results['minimum_node_radius'] = minimum_node_properties[0]
    results['minimum_node_coord_x'] = minimum_node_properties[1]
    results['minimum_node_coord_y'] = minimum_node_properties[2]
    results['minimum_node_coord_z'] = minimum_node_properties[3]
    results['maximum_node_radius'] = maximum_node_properties[0]
    results['maximum_node_coord_x'] = maximum_node_properties[1]
    results['maximum_node_coord_y'] = maximum_node_properties[2]
    results['maximum_node_coord_z'] = maximum_node_properties[3]
    results['coordinates'] = 'Cartesian'
    results['node_radius_unit'] = 'angstrom'
    results['total_number_of_accessible_Voronoi_nodes'] = total_num_nodes

    return results


# EOF
