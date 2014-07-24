class Options(object):
    
    def __init__(self, title="REDPy Catalog", filename="redtable.h5", groupName="hsr",
        groupDesc="MSH: HSR-EHZ-UW Default", station="HSR", channel="EHZ", network="UW",
        location="--", samprate=100.0, lwin=7.0, swin=0.8, trigon=3.0, trigoff=2.0,
        mintrig=10.0, winlen=512, ptrig=10.0, atrig=20.0, fmin=1.0, fmax=10.0):
        
		"""
		Defines the settings that are often passed to routines and that define the table.
		These are also written to the attributes of the table for posterity.
	
		TABLE DEFINITIONS:
		title: Name of the table (default "REDPy Catalog")
		filename: Filename for the table (default "redtable.h5")
		groupName: Short string describing the name of the station (default "hsr")
		groupDesc: Longer string describing the run (default "MSH: HSR-EHZ-UW Default")
	
		STATION PARAMETERS:
		station: String of station name (default "HSR")
		channel: String of channel of interest, no wildcards supported yet (default "EHZ")
		network: String of network code (default "UW")
		location: String of location code (default "--")
		samprate: Sampling rate of that station (default 100.0 Hz)
		
		TRIGGERING PARAMETERS:
		lwin: Length of long window for STALTA (default 7.0 s)
		swin: Length of short window for STALTA (default 0.8 s)
		trigon: Cutoff ratio for triggering STALTA (default 3.0)
		trigoff: Cutoff ratio for ending STALTA trigger (default 2.0)
		mintrig: Minimum spacing between triggers (default 10.0 s)
	
		WINDOWING PARAMETERS:
		winlen: Length of window for cross-correlation (default 512 samples, power of 2 best)
		ptrig: Length of time cut prior to trigger (default 10.0 s)
		atrig: Length of time cut after trigger (default 20.0 s)
	
		FILTERING PARAMETERS:
		fmin: Lower band for bandpass filter (default 1.0 Hz)
		fmax: Upper band for bandpass filter (default 10.0 Hz) 
	
		I envision that these could eventually be set interactively or by control file.
		This list will likely expand.	   
		"""
		
		self.title = title
		self.filename = filename
		self.groupName = groupName
		self.groupDesc = groupDesc
		self.station = station
		self.channel = channel
		self.network = network
		self.location = location
		self.samprate = samprate
		self.lwin = lwin
		self.swin = swin
		self.trigon = trigon
		self.trigoff = trigoff
		self.mintrig = mintrig
		self.winlen = 512         # NOTE: These are all currently hardcoded until we
		self.ptrig = 10.0         # figure out how to not have redpy.table.Trigger and
		self.atrig = 20.0         # redpy.table.Correlation not hardcoded
		self.fmin = fmin
		self.fmax = fmax
		