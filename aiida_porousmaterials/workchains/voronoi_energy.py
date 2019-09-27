"""
Voronoi Energy Calculation WorkChain
"""
from __future__ import absolute_import
import os

from aiida.common import AttributeDict
from aiida.plugins import CalculationFactory, DataFactory
from aiida.orm import Dict, List, SinglefileData
from aiida.engine import calcfunction, ToContext, WorkChain, if_
from aiida_porousmaterials.workchains import PorousMaterialsBaseWorkChain

CifData = DataFactory("cif")  # pylint: disable=invalid-name
ZeoppCalculation = CalculationFactory("zeopp.network")  # pylint: disable=invalid-name
PorousMaterialsCalculation = CalculationFactory("porousmaterials")  # pylint: disable=invalid-name
NetworkParameters = DataFactory("zeopp.parameters")  # pylint: disable=invalid-name


@calcfunction
def extract_wrap_results(**kwargs):
    """
    It gets all generated output_parameters from workchain,
    process them, and wrap them in a single Dict object!
    """
    results = {}
    # ZeoppCalculation Section
    results['zeopp'] = {}
    results['zeopp']['Largest_free_sphere'] = kwargs['zeopp_res'].get_dict()['Largest_free_sphere']
    results['zeopp']['Largest_included_sphere'] = kwargs['zeopp_res'].get_dict()['Largest_included_sphere']
    if 'zeopp_res_re' in kwargs.keys():
        results['zeopp']['S100'] = {}
        results['zeopp']['S100']['Largest_free_sphere'] = kwargs['zeopp_res_re'].get_dict()['Largest_free_sphere']
        results['zeopp']['S100']['Largest_included_sphere'] = kwargs['zeopp_res_re'].get_dict(
        )['Largest_included_sphere']
    if 'zeopp_visvoro' in kwargs.keys():
        results['zeopp']['visVoro_probe_radius'] = kwargs['zeopp_visvoro'].get_dict()['Input_visVoro']
    # PorousMaterials Secion!
    if 'pm_ev' in kwargs.keys():
        import pandas as pd
        ev_setting = kwargs['ev_setting']
        results['porousmaterials'] = {}
        results["porousmaterials"] = kwargs['pm_out'].get_dict()
        fname = kwargs['pm_ev'].filename
        output_abs_path = os.path.join(
            kwargs['pm_ev']._repository._get_base_folder().abspath,  # pylint: disable=protected-access
            fname)
        df = pd.read_csv(output_abs_path)  # pylint: disable=invalid-name
        minimum = df['Ev(kJ/mol)'].min()
        average = df['Ev(kJ/mol)'].mean()
        results['porousmaterials']['Ev_average'] = average
        for percentile in ev_setting:
            threshold = (percentile / 100) * minimum
            df_selected = df[df['Ev(kJ/mol)'] <= threshold]
            num_selected_nodes = df_selected.shape[0]
            percentile_average = df_selected.mean()['Ev(kJ/mol)']
            results['porousmaterials']["Ev_p" + str(percentile)] = percentile_average
            results['porousmaterials']["number_of_Voronoi_nodes_in_p" + str(percentile)] = num_selected_nodes

    return Dict(dict=results)


