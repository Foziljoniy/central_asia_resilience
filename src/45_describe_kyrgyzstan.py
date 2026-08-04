"""Phase 4G-J Kyrgyzstan descriptive entry point."""
from phase4_common import kyrgyzstan_outputs, load_data, setup_logging

if __name__ == "__main__":
    setup_logging()
    kyrgyzstan_outputs(load_data())
