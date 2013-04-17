#!/usr/bin/env python

from LSSTObject import *
from utilities import *
from AstronomicalSky import *

class SchedulingData (LSSTObject):

    def __init__ (self,
                  configFile,
		  surveyStartTime,
		  surveyEndTime,
		  astroSky,
		  lsstDB,
		  sessionID):

	self.sky = astroSky
	self.lsstDB = lsstDB
	self.sessionID = sessionID

        config, pairs = readConfFile(configFile)

	self.lookAheadNights = int(eval(str(config['lookAheadNights'])))
	self.dt = int(eval(str(config['lookAheadInterval'])))

	self.initSurvey(surveyStartTime, surveyEndTime)

	return


    def initSurvey (self, startTime, endTime):

        # Align time to NightTime
        t = startTime
        # sunRise < sunSet
        # This is what is happening:
        #  <---------------DAY------------------->
        # --------|----------------------|-------------->
        #      sunRise                 sunSet          t
	x = self.sky.getIntTwilightSunriseSunset (t)
        (sunRise,sunSet,sunRiseMJD,sunSetMJD, sunRiseTwil,sunSetTwil) = x
	#print sunRiseTwil
	#print sunRise
	#print sunSet
	#print sunSetTwil

	if (t < sunRise):
            #  <---------------DAY------------------->
            # --*-----|----------------------|-------------->
            #   t  sunRise                 sunSet         t

            ## LD: need to check if we're before previous day's sunset.
            #  <---------------DAY------------------->
            # --*-----|----------------------|------------->
            #   t  sunSet                  sunRise        t
            x = self.sky.getIntTwilightSunriseSunset(t - DAY)
            (yesterday_sunRise, yesterday_sunSet, yesterday_sunRiseMJD, yesterday_sunSetMJD, yesterday_sunRiseTwil, yesterday_sunSetTwil) = x
            #print yesterday_sunRiseTwil
            #print yesterday_sunRise
            #print yesterday_sunSet
            #print yesterday_sunSetTwil

            if t < yesterday_sunSet:
                t = yesterday_sunSet

	    tonight_sunSetMJD   = yesterday_sunSetMJD
            tonight_sunSet      = yesterday_sunSet
            tonight_sunSetTwil  = yesterday_sunSetTwil
	    tonight_sunRiseTwil = sunRiseTwil
	    tonight_sunRise     = sunRise

        elif (sunRise <= t < sunSet):    # Middle of the day
            #  <---------------DAY------------------->
            # -----|-------*--------------|-------------->
            #   sunRise    t            sunSet          t
            x = self.sky.getIntTwilightSunriseSunset (t + DAY)
            (tomorrow_sunRise, tomorrow_sunSet, tomorrow_sunRiseMJD, tomorrow_sunSetMJD, tomorrow_sunRiseTwil, tomorrow_sunSetTwil) = x
            #print tomorrow_sunRiseTwil
            #print tomorrow_sunRise
            #print tomorrow_sunSet
            #print tomorrow_sunSetTwil

            t = sunSet

	    tonight_sunSetMJD   = sunSetMJD
            tonight_sunSet      = sunSet
            tonight_sunSetTwil  = sunSetTwil
            tonight_sunRiseTwil = tomorrow_sunRiseTwil
            tonight_sunRise     = tomorrow_sunRise

        elif (t >= sunSet):                 # Next night
            #  <---------------DAY------------------->
            # --------|----------------------|-----*-------->
            #      sunRise                 sunSet  t       t

	    x = self.sky.getIntTwilightSunriseSunset (t + DAY)
            (tomorrow_sunRise, tomorrow_sunSet, tomorrow_sunRiseMJD, tomorrow_sunSetMJD, tomorrow_sunRiseTwil, tomorrow_sunSetTwil) = x

            tonight_sunSetMJD   = sunSetMJD
            tonight_sunSet      = sunSet
            tonight_sunSetTwil  = sunSetTwil
            tonight_sunRiseTwil = tomorrow_sunRiseTwil
            tonight_sunRise     = tomorrow_sunRise


        midnight = (int(tonight_sunSetTwil + tonight_sunRiseTwil)/2)

	#print t
	#print tonight_sunSet
	#print tonight_sunSetTwil
	#print tonight_sunRiseTwil
	#print tonight_sunRise

	self.lookAhead_nights = []
	self.lookAhead_times  = {}

        self.sunSetMJD   = {}
        self.sunSet      = {}
        self.sunSetTwil  = {}
        self.midnight    = {}
        self.sunRiseTwil = {}
        self.sunRise     = {}

	self.dictOfActiveFields = {}

        self.dateProfile = {}
        self.moonProfile = {}
        self.twilightProfile = {}
	self.computedNights = {}
        self.alt = {}
        self.az = {}
        self.airmass = {}
        self.brightness = {}
	self.dist2moon = {}
        self.visible = {}
        self.filters = {}
        self.proposals = {}

	#self.initMoonPhase(midnight)

        self.startTime = int(t)
        self.endTime   = int(endTime)
        self.currentTime = self.startTime

	night = 0
	self.currentNight           = night
        self.sunSetMJD[night]       = tonight_sunSetMJD
        self.sunSet[night]          = tonight_sunSet
        self.sunSetTwil[night]      = tonight_sunSetTwil
        self.midnight[night]        = midnight
        self.sunRiseTwil[night]     = tonight_sunRiseTwil
        self.sunRise[night]         = tonight_sunRise
        self.moonProfile[night]     = self.sky.computeMoonProfile(midnight)
	self.twilightProfile[night] = self.sky.computeTwilightProfile(t)

        self.lookAhead_nights       = [night]
	self.lookAhead_times[night] = range(self.startTime, self.sunRise[night], self.dt)
	for date in self.lookAhead_times[night]:
	    self.dateProfile[date] = self.sky.computeDateProfile(date)

	self.updateLookAheadWindow()

    def updateLookAheadWindow(self):

	lastnight = self.lookAhead_nights[-1]
        nightsToAdd = 2*self.lookAheadNights - (lastnight - self.currentNight)

	self.lookAheadLastNight = lastnight + nightsToAdd

        night = lastnight
        t = self.midnight[night]
        x = self.sky.getIntTwilightSunriseSunset(t)
        print x
        (sunRise,sunSet,sunRiseMJD,sunSetMJD,sunRiseTwil,sunSetTwil) = x
	last_sunSetMJD  = sunSetMJD
	last_sunSet     = sunSet
	last_sunSetTwil = sunSetTwil
	while ( (t < self.endTime) and (night < self.lookAheadLastNight) ):
	    night += 1
            t += DAY
	    x = self.sky.getIntTwilightSunriseSunset(t)
	    (sunRise,sunSet,sunRiseMJD,sunSetMJD,sunRiseTwil,sunSetTwil) = x
	    midnight = int((last_sunSetTwil+sunRiseTwil)/2)

	    self.sunSetMJD[night]       = last_sunSetMJD
	    self.sunSet[night]          = last_sunSet
	    self.sunSetTwil[night]      = last_sunSetTwil
	    self.midnight[night]        = midnight
	    self.sunRiseTwil[night]     = sunRiseTwil
	    self.sunRise[night]         = sunRise
	    self.moonProfile[night]     = self.sky.computeMoonProfile(midnight)
	    self.twilightProfile[night] = self.sky.computeTwilightProfile(t)

	    self.lookAhead_nights   += [night]
	    self.lookAhead_times[night] = range(self.sunSet[night], self.sunRise[night], self.dt)
	    for date in self.lookAhead_times[night]:
		self.dateProfile[date] = self.sky.computeDateProfile(date)

	    last_sunSetMJD  = sunSetMJD
	    last_sunSet     = sunSet
	    last_sunSetTwil = sunSetTwil

        self.computeTargetData(self.currentNight, {}, 0)

	for n in range(self.lookAhead_nights[0], self.currentNight):
	    del self.sunSetMJD[n]
            del self.sunSet[n]
            del self.sunSetTwil[n]
            del self.midnight[n]
            del self.sunRiseTwil[n]
            del self.sunRise[n]
            del self.moonProfile[n]
            del self.twilightProfile[n]

	    for t in self.lookAhead_times[n]:
	        del self.dateProfile[t]
	    del self.lookAhead_times[n]
	    self.lookAhead_nights.remove(n)

	return


    def findNightAndTime(self, time):
	n = self.lookAhead_nights[0]
	foundNight = False
	while (n<= self.lookAhead_nights[-1] and not foundNight):
	    if (time < self.sunSet[n]):
		t = self.sunSet[n]
		foundNight = True
	    elif (self.sunSet[n] <= time <= self.sunRise[n]):
		t = time
		foundNight = True
	    else:
	        n += 1
	if foundNight:
	    ix = 0
	    foundTime = False
	    while (ix < len(self.lookAhead_times[n]) and not foundTime):
		if (t > self.lookAhead_times[n][ix]):
		    ix += 1
		elif (ix == 0):
		    next_time = self.lookAhead_times[n][ix]
		    foundTime = True
		elif ( (t-self.lookAhead_times[n][ix-1]) < (self.lookAhead_times[n][ix]-t) ):
		    next_time = self.lookAhead_times[n][ix-1]
		    foundTime = True
		else:
                    next_time = self.lookAhead_times[n][ix]
		    foundTime = True
	    if not foundTime:
		next_time = self.lookAhead_times[n][-1]
	    return (n, next_time)
	else:
	    return None


    def updateTargets(self, dictOfNewFields, propID, dateProfile):

	(date,mjd,lst_RAD) = dateProfile

	(nextNight, nextTime) = self.findNightAndTime(date)
	print ("nextNight=%i nextTime=%i" % (nextNight, nextTime))
        self.currentNight = nextNight
        self.currentTime  = nextTime
	if ( (self.lookAhead_nights[-1] - self.currentNight) < self.lookAheadNights):
	    self.updateLookAheadWindow()

	self.computeTargetData(nextNight, dictOfNewFields, propID)

	return

    def computeTargetData(self, initNight, dictOfNewFields, propID):

	listOfNewFields = sorted(dictOfNewFields.iterkeys())
	listOfActiveFields = sorted(self.dictOfActiveFields.iterkeys())
	newfields = 0
	newprops  = 0
	for field in listOfNewFields:
	    if field not in listOfActiveFields:
		self.dictOfActiveFields[field] = dictOfNewFields[field]

		self.computedNights[field] = []
		self.alt[field] = {}
		self.az[field] = {}
		self.airmass[field] = {}
		self.brightness[field] = {}
		self.dist2moon[field] = {}
		self.visible[field] = {}
		self.filters[field] = {}

                self.proposals[field] = [propID]
                #print ("new field=%4i new propID=%i" % (field, propID))
                self.lsstDB.addProposalField(self.sessionID, propID, field)
		newfields += 1
            else:
                if propID not in self.proposals[field]:
                    self.proposals[field].append(propID)
                    #print ("    field=%4i new propID=%i" % (field, propID))
                    self.lsstDB.addProposalField(self.sessionID, propID, field)
		    newprops += 1

	print ("SchedulingData:: %4i new fields from propID=%4i" % (newfields, propID))
	print ("SchedulingData:: %4i existing fields registered for propID=%4i" % (newprops, propID))

        print initNight
        listOfActiveFields = sorted(self.dictOfActiveFields.iterkeys())
	print self.lookAhead_nights
        for n in self.lookAhead_nights:
	    #print n
	    #print self.lookAhead_times[n][0:3]
	    computed = 0
	    removed  = 0
	    for field in listOfActiveFields:
		#print self.computedNights[field]
		if (n >= initNight):
		    if n not in self.computedNights[field]:
			(ra, dec) = self.dictOfActiveFields[field]
                    	for t in self.lookAhead_times[n]:
                            (am, alt, az) = self.sky.airmasst(t, ra, dec)
                            self.alt[field][t] = alt
                            self.az[field][t] = az
                            self.airmass[field][t] = am
                            (br, dist2moon, moonAlt, brprofile) = \
				self.sky.getSkyBrightness(0, ra, dec, alt,
                                		self.dateProfile[t],
                                            	self.moonProfile[n],
                                            	self.twilightProfile[n])
                            self.brightness[field][t] = br
			    self.dist2moon[field][t] = dist2moon
                        self.computedNights[field].append(n)
                        computed += 1
		else:
                    if n in self.computedNights[field]:
                        for t in self.lookAhead_times[n]:
                            del self.alt[field][t]
                            del self.az[field][t]
                            del self.airmass[field][t]
                            del self.brightness[field][t]
			    del self.dist2moon[field][t]
                        self.computedNights[field].remove(n)
                        removed += 1

	    if (computed > 0):
		print ("SchedulingData:: night %i computed %4i fields" % (n, computed))
	    if (removed > 0):
		print ("SchedulingData:: night %i removed %4i fields" % (n, removed))

	return

if (__name__ == '__main__'):

    longitude =  -70.815
    latitude =  -30.16527778
    height =  2215.
    simEpoch =  49353.
    pressure =  1010.
    temperature =  12.
    relativeHumidity =  0.
 
    obsProfile = (longitude *DEG2RAD, latitude *DEG2RAD, height, simEpoch,pressure,temperature,relativeHumidity)

    sky = AstronomicalSky(None, obsProfile, 0, 0, None, "../conf/system/AstronomicalSky.conf", False, './AstronomicalSky.log', 0)

    data = SchedulingData('../test/SchedulingData.conf', 0, 432000, sky)

    sys.exit(0)

