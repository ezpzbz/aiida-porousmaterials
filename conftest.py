# """
# For pytest initialise a test database and profile
# """
# import pytest
# pytest_plugins = ['aiida.manage.tests.pytest_fixtures']  # pylint: disable=invalid-name
#
#
# @pytest.fixture(scope='function')
# def julia_code(aiida_local_code_factory):  # pylint: disable=unused-argument
#     return aiida_local_code_factory("julia")
