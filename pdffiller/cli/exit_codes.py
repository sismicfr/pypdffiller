# Exit codes for pdffiller command:
SUCCESS = 0  # 0: Success
ERROR_GENERAL = 1  # 1: General exception error
USER_CTRL_C = 2  # 2: Ctrl+C
USER_CTRL_BREAK = 3  # 3: Ctrl+Break
ERROR_SIGTERM = 4  # 4: SIGTERM
ERROR_UNEXPECTED = 5  # 5: Unexpected error
ERROR_ENCOUNTERED = 6  # 6: Error occurs during command execution
ERROR_COMMAND_NAME = 7  # 7: Action/command name missing
ERROR_SUBCOMMAND_NAME = 8  # 8: Sub-command name missing
