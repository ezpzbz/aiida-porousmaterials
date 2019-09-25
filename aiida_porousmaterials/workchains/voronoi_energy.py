"""
Voronoi Energy Calculation WorkChain
"""
from __future__ import absolute_import
import os

from aiida.plugins import CalculationFactory, DataFactory
from aiida.orm import Code, Dict, SinglefileData
from aiida.engine import submit  # pylint: disable=unused-import
from aiida.engine import ToContext, WorkChain, if_

CifData = DataFactory("cif")  # pylint: disable=invalid-name
ParameterData = DataFactory("dict")  # pylint: disable=invalid-name
# SinglefileData = DataFactory("singlefile")  # pylint: disable=invalid-name
# FolderData = DataFactory('folder')  # pylint: disable=invalid-name
ZeoppCalculation = CalculationFactory("zeopp.network")  # pylint: disable=invalid-name
PorousMaterialsCalculation = CalculationFactory("porousmaterials")  # pylint: disable=invalid-name
NetworkParameters = DataFactory("zeopp.parameters")  # pylint: disable=invalid-name

# Lambda function taken from (https://stackoverflow.com/a/36977549)
# to make report nicer by using ordinary numbers.
ordinal = lambda n: "%d%s" % (n, {1: "st", 2: "nd", 3: "rd"}.get(n if n < 20 else n % 10, "th"))  # pylint: disable=invalid-name


