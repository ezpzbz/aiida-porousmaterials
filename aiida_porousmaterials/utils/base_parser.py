# -*- coding: utf-8 -*-
"""Basic PorousMaterials parser."""
from __future__ import absolute_import
import os
import pandas as pd

def parse_base_output(output_abs_path, ev_setting):
    """Parse Ev PorousMaterials output file"""
    df = pd.read_csv(output_abs_path)
    results = {}
    results['Ev_unit'] = 'kJ/mol'
    average = df['Ev(kJ/mol)'].mean()
    total_num_nodes = df.shape[0]
    minimum = df['Ev(kJ/mol)'].min()
    df_min = df.loc[df['Ev(kJ/mol)'] == minimum]
    minimum_node_properties = [float(df_min['Rv(A)']), float(df_min['x']), float(df_min['y']), float(df_min['z'])]
    results['Ev_average'] = average
    results['Ev_minimum'] = minimum
    results['minimum_node_radius'] = minimum_node_properties[0]
    results['minimum_node_coord_x'] = minimum_node_properties[1]
    results['minimum_node_coord_y'] = minimum_node_properties[2]
    results['minimum_node_coord_z'] = minimum_node_properties[3]
    results['coordinates'] = 'Cartesian'
    results['minimum_node_radius_unit'] = 'angstrom'
    results['total_number_of_accessible_Voronoi_nodes'] = total_num_nodes
    for i in ev_setting:
        threshold = (i / 100) * minimum
        df_selected = df[df['Ev(kJ/mol)'] <= threshold]
        num_selected_nodes = df_selected.shape[0]
        percentile_average = df_selected.mean()['Ev(kJ/mol)']
        results["Ev_p" + str(i)] = percentile_average
        results["number_of_Voronoi_nodes_in_p" + str(i)] = num_selected_nodes

    return results
# EOF
