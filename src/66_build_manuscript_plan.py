"""Build final table and figure plans plus manuscript materials."""
from phase6_common import manuscript_materials, plans_and_registers, read_sources, setup_logging
if __name__ == "__main__":
    setup_logging(); manuscript_materials(read_sources()); plans_and_registers()