class VoronoiEnergyWorkChain(WorkChain):
    """
    The VoronoiEnergyWorkChain is designed to perform zeo++ and
    PorousMaterials calculations.
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

        # General inputs
        spec.input("structure", valid_type=CifData, required=True, help="Input structure in cif format")
        spec.input("general_calc_params", valid_type=Dict, required=False)

        # Zeopp inputs
        spec.input("zeopp_code", valid_type=Code, required=False)
        spec.input("zeopp_atomic_radii", valid_type=SinglefileData, required=False)

        # PorousMaterials inputs
        spec.input("julia_code", valid_type=Code, required=False)
        spec.input("pm_parameters", valid_type=ParameterData, required=False)

        # Scheduler options.
        spec.input_namespace("zeopp_options", required=False, dynamic=True, non_db=True)
        spec.input_namespace("julia_options", required=False, dynamic=True, non_db=True)

        # Workflow
        spec.outline(
            cls.setup,
            cls.run_pore_dia_zeopp,
            if_(cls.should_run_zeopp_visvoro)(if_(cls.should_run_ha_pld)(cls.run_pore_dia_zeopp),
                                              cls.run_zeopp_visvoro),
            if_(cls.should_run_ev)(
                # cls.init_ev,
                cls.run_ev,),
            cls.return_results,
        )
        # )
        # to be returned
        spec.outputs.dynamic = True

    def setup(self):
        """
        Initialize variables and setup screening protocol!
        """
        # set PLD reperform flag to False:
        self.ctx.reperform = False

        # Create context of general calculations parameters.
        self.ctx.general_calc_params = self.inputs.general_calc_params

        # Scheduler options
        self.ctx.zeopp_options = self.inputs.zeopp_options
        self.ctx.julia_options = self.inputs.julia_options

    def run_pore_dia_zeopp(self):
        """
        It performs the zeopp pore diameter calculation.
        """
        # Required inputs
        # ha_flag = self.ctx.general_calc_params["zeopp"]["accuracy_low"]

        # First run a short run without -ha to have the LCD/PLD estimation for pre-screening.
        # If the structure is selected and PLD-based protocol is chosen,
        # it will be reperformed at high accuracy, ie. S100
        if self.ctx.reperform:
            ha_flag = self.ctx.general_calc_params["zeopp"]["accuracy_high"]
            params = {"res": True, "cssr": True, "ha": ha_flag}
        else:
            params = {
                "cssr": True,
                "res": True,
            }

        parameters = NetworkParameters(dict=params)

        inputs = {
            "code": self.inputs.zeopp_code,
            "structure": self.inputs.structure,
            "parameters": parameters,
            "metadata": {
                "options": self.ctx.zeopp_options,
                "label": "Pore Diameter Calculation",
                "description": "Pore Diameter Calculation for <{}>".format(self.inputs.structure.label)
            }
        }

        # Use default zeopp atomic radii only if a .rad file is not specified
        try:
            inputs["atomic_radii"] = self.inputs.zeopp_atomic_radii
            self.report("Zeopp will use atomic radii from the .rad file")
        except ValueError:
            self.report("Zeopp will use default atomic radii")

        # Creating the calculation process and submit it
        # It needed to be separated as -ha flag outputs the cssr of
        # supercell.
        if self.ctx.reperform:
            res_re = self.submit(ZeoppCalculation, **inputs)
            self.report("pk: <{}> | Re-Running zeo++ pore diameter calculation".format(res_re.pk))
            return ToContext(zeopp_res_re=res_re)

        res = self.submit(ZeoppCalculation, **inputs)
        self.report("pk: <{}> | Running zeo++ pore diameter calculation".format(res.pk))
        return ToContext(zeopp_res=res)

    def should_run_zeopp_visvoro(self):
        """
        It uses largest included sphere (Di or LCD) and largest free sphere
        (Df or PLD) as pre-screenig descriptors to pass or reject the
        structure.
        """

        lcd_lim = self.ctx.general_calc_params["zeopp"]["lcd_max"]
        pld_lim = self.ctx.general_calc_params["zeopp"]["pld_min"]
        lcd_current = self.ctx.zeopp_res.outputs.output_parameters.get_dict()["Largest_included_sphere"]
        pld_current = self.ctx.zeopp_res.outputs.output_parameters.get_dict()["Largest_free_sphere"]

        if (lcd_current < lcd_lim) and (pld_current > pld_lim):
            self.report("<{}> is a suitable structure for further investigation".format(self.inputs.structure.label))
            return True

        self.report("<{}> does not look like promising: stop".format(self.inputs.structure.label))
        return False

    def should_run_ha_pld(self):
        """
        It decides that if we should run another pore diamter calculation at
        higher accuracy level or just using user-defined probe for visVoro.
        """

        if self.ctx.general_calc_params["porousmaterials"]["pld_based"]:
            self.ctx.reperform = True
            self.report("PLD-based protocol is chosen!")
            return True

        self.report("Probe-based protocol is chosen!")
        return False

    def run_zeopp_visvoro(self):
        """
        It performs the visVoro calculation.
        """
        # Getting the probe_radius based on the chosen protocol.
        if self.ctx.general_calc_params["porousmaterials"]["pld_based"]:
            probe_radius = self.ctx.zeopp_res.outputs.output_parameters.get_dict()["Largest_free_sphere"] / 2
        else:
            probe_radius = self.ctx.general_calc_params["zeopp"]["probe_radius"]

        # Setting up the parameters based on the desired accuracy level for visVoro.
        if self.ctx.general_calc_params["zeopp"]["visvoro_ha"]:
            ha_flag = self.ctx.general_calc_params["zeopp"]["visvoro_accuracy"]
            params = {"visVoro": probe_radius, "ha": ha_flag}
        else:
            params = {
                "visVoro": probe_radius,
            }

        parameters = NetworkParameters(dict=params).store()

        # Required inputs
        inputs = {
            "code": self.inputs.zeopp_code,
            "structure": self.inputs.structure,
            "parameters": parameters,
            "metadata": {
                "options": self.ctx.zeopp_options,
                "label": "Zeo++ visVoro Calculation",
                "description": "Zeo++ visVoro Calculation for <{}>".format(self.inputs.structure.label)
            }
        }

        try:
            inputs["atomic_radii"] = self.inputs.zeopp_atomic_radii
            self.report("Zeopp will use atomic radii from the .rad file")
        except ValueError:
            self.report("Zeopp will use default atomic radii")

        # Creating the calculation process and submit it
        visvoro = self.submit(ZeoppCalculation, **inputs)
        self.report("pk: <{}> | Running Zeo++ visVoro calculation using <{}> probe".format(visvoro.pk, probe_radius))
        return ToContext(visvoro=visvoro)

    def should_run_ev(self):
        """
        It checks if there is any accessible Voronoi nodes or not!
        If there is any, it submits a PorousMaterials calculation.
        """
        visvoro_dir = self.ctx.visvoro.outputs.retrieved._repository._get_base_folder().abspath  # pylint: disable=protected-access
        visvoro_path = os.path.join(visvoro_dir, "out.visVoro_voro_accessible.xyz")

        with open(visvoro_path, "r") as fobj:
            self.ctx.number_acc_voronoi_nodes = int(fobj.readline().strip())
            if self.ctx.number_acc_voronoi_nodes > 0:
                self.report("Found <{}> accessible Voronoi nodes".format(self.ctx.number_acc_voronoi_nodes))
                return True

            self.report("No accessible Voronoi nodes!: stop")
            return False

    # def init_ev(self):
    #     """
    #     It generates the ParameterData for PorousMaterials calculation.
    #     """
    #     # Renaming the cssr file.
    #     cssr_dir = self.ctx.zeopp_res.outputs.structure_cssr._repository._get_base_folder().abspath
    #     new_filename = self.inputs.structure.label + "_voro_accessible.xyz"
    #     os.rename(os.path.join(cssr_dir,"out.cssr"), os.path.join(cssr_dir,new_filename))
    #
    #     # Create a deepcopy of the user parameters, to modify before submission
    #     self.ctx.pm_parameters = deepcopy(self.inputs.pm_parameters.get_dict())
    #
    #
    #     return

    def run_ev(self):
        """
        It runs a Ev calculation in PorousMaterials.
        """

        # Create the inputs dictionary
        inputs = {
            # "structure"  : self.ctx.zeopp_res.outputs.structure_cssr,
            "code": self.inputs.julia_code,
            "parameters": self.inputs.pm_parameters,
            # "voronoi_nodes" : self.ctx.visvoro.outputs.acc_nodes_visvoro,
            "metadata": {
                "options": self.ctx.julia_options,
                "label": "PorousMaterials Ev Calculation",
                "description": "PorousMaterials Ev Calculation for <{}>".format(self.inputs.structure.label)
            }
        }
        inputs['structure'] = {}
        inputs['acc_voronoi_nodes'] = {}

        inputs['structure'][self.inputs.structure.filename[:-4]] = self.ctx.zeopp_res.outputs.structure_cssr
        inputs['acc_voronoi_nodes'][self.inputs.structure.filename[:-4]] = self.ctx.visvoro.outputs.acc_nodes_visvoro

        ev = self.submit(PorousMaterialsCalculation, **inputs)  # pylint: disable=invalid-name
        self.report("pk: <{}> | Running Voronoi Energy Calculation".format(ev.pk))
        return ToContext(pm_ev=ev)

    def return_results(self):
        """
        Attach the results to the output.
        """
        # Create empty results dictionary.
        result_dict = {}

        # Zeopp section
        try:
            # Output of Di and Df
            result_dict["Largest_included_sphere"] = self.ctx.zeopp_res.outputs.output_parameters.get_dict(
            )["Largest_included_sphere"]
            result_dict["Largest_free_sphere"] = self.ctx.zeopp_res.outputs.output_parameters.get_dict(
            )["Largest_free_sphere"]
        except AttributeError:
            pass

        # PorousMaterials section
        try:
            # Getting the output parameters
            output_pm = self.ctx.pm_ev.outputs.output_parameters.get_dict()
            result_dict.update(output_pm)
        except AttributeError:
            pass

        # Voronoi Nodes Section
        self.out("accessible_voronoi_nodes", self.ctx.visvoro.outputs.acc_nodes_visvoro)

        # Finalizing the results and report!
        self.out("results", ParameterData(dict=result_dict).store())
        self.report("Workchain completed successfully! | Result Dict is <{}>".format(self.outputs["results"].pk))
        # return


# EOF
