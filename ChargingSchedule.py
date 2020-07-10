# Script-ised version of 'On the Ease of Being Green' heuristic
# input a travel diary, return a charging schedule

import pickle
import pandas as pd
import numpy as np
from scipy import optimize

pd.options.mode.chained_assignment = None

np.warnings.filterwarnings('ignore')

SoCLimit = 0.8

# objective function - integral of charge curve - CV region
def objective(x):
    l, dt = x  # l is lambda, the decay constant. dt is t_infty - t1.

    return Pdc * (np.exp(-dt * l) - 1) + 60 * (1 - SoCLimit) * bsize * l


def func(x):
    l, dt = x

    f = Pdc * np.exp(-l * dt) - 0.001 * Pdc

    return -1 * f


cons = [{'type': 'ineq', 'fun': objective}, {'type': 'ineq', 'fun': func}]  # objective > 0
bnds = ((0, None), (0, None))
x0 = [0.2, 30]


def initial_SoC(minSoC):
    LocSoC = 0

    while LocSoC < minSoC:
        # Beta distribution parameters
        a = 2
        b = 2

        # Sample from beta distribution
        LocSoC = np.random.beta(a, b)

    return LocSoC


def get_Consumption(journeytype, consumption_city, consumption_combi, consumption_hwy):
    if journeytype == 'city':
        consumption = consumption_city
    elif journeytype == 'combined':
        consumption = consumption_combi
    else:
        consumption = consumption_hwy

    return consumption


def get_ChargeType(Location):
    if Location == 'Home':
        ChargeType = 'home'
    elif Location == 'Work' or Location == 'Education':
        ChargeType = 'work'
    elif Location == 'Food shopping' or Location == 'Non food shopping' or Location == 'Personal business medical' or Location == 'Personal business eat/drink' or Location == 'Personal business other' or Location == 'Eat/drink with friends' or Location == 'Other social' or Location == 'Entertain/ public activity' or Location == 'Sport: participate' or Location == 'Day trip/just walk':
        ChargeType = 'destination'
    elif Location == 'In course of work' or Location == 'Escort home' or Location == 'Escort work' or Location == 'Escort in course of work' or Location == 'Escort education' or Location == 'Escort shopping/personal' or Location == 'Other escort':
        ChargeType = 'none'
    else:
        ChargeType = 'none'

    return ChargeType


def get_ChargingOpp(ChargeType, HomeChargeAccess, WorkChargeAccess, PubChargeAccess):
    if (ChargeType == 'home' and HomeChargeAccess == True) or (ChargeType == 'work' and WorkChargeAccess == True) or (
            ChargeType == 'destination' and PubChargeAccess == True):
        return True
    else:
        return False


def get_Pmax(ChargeType, PowerScenario):
    if ChargeType == 'home':
        if PowerScenario == 'low':
            ChargePower = 3.7
        else:
            ChargePower = 7.4
    elif ChargeType == 'work' or ChargeType == 'destination':
        if PowerScenario == 'low':
            ChargePower = 11
        else:
            ChargePower = 22
    else:
        ChargePower = 0

    return ChargePower


def get_Pdc(bsize, PowerScenario):
    if PowerScenario == 'low':
        if bsize < 60:
            Pdc = 50
        else:
            Pdc = 120
    else:
        if bsize < 60:
            Pdc = 150
        else:
            Pdc = 350

    return Pdc


def RapidCharge(TripID, VehicleID, TripStart, TripEnergy, Capacity, Pmax, TotalRemainingEnergy, SoCPrev, min_SoC):
    if TripEnergy < 0.001:
        TripEnergy = 0.001

    ChargeType = 'Rapid Enroute'

    t0 = TripStart

    if TripEnergy >= (SoCPrev - min_SoC) * Capacity:
        ncharge = int(np.ceil((TripEnergy - (SoCPrev - min_SoC) * Capacity) / ((SoCLimit - min_SoC) * Capacity)))
    else:
        ncharge = 0

    # change in energy
    if ncharge >= 1:
        dE = min(ncharge * (SoCLimit - min_SoC) * Capacity, TotalRemainingEnergy - (SoCPrev - min_SoC) * Capacity)
    else:
        dE = 0

    t1 = t0 + 60 * dE / Pmax
    t2 = t1

    SoCEnd = SoCPrev - TripEnergy / Capacity + dE / Capacity

    Loc = ChargeType  # rapid enroute charging not assigned a location

    RapidChargeEvent = pd.DataFrame({'TripID': [TripID], 'VehicleID': [VehicleID],
                                     'ChargeType': [ChargeType], 'Location': [Loc], 'BatteryCapacity': [Capacity],
                                     'SoCStart': [minSoC],
                                     'SoCEnd': [SoCEnd], 'dE': [dE], 'Pmax': [Pmax], 't0': [t0],
                                     't1': [t1], 't2': [t2], 't_inf': [t2]})

    return RapidChargeEvent, ncharge


