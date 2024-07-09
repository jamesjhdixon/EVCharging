# EVCharging
Produces **credible** EV charging schedules from car journey data according to two models for driver behaviour.

![image](https://github.com/jamesjhdixon/EVCharging/assets/36702681/920954dd-78f8-4e64-ac2d-e4a00e691e87)
*Comparison of average charging frequency (events per day) against vehicle battery size for Electric Nation trial data and results from this model (for 'minimal charging'). Taken from: https://doi.org/10.1016/j.renene.2020.07.017*

Inputs:
<ul>
  <li>Trip data (a series of trips made by a set of vehicles, including information on their origins, destinations, distances and times.</li>
  <li>Car spec (battery size (kWh), consumption (city/combi/highway) (kWh/km))</li>
  <li>Charger power (kW - home, work, public)</li>
  <li>Charging access (home, work and public)</li>
  <li>Charging behaviour model ('minimal' - in which drivers seek the minimum possible number of plug-ins - or 'routine' - in which drivers will always plug-in on arrival at home)</li>
</ul>

For details on the model, see https://doi.org/10.1016/j.apenergy.2019.114090.

# Getting started: trip data
Example trip data is provided as TripData.csv. **Any trip data can be read**, so long as the column headers match. These example data are anonymised entries from the UK National Travel Survey (https://beta.ukdataservice.ac.uk/datacatalogue/studies/study?id=5340).

Clone repository and save in a single directory. Execute run.py to generate charging schedules from travel diaries.

# 'Pre-made' EV charge events
If you don't have access to the travel data, there are two spread csv files provided with the output of the model for the trip data of 10,000 cars (from the UK National Travel Survey). The trip data itself is not published (not public access) but the charge events are there. All vehicles in this analysis had access to charging at home only at 7.4 kW and were of a variety of battery sizes (24-100 kWh).

A key to the columns of the output:
<ul>
<li>TripID: unique trip identifier</li>
<li>VehicleID: unique vehicle identifier</li>
<li>ChargeType: e.g. 'home', 'rapid enroute'</li>
<li>SoCStart: state of charge at start of charge event</li>
<li>SoCEnd: state of charge at start of charge event</li>
<li>dE: change in energy (kWh)</li>
<li>Pmax: max rated charger power (kW, AC)</li>
<li>BatteryCapacity: battery capacity of vehicle (kWh)</li>
<li>t0: plug-in time, minutes past 00:00 on Monday (i.e. ranges from 0-10080, the number of minutes in a week)</li>
<li>t1: time at which (if the vehicle is charging uncontrolled) the vehicle reaches 80% SoC and hence moves from constant current (CC) to constant voltage (CV) charging. Also in minutes past 00:00 on Monday</li>
<li>t2: plug-out time, time at which the vehicle commences its next journey</li>
<li>t_inf: time at which (if the vehicle is charging uncontrolled) the vehicle reaches ~100% SoC and stops charging</li>
<li>Location: h = home, rapid enroute = …</li>
<li>lbd: decay constant (lambda) for charging in the CV region</li>
</ul>

# Author
This was developed by James Dixon at the University of Strathclyde, Glasgow, 2019-2020.

# Citation
J. Dixon, K. Bell. (2020) Electric vehicles: Battery capacity, charger power, access to charging and the impacts on distribution networks. eTransportation, volume 4, https://doi.org/10.1016/j.etran.2020.100059
