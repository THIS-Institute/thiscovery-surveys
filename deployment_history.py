#!/usr/bin/env python3

import local.dev_config  # set environment variables
import local.secrets  # set environment variables
import subprocess
import thiscovery_lib.utilities as utils
from src.common.constants import STACK_NAME


if __name__ == '__main__':
    env_name = utils.get_environment_name()
    history = subprocess.run(
        ['stackery', 'history', f'--stack-name={STACK_NAME}', f'--env-name={env_name}']
    )
    print(history)