class VoronoiEnergyWorkChain(WorkChain):
    """
    The VoronoiEnergyWorkChain is designed to perform zeo++ and
    PorousMaterials calculations to obtain and exctract Voronoi
    energy.
    """

    @classmethod
    def define(cls, spec):
        """
        Define workflow specification.
        This is the most important method of a Workchain, which defines the
        inputs it takes, the logic of the execution and the outputs
        that are generated in the process.
        """
        super(VoronoiEnergyWorkChain, cls).define(spec)

        # Zeopp
        spec.expose_inputs(ZeoppCalculation, namespace='zeopp', exclude=['parameters', 'structure'])

        # PorousMaterialsCalculation
        spec.expose_inputs(
            PorousMaterialsBaseWorkChain, namespace='porousmaterials_base', exclude=['porousmaterials.structure'])

        # VoronoiEnergyWorkChain specific inputs!
        spec.input("structure", valid_type=CifData, required=True, help="Input structure in cif format")
        spec.input("parameters", valid_type=Dict, required=False, help="Parameters to do the logic in workchain")

        # Workflow
        spec.outline(
            cls.setup,
            cls.run_zeopp_res,
            if_(cls.should_run_zeopp_visvoro)(if_(cls.should_reperform_zeopp_res)(cls.run_zeopp_res),
                                              cls.run_zeopp_visvoro),
            if_(cls.should_run_ev)(cls.run_ev),
            cls.return_results,
        )

        # to be returned
        spec.output('accessible_voronoi_nodes', valid_type=SinglefileData, required=False, help='testing')
        spec.output('structure_cssr', valid_type=SinglefileData, required=False, help='testing')
        spec.output('results', valid_type=Dict, required=False, help='Aggregated results of whole workchain!')

    def setup(self):
        """
        Initialize variables and setup screening protocol!
        """
        # set PLD reperform flag to False:
        self.ctx.reperform = False
        # Create context of general calculations parameters.
        self.ctx.parameters = self.inputs.parameters

    def run_zeopp_res(self):
        """
        It performs the zeopp pore diameter calculation.
        """
        zeopp_input = AttributeDict(self.exposed_inputs(ZeoppCalculation, 'zeopp'))
        zeopp_input['structure'] = self.inputs.structure
        # First run a short run without -ha to have the LCD/PLD estimation for pre-screening.
        # If the structure is selected and PLD-based protocol is chosen,
        # it will be reperformed at high accuracy, ie. S100
        if self.ctx.reperform:
            ha_flag = self.ctx.parameters['accuracy_high']
            params = {"res": True, "ha": ha_flag}
        else:
            params = {
                "cssr": True,
                "res": True,
            }
        zeopp_input['parameters'] = NetworkParameters(dict=params)

        # Use default zeopp atomic radii only if a .rad file is not specified
        try:
            zeopp_input['atomic_radii'] = self.inputs.zeopp.atomic_radii
            self.report("Zeopp will use atomic radii from the .rad file")
        except ValueError:
            self.report("Zeopp will use default atomic radii")

        # Creating the calculation process and submit it
        # It needed to be separated as -ha flag outputs the cssr of
        # supercell.
        if self.ctx.reperform:
            res_re = self.submit(ZeoppCalculation, **zeopp_input)
            self.report("pk: <{}> | Re-Running zeo++ pore diameter calculation".format(res_re.pk))
            return ToContext(zeopp_res_re=res_re)

        res = self.submit(ZeoppCalculation, **zeopp_input)
        self.report("pk: <{}> | Running zeo++ pore diameter calculation".format(res.pk))
        return ToContext(zeopp_res=res)

    def should_run_zeopp_visvoro(self):
        """
        It uses largest included sphere (Di or LCD) and largest free sphere
        (Df or PLD) as pre-screenig descriptors to pass or reject the
        structure.
        """

        lcd_lim = self.ctx.parameters['lcd_max']
        pld_lim = self.ctx.parameters['pld_min']
        lcd_current = self.ctx.zeopp_res.outputs.output_parameters.get_dict()["Largest_included_sphere"]
        pld_current = self.ctx.zeopp_res.outputs.output_parameters.get_dict()["Largest_free_sphere"]
        if (lcd_current < lcd_lim) and (pld_current > pld_lim):
            self.report("<{}> is a suitable structure for further investigation".format(self.inputs.structure.label))
            return True
        self.report("<{}> does not look like promising: stop".format(self.inputs.structure.label))
        return False

    def should_reperform_zeopp_res(self):
        """
        It decides that if we should run another pore diamter calculation at
        higher accuracy level or just using user-defined probe for visVoro.
        """

        if self.ctx.parameters['pld_based']:
            self.ctx.reperform = True
            self.report("PLD-based protocol is chosen!")
            return True

        self.report("Probe-based protocol is chosen!")
        return False

    def run_zeopp_visvoro(self):
        """
        It performs the visVoro calculation.
        """
        zeopp_inp = AttributeDict(self.exposed_inputs(ZeoppCalculation, 'zeopp'))
        zeopp_inp['structure'] = self.inputs.structure

        # Getting the probe_radius based on the chosen protocol.
        if self.ctx.parameters['pld_based']:
            probe_radius = self.ctx.zeopp_res.outputs.output_parameters.get_dict()["Largest_free_sphere"] / 2
            self.report("The pld-based chosen probe size is <{}>".format(probe_radius))
        probe_radius = self.ctx.parameters['probe_radius']
        self.report("I am here with probe radius of {}".format(probe_radius))
        # Setting up the parameters based on the desired accuracy level for visVoro.
        if self.ctx.parameters['visvoro_ha']:
            ha_flag = self.ctx.parameters['visvoro_accuracy']
            params = {'visVoro': probe_radius, 'ha': ha_flag}

        params = {"visVoro": probe_radius}

        zeopp_inp['parameters'] = NetworkParameters(dict=params)
        # Use default zeopp atomic radii only if a .rad file is not specified
        if self.ctx.zeopp_res.inputs.atomic_radii is not None:
            zeopp_inp['atomic_radii'] = self.ctx.zeopp_res.inputs.atomic_radii

        # Creating the calculation process and submit it
        visvoro = self.submit(ZeoppCalculation, **zeopp_inp)
        self.report("pk: <{}> | Running Zeo++ visVoro calculation using <{}> probe".format(visvoro.pk, probe_radius))
        return ToContext(zeopp_visvoro=visvoro)

    def should_run_ev(self):
        """
        It checks if there is any accessible Voronoi nodes or not!
        If there is any, it submits a PorousMaterials calculation.
        """
        visvoro_dir = self.ctx.zeopp_visvoro.outputs.retrieved._repository._get_base_folder().abspath  # pylint: disable=protected-access
        visvoro_path = os.path.join(visvoro_dir, "out.visVoro.voro_accessible")
        with open(visvoro_path, "r") as fobj:
            self.ctx.number_acc_voronoi_nodes = int(fobj.readline().strip())
            if self.ctx.number_acc_voronoi_nodes > 0:
                self.report("Found <{}> accessible Voronoi nodes".format(self.ctx.number_acc_voronoi_nodes))
                return True

            self.report("No accessible Voronoi nodes!: stop")
            return False

    def run_ev(self):
        """
        It runs a Ev calculation in PorousMaterials.
        """
        pm_input = AttributeDict(self.exposed_inputs(PorousMaterialsBaseWorkChain, 'porousmaterials_base'))
        pm_input['porousmaterials']['structure'] = {}
        pm_input['porousmaterials']['acc_voronoi_nodes'] = {}
        pm_input['porousmaterials']['structure'][
            self.inputs.structure.filename[:-4]] = self.ctx.zeopp_res.outputs.structure_cssr
        pm_input['porousmaterials']['acc_voronoi_nodes'][
            self.inputs.structure.filename[:-4]] = self.ctx.zeopp_visvoro.outputs.voro_accessible

        pm_ev = self.submit(PorousMaterialsBaseWorkChain, **pm_input)  # pylint: disable=invalid-name
        self.report("pk: <{}> | Running Voronoi Energy Calculation".format(pm_ev.pk))
        return ToContext(pm_ev=pm_ev)

    def return_results(self):
        """
        Attach the results to the output.
        """
        output_parameters = {}
        all_outputs = {}
        # ZeoppCalculation Section
        # We assume that at least the first zeopp calculation has been performed!
        all_outputs['zeopp_res'] = self.ctx.zeopp_res.outputs.output_parameters

        if self.ctx.reperform:
            all_outputs['zeopp_res_re'] = self.ctx.zeopp_res_re.outputs.output_parameters
        if self.ctx.zeopp_visvoro.is_finished_ok:
            all_outputs['zeopp_visvoro'] = self.ctx.zeopp_visvoro.outputs.output_parameters
            if 'voro_accessible' in self.ctx.zeopp_visvoro.outputs:
                self.out('accessible_voronoi_nodes', self.ctx.zeopp_visvoro.outputs.voro_accessible)

        # PorousMaterials Section!
        if self.ctx.pm_ev.is_finished_ok:
            all_outputs['pm_ev'] = self.ctx.pm_ev.outputs.ev_output_file
            all_outputs['pm_out'] = self.ctx.pm_ev.outputs.output_parameters
            if 'ev_setting' in self.ctx.parameters.get_dict():
                all_outputs['ev_setting'] = List(list=self.ctx.parameters['ev_setting'])
            else:
                all_outputs['ev_setting'] = List(list=[90, 80, 50])

        output_parameters = extract_wrap_results(**all_outputs)

        self.out('structure_cssr', self.ctx.zeopp_res.outputs.structure_cssr)
        # Finalizing the results and report!
        self.out("results", output_parameters)
        self.report("Workchain completed successfully! | Result Dict is <{}>".format(self.outputs["results"].pk))
        # return


# EOF
