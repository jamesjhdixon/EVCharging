from ChargingSchedule_ExampleData import *
import numpy as np
import pandas as pd


#Load travel data - all vehicles
TravelData = pd.read_csv('TripData.csv')

#choose vehicle - must be present in VehicleID
veh = 'Canyonero'

#Return trips made only by that vehicle
TravelDiary = TravelData[TravelData.VehicleID == veh]

#Specify car spec - battery size (kWh), consumption - city (kWh/km), consumption - combination (kWh/km), consumption - highway (kWh/km)
CarSpec = (30, 0.17, 0.19, 0.18)

#Specify charging power.
#'low' = 3.7 kW at home, 11 kW at work/public, 50 kW en route for batteries< 60 kWh, 120 kW for batteries >= 60 kWh
# 'low' = 7.4 kW at home, 22 kW at work/public, 150 kW en route for batteries< 60 kWh, 350 kW for batteries >= 60 kWh
ChargingPower = 'high'

#Specify home, work and public charging access
HomeCharge, WorkCharge, PubCharge = True, True, False

#Specify charging behaviour.
#Minimal = minimise number of charge events, deferring until last possible moment --> finish travel diary with max possible SoC
#Routine = plug in upon every arrival at home (if HomeCharge == True). Minimise other charge events
ChargeBehaviour = 'Minimal'

#minimum allowed range (km)
min_range = 25

ChargeEvents, Trips = ChargingSchedule(TravelDiary, CarSpec, ChargingPower, HomeCharge, WorkCharge, PubCharge,
                      ChargeBehaviour, min_range)

print('Charging schedule:')
print(ChargeEvents)
