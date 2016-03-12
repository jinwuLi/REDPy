from obspy import UTCDateTime
import obspy
from obspy.fdsn import Client
from obspy.earthworm import Client as EWClient
from obspy.core.trace import Trace
from obspy.core.stream import Stream
from obspy.signal.trigger import coincidenceTrigger
import numpy as np
from scipy import stats
from scipy.fftpack import fft

def getData(date, opt):

    """
    Download data from IRIS or Earthworm waveserver with padding and filter it.

    date: UTCDateTime of beginning of period of interest
    opt: Options object describing station/run parameters
    
    Returns ObsPy stream objects, one for cutting and the other for triggering
    """    
    
    nets = opt.network.split(',')
    stas = opt.station.split(',')
    locs = opt.location.split(',')
    chas = opt.channel.split(',')
    
    if opt.server == "IRIS":
        client = Client("IRIS")
    else:
        client = EWClient(opt.server, opt.port)
        
    st = Stream()
    for n in range(len(stas)):
        try:
            if opt.server == "IRIS":
                stmp = client.get_waveforms(nets[n], stas[n], locs[n], chas[n],
                    date - opt.atrig, date + opt.nsec + opt.atrig)
            else:
                stmp = client.getWaveform(nets[n], stas[n], locs[n], chas[n],
                    date - opt.atrig, date + opt.nsec + opt.atrig)
            stmp = stmp.filter("bandpass", freqmin=opt.fmin, freqmax=opt.fmax,
                corners=2, zerophase=True)
            stmp = stmp.merge(method=1, fill_value='interpolate')
        except (obspy.fdsn.header.FDSNException):
            try: # try again
                if opt.server == "IRIS":
                    stmp = client.get_waveforms(nets[n], stas[n], locs[n], chas[n],
                        date - opt.atrig, date + opt.nsec + opt.atrig)
                else:
                    stmp = client.getWaveform(nets[n], stas[n], locs[n], chas[n],
                        date - opt.atrig, date + opt.nsec + opt.atrig)
                stmp = stmp.filter("bandpass", freqmin=opt.fmin, freqmax=opt.fmax,
                    corners=2, zerophase=True)
                stmp = stmp.merge(method=1, fill_value='interpolate')
            except (obspy.fdsn.header.FDSNException):
                print('No data found for {0}.{1}'.format(stas[n],nets[n]))
                trtmp = Trace()
                trtmp.stats.sampling_rate = opt.samprate
                trtmp.stats.station = stas[n]
                stmp = Stream().extend([trtmp.copy()])
        # Resample to ensure all traces are same length
        if stmp[0].stats.sampling_rate != opt.samprate:
            stmp = stmp.resample(opt.samprate)
        st.extend(stmp.copy()) 
    
    st = st.trim(starttime=date-opt.atrig, endtime=date+opt.nsec+opt.atrig, pad=True,
        fill_value=0)
    stC = st.copy()
    
    return st, stC


def getCatData(date, opt):

    """
    Download data from IRIS or Earthworm waveserver with padding and filter it. This is
    a specialized version getData() for catalog events, pulling a smaller amount of time
    around a known event.

    date: UTCDateTime of known catalog event
    opt: Options object describing station/run parameters
    
    Returns ObsPy stream objects, one for cutting and the other for triggering
    """    
    
    nets = opt.network.split(',')
    stas = opt.station.split(',')
    locs = opt.location.split(',')
    chas = opt.channel.split(',')
    
    if opt.server == "IRIS":
        client = Client("IRIS")
    else:
        client = EWClient(opt.server, opt.port)
        
    st = Stream()
    for n in range(len(stas)):
        try:
            if opt.server == "IRIS":
                stmp = client.get_waveforms(nets[n], stas[n], locs[n], chas[n],
                    date - opt.atrig, date + 3*opt.atrig)
            else:
                stmp = client.getWaveform(nets[n], stas[n], locs[n], chas[n],
                    date - opt.atrig, date + 3*opt.atrig)
            stmp = stmp.filter("bandpass", freqmin=opt.fmin, freqmax=opt.fmax,
                corners=2, zerophase=True)
            stmp = stmp.merge(method=1, fill_value='interpolate')
        except (obspy.fdsn.header.FDSNException):
            try: # try again
                if opt.server == "IRIS":
                    stmp = client.get_waveforms(nets[n], stas[n], locs[n], chas[n],
                        date - opt.atrig, date + 3*opt.atrig)
                else:
                    stmp = client.getWaveform(nets[n], stas[n], locs[n], chas[n],
                        date - opt.atrig, date + 3*opt.atrig)
                stmp = stmp.filter("bandpass", freqmin=opt.fmin, freqmax=opt.fmax,
                    corners=2, zerophase=True)
                stmp = stmp.merge(method=1, fill_value='interpolate')
            except (obspy.fdsn.header.FDSNException):
                print('No data found for {0}.{1}'.format(stas[n],nets[n]))
                trtmp = Trace()
                trtmp.stats.sampling_rate = opt.samprate
                trtmp.stats.station = stas[n]
                stmp = Stream().extend([trtmp.copy()])
        # Resample to ensure all traces are same length
        if stmp[0].stats.sampling_rate != opt.samprate:
            stmp = stmp.resample(opt.samprate)
        st.extend(stmp.copy()) 
    
    st = st.trim(starttime=date-opt.atrig, endtime=date+3*opt.atrig, pad=True,
        fill_value=0)
    stC = st.copy() 

    return st, stC


