# -*- coding: utf-8 -*-
"""Base workchain to run a PorousMaterials calculation"""
from __future__ import absolute_import

from aiida.common import AttributeDict
from aiida.engine import while_
from aiida.plugins import CalculationFactory

from aiida_porousmaterials.workchains.aiida_base_restart import BaseRestartWorkChain

PorousMaterialsCalculation = CalculationFactory('porousmaterials')  # pylint: disable=invalid-name


class PorousMaterialsBaseWorkChain(BaseRestartWorkChain):
    """Workchain to run a RASPA calculation with automated error handling and restarts."""

    _calculation_class = PorousMaterialsCalculation

    @classmethod
    def define(cls, spec):
        super(PorousMaterialsBaseWorkChain, cls).define(spec)
        spec.expose_inputs(PorousMaterialsCalculation, namespace='porousmaterials')
        spec.outline(
            cls.setup,
            while_(cls.should_run_calculation)(
                cls.run_calculation,
                cls.inspect_calculation,
            ),
            cls.results,
        )
        spec.expose_outputs(PorousMaterialsCalculation)

    def setup(self):
        """Call the `setup` of the `BaseRestartWorkChain` and then create the inputs dictionary in `self.ctx.inputs`.
        This `self.ctx.inputs` dictionary will be used by the `BaseRestartWorkChain` to submit the calculations in the
        internal loop.
        """
        super(PorousMaterialsBaseWorkChain, self).setup()
        self.ctx.inputs = AttributeDict(self.exposed_inputs(PorousMaterialsCalculation, 'porousmaterials'))