def ChargeWhileParked(TripID, VehicleID, capacity, ChargeType, powerscenario, SoC_init, t0, t2):
    Pmax = get_Pmax(ChargeType, powerscenario)

    if SoC_init < minSoC:
        SoC_init = minSoC

    global Pdc
    eff = 0.88
    Pdc = eff * Pmax

    sol = optimize.minimize(objective, x0, bounds=bnds, constraints=cons)  # numerically solve for lambda
    lbd, dt = list(sol.x)

    # define what kind of parked charging event it is - CC, CC-CV, CV
    if SoC_init < SoCLimit:  # before it gets to 80%
        t1 = t0 + 60 * capacity * (SoCLimit - SoC_init) / Pdc  # whe nthe car would theoretically reach the CV region

        t_infty = t1 + dt

        if t2 > t1:  # (CC then CV)
            dE = (1 / 60) * (Pdc * (t1 - t0) + (Pdc / lbd) * (1 - np.exp(-lbd * (t_infty - t1))))
            SoC_new = (SoC_init * capacity + dE) / capacity
            if SoC_new > 1:
                SoC_new = 1
                dE = (SoC_new - SoC_init) * capacity
        else:  # (CC only)
            dE = 1 / 60 * Pdc * (t2 - t0)
            SoC_new = (SoC_init * capacity + dE) / capacity

    else:
        # establish t0, t1 and t2
        t1 = t0 + 60 * capacity * (SoCLimit - SoC_init) / Pdc  # in this case, this will be in the PAST

        t_infty = t1 + dt

        # 2.Update the car's SoC
        # CV only charging
        dE = (1 / 60) * (Pdc / lbd) * (np.exp(-lbd * (t0 - t1)) - np.exp(-lbd * (t_infty - t1)))
        SoC_new = (SoC_init * capacity + dE) / capacity
        if SoC_new > 1:
            SoC_new = 1
            dE = (SoC_new - SoC_init) * capacity  # *****ADDITION

    if ChargeType == 'home':
        Loc = 'h'
    else:
        Loc = ChargeType

    ChargeEvent = pd.DataFrame({'TripID': [TripID], 'VehicleID': [VehicleID],
                                'ChargeType': [ChargeType], 'Location': [Loc], 'BatteryCapacity': [capacity],
                                'SoCStart': [SoC_init],
                                'SoCEnd': [SoC_new], 'dE': [dE], 'Pmax': [Pmax], 't0': [t0],
                                't1': [t1], 't2': [t2], 'lbd': [lbd], 't_inf': [t_infty]})

    return ChargeEvent


def set_SoCs(df, SoC_init, bsize):
    for i in list(df.index.values):
        if i == df.index[0]:
            df.at[i, 'SoC'] = SoC_init - df.TE[i] / bsize + df.dE_Parked[i] / bsize + df.dE_Enroute[i] / bsize
        else:
            df.at[i, 'SoC'] = df.SoC[i - 1] - df.TE[i] / bsize + df.dE_Parked[i] / bsize + df.dE_Enroute[i] / bsize

    return df


def set_Zs(df, SoC_init, bsize):
    for i in list(df.index.values):
        if i == df.index[0]:
            df.at[i, 'Z'] = SoC_init - df.TE[i] / bsize
        else:
            df.at[i, 'Z'] = df.SoC[i - 1] - df.TE[i] / bsize

    return df