def trigger(st, stC, rtable, opt):

    """
    Run triggering algorithm on a stream of data.

    st: OBSPy stream of data
    rtable: Repeater table contains reference time of previous trigger in samples
    opt: Options object describing station/run parameters

    Returns triggered traces as OBSPy trace object updates ptime for next run 
    """
    
    tr = st[0]
    t = tr.stats.starttime

    cft = coincidenceTrigger("classicstalta", opt.trigon, opt.trigoff, stC, opt.nstaC,
        sta=opt.swin, lta=opt.lwin, details=True)
    if len(cft) > 0:
        
        ind = 0
        
        # Slice out the data from st and save the maximum STA/LTA ratio value for
        # use in orphan expiration
        
        # Convert ptime from time of last trigger to seconds before start time
        if rtable.attrs.ptime:
            ptime = (UTCDateTime(rtable.attrs.ptime) - t)
        else:
            ptime = -opt.mintrig
        
        for n in range(len(cft)):
                    
            ttime = cft[n]['time'] # This is a UTCDateTime, not samples
            
            if (ttime >= t + opt.atrig) and (ttime >= t + ptime +
                opt.mintrig) and (ttime < t + len(tr.data)/opt.samprate -
                2*opt.atrig):
                
                ptime = ttime - t
                
                # Slice and save as first trace              
                ttmp = st.slice(ttime - opt.ptrig, ttime + opt.atrig)
                ttmp[0].data = ttmp[0].data[0:opt.wshape] - np.mean(
                    ttmp[0].data[0:opt.wshape])
                for s in range(1,len(ttmp)):
                    ttmp[0].data = np.append(ttmp[0].data, ttmp[s].data[
                        0:opt.wshape] - np.mean(ttmp[s].data[0:opt.wshape]))
                ttmp[0].stats.maxratio = np.max(cft[n]['cft_peaks'])
                if ind is 0:
                    trigs = Stream(ttmp[0])
                    ind = ind+1
                else:
                    trigs = trigs.append(ttmp[0])
                                                         
        if ind is 0:
            rtable.attrs.ptime = (t + len(tr.data)/opt.samprate - opt.mintrig).isoformat()
            return []
        else:
            rtable.attrs.ptime = (t + ptime).isoformat()
            return trigs
    else:
        rtable.attrs.ptime = (t + len(tr.data)/opt.samprate - opt.mintrig).isoformat()
        return []


def dataclean(alltrigs, opt, flag=1):

    """
    Examine triggers and weed out spikes and calibration pulses using kurtosis and
    outlier ratios
    
    alltrigs: triggers output from triggering
    opt: opt from config
    flag: 1 if defining window to check, 0 if want to check whole waveform for spikes
        (note that different threshold values should be used for different window lengths)
    
    Returns good trigs (trigs) and junk (junk)
    """
    
    trigs=Stream()
    junk=Stream()
    for i in range(len(alltrigs)):
            
        njunk = []
        
        for n in range(opt.nsta):
            
            dat = alltrigs[i].data[n*opt.wshape:(n+1)*opt.wshape]
            if flag == 1:
                datcut=dat[range(int((opt.ptrig-opt.kurtwin/2)*opt.samprate),
                    int((opt.ptrig+opt.kurtwin/2)*opt.samprate))]
            else:
                datcut=dat
            
            # Calculate kurtosis in window
            k = stats.kurtosis(datcut)
            # Compute kurtosis of frequency amplitude spectrum next
            datf = np.absolute(fft(dat))
            kf = stats.kurtosis(datf)
            # Calculate outlier ratio using z ((data-median)/mad); outliers have z > 4.45
            mad = np.median(np.absolute(dat - np.median(dat)))
            z = (dat-np.median(dat))/mad
            orm = len(z[z>4.45])/np.array(len(z)).astype(float)
            
            if k >= opt.kurtmax or orm >= opt.oratiomax or kf >= opt.kurtfmax:
                njunk.append(n)
          
        # Allow if there are enough good stations to correlate
        if len(njunk) <= (opt.nsta-opt.ncor):
            trigs.append(alltrigs[i])
        else:
            junk.append(alltrigs[i])
            
                
    return trigs, junk


def aicpick(st, initialTrigger, opt):
    
    """
    An autopicker to (hopefully) improve consistency in triggering
    
    st: OBSPy stream of data containing trigger
    initialTrigger: initial guess at trigger time (in number of samples into stream)
    opt: Options object describing station/run parameters
    
    Returns updated trigger time
    
    AIC stands for Akaike Information Criterion. This code is based on the formula in
    Zhang, Thurber, and Rowe [2003] (originally from Maeda [1985]) to calculate AIC
    directly from the waveform. It is a purely statistical picker, and the minimum of
    the AIC corresponds to where one can divide the signal into two different parts (in
    this case, noise followed by signal).
    """
    
    t = st[0].stats.starttime   
    x0 = st.slice(t - opt.ptrig/2 + initialTrigger/opt.samprate,
                  t + opt.ptrig/2 + initialTrigger/opt.samprate)
    x = x0[0].data
    nsamp = int(opt.ptrig*opt.samprate)
    
    AIC = np.zeros([nsamp,1])
        
    for k in range(nsamp):
            
        # Calculate the Akaike Information Criteria
        var1 = np.var(x[0:k+1])
        var2 = np.var(x[k:nsamp+1])
        
        if var1 == 0 or var2 == 0:
            AIC[k] = np.NaN
        else:
            AIC[k] = (k+1)*np.log10(var1) + (nsamp-k)*np.log10(var2)
            
    # Pad 10 samples on either end to prevent encountering edge effects
    picksamp = np.argmin(AIC[10:nsamp-10]) + initialTrigger - nsamp/2
                
    return picksamp
