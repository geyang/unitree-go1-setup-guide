network:
	python jetson_deploy/utils/network_config_unitree.py
low_level:
	cd unitree_legged_sdk/build && ./lcm_position lowlevel