def ChargingSchedule(TravelDiary, CarSpec, ChargingPower, HomeCharge, WorkCharge, PubCharge, ChargeBehaviour, min_range):
    ChargeEvents = pd.DataFrame \
        (columns=['TripID', 'VehicleID', 'ChargeType', 'SoCStart', 'SoCEnd', 'dE', 'Pmax', 't0', 't1', 't2'])

    global bsize
    bsize, consumption_city, consumption_combi, consumption_hwy = CarSpec

    TravelDiary = TravelDiary.reset_index(drop=True)

    # calculate the minimum SoC for this vehicle
    global minSoC
    minSoC = min_range * consumption_combi / bsize  # note that COMBINATION consumption value is used to calculate min SoC

    # establish start SoC
    StartSoC = initial_SoC(minSoC)

    # make new column for Trip Energy consumption
    TravelDiary['TE'] = TravelDiary.apply(lambda row: row['Trip_km'] * get_Consumption(row['Journey_Type'], consumption_city, consumption_combi, consumption_hwy), axis=1)

    # make a new column for the parking duration (and hence opportunitiy to charge)
    TravelDiary['PD'] = TravelDiary.Trip_Start.shift(-1) - TravelDiary.Trip_End

    # make a clumn for the charge tyep (home/work/destiantion)
    TravelDiary['ChargeType'] = TravelDiary.apply(lambda row: get_ChargeType(row['Trip_Destination']), axis=1)

    # make a column for the Pmax
    TravelDiary['Pmax'] = TravelDiary.apply(lambda row: get_Pmax(row['ChargeType'], ChargingPower), axis=1)

    # make a column for whether it represents a charging opportunity
    TravelDiary['ChargingOpp'] = TravelDiary.apply(
        lambda row: get_ChargingOpp(row['ChargeType'], HomeCharge, WorkCharge, PubCharge),
        axis=1)
    TravelDiary.loc[len(TravelDiary) - 1, 'ChargingOpp'] = False

    TravelDiary['ChargeParked'] = False
    TravelDiary['ChargeEnRoute'] = int(0)

    TravelDiary['dE_Parked'] = float(0)
    TravelDiary['dE_Enroute'] = float(0)

    TravelDiary = set_SoCs(TravelDiary, StartSoC, bsize)
    TravelDiary = set_Zs(TravelDiary, StartSoC, bsize)

    """
    Finished initialisation of travel diary
    """

    # add some home charging events --> routine charging

    if ChargeBehaviour.lower() == 'routine':

        home_k = TravelDiary[(TravelDiary.ChargingOpp == True) & (TravelDiary.ChargeType == 'home')].index.tolist()

        for hk in home_k:
            # enact a charging event at hk
            ChargeEvent = ChargeWhileParked(TravelDiary.TripID[hk], TravelDiary.VehicleID[hk], bsize,
                                            TravelDiary.ChargeType[hk], ChargingPower, TravelDiary.SoC[hk],
                                            TravelDiary.Trip_End[hk], TravelDiary.Trip_Start[hk + 1])

            ChargeEvents = ChargeEvents.append(ChargeEvent, sort=False)

            TravelDiary.at[hk, 'SoC'] = ChargeEvent.SoCEnd.item()
            TravelDiary.at[hk + 1:] = set_SoCs(TravelDiary[TravelDiary.index > hk], ChargeEvent.SoCEnd.item(), bsize)
            TravelDiary.at[hk, 'Z'] = ChargeEvent.SoCEnd.item()
            TravelDiary.at[hk + 1:] = set_Zs(TravelDiary[TravelDiary.index > hk], ChargeEvent.SoCEnd.item(), bsize)

            TravelDiary.at[hk, 'ChargeParked'] = True
            TravelDiary.at[hk, 'dE_Parked'] = ChargeEvent.dE.item()

    if TravelDiary.SoC.min() < minSoC:
        # define set K as the set of possible parked charging events in the travel diary
        K = TravelDiary[TravelDiary.ChargingOpp == True].index.tolist()

        if ChargeBehaviour.lower() == 'routine':
            K = [k for k in K if k not in home_k]

        if K:

            # for each trip i in the TravelDiary

            for i in list(TravelDiary.index.values):

                # Initialise flag variable Q
                Q = TravelDiary.SoC[i]

                # evaluate whether it is less thant the minimum
                while TravelDiary.SoC[i] < minSoC:

                    # Initialise set of possible SoC values S

                    Sset = []

                    for k in [k for k in K if k < i]:  # for each parked charging opportunity before trip i

                        # evaluate the potential SoC increase and effect on SoC[i]

                        PotentialChargeEvent = ChargeWhileParked(TravelDiary.TripID[k], TravelDiary.VehicleID[k], bsize,
                                                                 TravelDiary.ChargeType[k],
                                                                 ChargingPower, TravelDiary.SoC[k],
                                                                 TravelDiary.Trip_End[k],
                                                                 TravelDiary.Trip_Start[k + 1])

                        aftercharge_TravelDiary = TravelDiary[TravelDiary.index >= k]
                        aftercharge_TravelDiary.at[k, 'ChargeParked'] = True
                        aftercharge_TravelDiary.at[k, 'dE_Parked'] = PotentialChargeEvent.dE.item()
                        aftercharge_TravelDiary.at[k, 'SoC'] = PotentialChargeEvent.SoCEnd.item()
                        aftercharge_TravelDiary.loc[k + 1:] = set_SoCs(aftercharge_TravelDiary.loc[k + 1:],
                                                                       PotentialChargeEvent.SoCEnd.item(), bsize)

                        # append potential effect on SoC after trip i
                        Sset.append(aftercharge_TravelDiary.SoC[i])

                    if Sset and max(Sset) > Q:
                        # the one to charge at is the kth trip that gives the biggest SoC at trip i -> i.e. max(Sset)
                        c = K[Sset.index(max(Sset))]

                        ChargeEvent = ChargeWhileParked(TravelDiary.TripID[c], TravelDiary.VehicleID[c], bsize,
                                                        TravelDiary.ChargeType[c],
                                                        ChargingPower, TravelDiary.SoC[c], TravelDiary.Trip_End[c],
                                                        TravelDiary.Trip_Start[c + 1])

                        ChargeEvents = ChargeEvents.append(ChargeEvent, sort=False)

                        TravelDiary.at[c, 'SoC'] = ChargeEvent.SoCEnd.item()
                        TravelDiary.at[c + 1:] = set_SoCs(TravelDiary[TravelDiary.index > c], ChargeEvent.SoCEnd.item(),
                                                          bsize)
                        TravelDiary.at[c, 'Z'] = ChargeEvent.SoCEnd.item()
                        TravelDiary.at[c + 1:] = set_Zs(TravelDiary[TravelDiary.index > c], ChargeEvent.SoCEnd.item(),
                                                        bsize)

                        TravelDiary.at[c, 'ChargeParked'] = True
                        TravelDiary.at[c, 'dE_Parked'] = ChargeEvent.dE.item()

                        # remove that possible charging opportunity from K
                        K = [k for k in K if k > c]
                        # K.remove(c)
                        Q = TravelDiary.SoC[i]

                    else:
                        break  # adding any more charge events will not bring an improvement

    """
    Now we will have to resort to en route charging events
    """
    if TravelDiary.SoC.min() < minSoC:

        K = TravelDiary[TravelDiary.ChargingOpp == True].index.tolist()

        for i in list(TravelDiary.index.values):

            if TravelDiary.SoC[i] < minSoC:

                # find the index of the next charging opportunity
                if [k for k in K if k >= i]:
                    o = min([k for k in K if k >= i])
                else:
                    o = TravelDiary.index.tolist()[-1]

                RapidChargeEvent, ncharge = RapidCharge(TravelDiary.TripID[i], TravelDiary.VehicleID[i],
                                                        TravelDiary.Trip_Start[i], TravelDiary.TE[i],
                                                        bsize, get_Pdc(bsize, ChargingPower),
                                                        TravelDiary[i:o + 1].TE.sum(),
                                                        TravelDiary.SoC[i - 1] if i >= 1 else StartSoC, minSoC)

                ChargeEvents = ChargeEvents.append(RapidChargeEvent, sort=False)

                TravelDiary.at[i, 'SoC'] = RapidChargeEvent.SoCEnd.item()
                TravelDiary.at[i + 1:] = set_SoCs(TravelDiary[TravelDiary.index > i], RapidChargeEvent.SoCEnd.item(),
                                                  bsize)
                TravelDiary.at[i + 1:] = set_Zs(TravelDiary[TravelDiary.index > i], RapidChargeEvent.SoCEnd.item(),
                                                bsize)

                TravelDiary.at[i, 'ChargeEnRoute'] = ncharge
                TravelDiary.at[i, 'dE_Enroute'] = RapidChargeEvent.dE.item()

    ChargeEvents = ChargeEvents.reset_index(drop=True)

    return ChargeEvents, TravelDiary


print('done')