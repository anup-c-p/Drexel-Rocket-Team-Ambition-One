import synnax as sy
import time 
import random as r 


client = sy.Synnax(
    host="demo.synnaxlabs.com",
    port=9090,
    username="synnax",
    password="seldon",
    secure=True,
)


sim_time = client.channels.create(
    name="sim_time",
    data_type=sy.DataType.TIMESTAMP,
    is_index=True,
    retrieve_if_name_exists=True,
)

# VALVES

client.channels.create(
    name="fuel_valve",
    data_type=sy.DataType.UINT8,
    index=sim_time.key,
    retrieve_if_name_exists=True,
)

client.channels.create(
    name="nox_valve",
    data_type=sy.DataType.UINT8,
    index=sim_time.key,
    retrieve_if_name_exists=True,
)

client.channels.create(
    name="gse_co2",
    data_type=sy.DataType.UINT8,
    index=sim_time.key,
    retrieve_if_name_exists=True,
)

client.channels.create(
    name="gse_nox",
    data_type=sy.DataType.UINT8,
    index=sim_time.key,
    retrieve_if_name_exists=True,
)

# SENSORS

client.channels.create(
    name="nox_pressure",
    data_type=sy.DataType.FLOAT32,
    index=sim_time.key,
    retrieve_if_name_exists=True,
)

client.channels.create(
    name="chamber_pressure",
    data_type=sy.DataType.FLOAT32,
    index=sim_time.key,
    retrieve_if_name_exists=True,
)

client.channels.create(
    name="Fuel_Pressure",
    data_type=sy.DataType.FLOAT32,
    index=sim_time.key,
    retrieve_if_name_exists=True,
)

client.channels.create(
    name="Force",
    data_type=sy.DataType.FLOAT32,
    index=sim_time.key,
    retrieve_if_name_exists=True
)

print("Success")