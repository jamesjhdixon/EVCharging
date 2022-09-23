from ChargingSchedule_NTSData import *
import numpy as np
import pandas as pd
import pickle

# Load travel data - all vehicles
NTS_DataDir = f"C:/Users/cenv0795/Data/NTS_TripData/"
f = open(f"{NTS_DataDir}NTSTripData.pckl", "rb")
TravelData = pickle.load(f)
f.close()

SaveDir = f"C:/Users/cenv0795/Data/EVCharging_Schedules/"

# Specify car spec - battery size (kWh), consumption - city (kWh/km), consumption - combination (kWh/km), consumption - highway (kWh/km)
Consumption_dict = {24: (0.17, 0.187, 0.21),
                    30: (0.172, 0.191, 0.21),
                    40: (0.17, 0.19, 0.21),
                    60: (0.23, 0.22, 0.22),
                    75: (0.24, 0.23, 0.23),
                    100: (0.24, 0.23, 0.23)}

# randomly select 10,000 cars
n_cars = 10000
vehicles = np.random.choice(TravelData.VehicleID.unique().tolist(), size=n_cars, replace=False)
ChargeBehaviours = ['Minimal', 'Routine']

for ChargeBehaviour in ChargeBehaviours:

    All_ChargeEvents = pd.DataFrame(columns=['TripID', 'VehicleID', 'ChargeType', 'SoCStart', 'SoCEnd', 'dE',
                                             'Pmax', 't0', 't1', 't2'])

    All_Trips = pd.DataFrame(columns=TravelData.columns)

    veh_count = 0
    for veh in vehicles:

        # Return trips made only by that vehicle
        TravelDiary = TravelData[TravelData.VehicleID == veh]

        BatterySize_kWh = np.random.choice(list(Consumption_dict.keys()))
        Consumption_city, Consumption_combination, Consumption_highway = Consumption_dict[BatterySize_kWh]
        CarSpec = (BatterySize_kWh, Consumption_city, Consumption_combination, Consumption_highway)

        # Specify charging power.
        # 'low' = 3.7 kW at home, 11 kW at work/public, 50 kW en route for batteries< 60 kWh, 120 kW for batteries >= 60 kWh
        # 'low' = 7.4 kW at home, 22 kW at work/public, 150 kW en route for batteries< 60 kWh, 350 kW for batteries >= 60 kWh
        ChargingPower = 'high'

        # Specify home, work and public charging access
        HomeCharge, WorkCharge, PubCharge = True, False, False

        # minimum allowed range (km)
        min_range = 25

        # Specify charging behaviour.
        # Minimal = minimise number of charge events, deferring until last possible moment --> finish travel diary with max possible SoC
        # Routine = plug in upon every arrival at home (if HomeCharge == True). Minimise other charge events

        ChargeEvents, Trips = ChargingSchedule(TravelDiary, CarSpec, ChargingPower, HomeCharge, WorkCharge, PubCharge,
                                               ChargeBehaviour, min_range)

        All_ChargeEvents = All_ChargeEvents.append(ChargeEvents)
        All_Trips = All_Trips.append(Trips)

        veh_count += 1
        print(veh_count)

    All_ChargeEvents = All_ChargeEvents.reset_index()
    All_Trips = All_Trips.reset_index()

    #save as a csv and a pickle
    All_ChargeEvents.to_csv(f"{SaveDir}ChargeEvents_{ChargeBehaviour}_{n_cars}_vehicles.csv", index=False)
    All_Trips.to_csv(f"{SaveDir}TripData_{ChargeBehaviour}_{n_cars}_vehicles.csv", index=False)

    f = open(f"{SaveDir}ChargeEvents_{ChargeBehaviour}_{n_cars}_vehicles.pckl", "wb")
    pickle.dump(All_ChargeEvents, f)
    f.close()

    f = open(f"{SaveDir}TripData_{ChargeBehaviour}_{n_cars}_vehicles.pckl", "wb")
    pickle.dump(All_Trips, f)
    f.close()

    print(f'Charging schedule for: {ChargeBehaviour}')