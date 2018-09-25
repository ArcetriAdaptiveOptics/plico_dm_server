


class Constants:
    METER_2_NANOMETER= 1e9
    APP_NAME= "inaf.arcetri.ao.palpao_server"
    APP_AUTHOR= "INAF Arcetri Adaptive Optics"
    THIS_PACKAGE= 'palpao_server'

    PROCESS_MONITOR_CONFIG_SECTION= 'processMonitor'
    DEFORMABLE_MIRROR_1_CONFIG_SECTION= 'server1'
    DEFORMABLE_MIRROR_2_CONFIG_SECTION= 'server2'

    # TODO: must be the same of console_scripts in setup.py
    START_PROCESS_NAME= 'palpao_start'
    STOP_PROCESS_NAME= 'palpao_stop'
    KILL_ALL_PROCESS_NAME= 'palpao_kill_all'
    MIRROR_CONTROLLER_1_PROCESS_NAME= 'palpao_mirror_controller_1'
    MIRROR_CONTROLLER_2_PROCESS_NAME= 'palpao_mirror_controller_2'
