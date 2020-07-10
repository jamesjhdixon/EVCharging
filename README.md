# EVCharging
Produces credible EV charging schedules from car journey data according to two models for driver behaviour. 

Inputs:
<ul>
  <li>Trip data (a series of trips made by a set of vehicles, including information on their origins, destinations, distances and times.</li>
  <li>Car spec (battery size (kWh), consumption (city/combi/highway) (kWh/km))</li>
  <li>Charger power (kW - home, work, public)</li>
  <li>Charging access (home, work and public)</li>
  <li>Charging behaviour model ('minimal' - in which drivers seek the minimum possible number of plug-ins - or 'routine' - in which drivers will always plug-in on arrival at home)</li>
</ul>

For details on the model, see https://www.sciencedirect.com/science/article/pii/S0306261919317775.

Case studies where this model has been used:
https://www.sciencedirect.com/science/article/pii/S2590116820300163
https://strathprints.strath.ac.uk/73065/

# Getting Started
Example trip data is provided as TripData.csv. Any trip data can be read, so long as the column headers match. These example data are anonymised entries from the UK National Travel Survey (https://beta.ukdataservice.ac.uk/datacatalogue/studies/study?id=5340).

Clone repository and save in a single directory. Execute run.py to generate charging schedules from travel diaries.

# Author
This was developed by James Dixon at the University of Strathclyde, Glasgow, 2019-2020.

# Citation
J. Dixon, P.B. Andersen, K. Bell, C. Træholt, On the ease of being green: An investigation of the inconvenience of electric vehicle charging. Applied Energy,
Volume 258, 2020. https://doi.org/10.1016/j.apenergy.2019.114090.
