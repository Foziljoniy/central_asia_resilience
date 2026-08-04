"""Audit Kazakhstan FIES microdata formats and variable metadata."""

from kazakhstan_fies_common import dataset_inventory, design_registry, derived_indicator_registry, microdata_inventory, variable_metadata


if __name__ == "__main__":
    microdata_inventory()
    dataset_inventory()
    variable_metadata()
    derived_indicator_registry()
    design_registry()
