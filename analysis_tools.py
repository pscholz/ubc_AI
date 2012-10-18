"""
Some routines that may be useful in analyzing the prediction performance.

"""
import numpy as np
import pylab as plt


def hist_overlap(A,B, idx=0, norm=True):
    """
    given two histograms, determine the overlap:
    Overlap(A,B) = \sum_i( min(A[i], B[i]) )

    args:
    A: array NumA(nbins)
    B: array NumB(nbins)
    
    Optional:
    idx: starting index of the sum "i" 
         (useful to determine the best cut (to minimize overlap))
    norm: True: normalize the Overlap with A.sum()/(A+B).sum()

    """
    k = np.array([ min(v, B[idx:][i]) for i, v in enumerate(A[idx:])])
    if norm:
        N = float(A[idx:].sum())/(A[idx:] + B[idx:]).sum()
    else:
        N = 1.
    return k.sum()*N

def plot_histogram(probs, target, title=''):
    """
    Given the list of pulsar probabilities 'proba'
    and the true target 'target', make a histogram
    of the pulsar and rfi distributions

    Assumes pulsars labelled '1', rfi '0'
    """
    if isinstance(probs, list):
        probs = np.array(probs)
    if probs.ndim == 2:
        probs = probs[...,1]

    plt.clf()
    nrfi = np.sum(target != 1)
    npulsar = np.sum(target == 1)
    npsr_clf, binpsr, patchespsr = plt.hist(probs[target==1], 25, facecolor='green', alpha=0.65, label='pulsars (%s)' %npulsar, range=[0,1])

    nrfi_clf, binrfi_clf, patchesrfi_clf = plt.hist(probs[target!=1], 25, facecolor='red', alpha=0.65, label='rfi (%s)' %nrfi, range=[0,1])

    plt.legend()
    plt.xlabel('pulsar prediciton')
    plt.ylabel('number')

    pct, f1, prec, compl = find_best_f1(probs, target)
    overlap = hist_overlap(npsr_clf, nrfi_clf, idx=0, norm=True)
    title = '%s, best (cut, P, C, f1) = (%.3f, %.3f, %.3f, %.3f), (overlap: %s)' %\
        (title, pct, prec, compl, f1, int(overlap))

    plt.title(title)
    plt.show()
    
def find_best_f1(proba, target):
    """
    look at different proba cuts for pulsar classification (label '1')
    to determine the best f1

    returns:
    pct of best cut, F1 of best cut, precision of best cut, completeness of best cut

    """
    if isinstance(proba, list):
        proba = np.array(proba)
    if proba.ndim == 2:
        proba = proba[...,1]

    nbins = 100
    #true pulsars
    tp = target == 1

    bestpct = 0.
    f1 = 0
    bestprec = 0.
    bestcompl = 0.
    for pct in np.linspace(0., proba.max(), nbins, endpoint=False):
        preds = np.where(proba > pct, 1, 0)
        #pulsars have value '1'
        precision = float(np.sum(preds[tp] == target[tp]))/preds.sum()
        completeness = float(np.sum(preds[tp] == target[tp]))/tp.sum()
        
        this_f1 = 2*precision*completeness/(precision+completeness)

        if this_f1 > f1:
            bestpct = pct
            f1 = this_f1
            bestprec = precision
            bestcompl = completeness
    return bestpct, f1, bestprec, bestcompl
    
def cut_performance(AIs, target, nbins=25, plot=True, norm=True):
    """
    given a dictionary of AIs (keyword = descriptive name, value = predict_proba[...,1])
    return a dictionary of the hist_overlap as we change the %cut

    useful for determining and comparing the optimal cut, below which 
    the mixing of pulsars and rfi is too much

    Args:
    AIs: dictionary of AIs 
    target: target value
    nbins: number of phase bins to cut
    plot: True/False make the plots, or only return the data
    norm: when calculating the overlap, 
          normalize recovered fraction by by pulsar/(pulsar+rfi)


    Returns:
    1) pct cut
    2) dictionary of key=AI, val=overlap(cut)
    3) dictionary of key=AI, val=% of pulsar recovered at this cut

    """
    import pylab as plt
    from itertools import cycle
    lines = ["--","-",":","-."]

    performance = {}
    pct_recovered = {}
    for k in AIs:
        performance[k] = []
        pct_recovered[k] = []
    psr_hist = {}
    rfi_hist = {}
    for k, v in AIs.iteritems():
        if v.ndim == 1:
            psr_hist[k] = np.histogram(v[target==1], nbins, range=[0,1])[0] #returns histogram, bin_edges
            rfi_hist[k] = np.histogram(v[target!=1], nbins, range=[0,1])[0]
        else:
            psr_hist[k] = np.histogram(v[target==1][...,1], bins=nbins, range=[0,1])[0] #returns histogram, bin_edges
            rfi_hist[k] = np.histogram(v[target!=1][...,1], bins=nbins, range=[0,1])[0]
        
    #now change the cut and record the overlap
    pcts = []
    for i in range(nbins-1):
        pcts.append(float(i)/nbins)
        for k, v in performance.iteritems():
            A = psr_hist[k]
            B = rfi_hist[k]
            v.append( hist_overlap(A,B, idx=i, norm=norm) )
            pct_recovered[k].append(float(A[i:].sum())/A.sum())

    if plot:
        ax = plt.subplot(211)
        linecycler = cycle(lines)
        for k, v in performance.iteritems():
            ax.plot(pcts, v, next(linecycler), label=k)
        ax.set_xlabel('pct cut')
        ax.set_ylabel('overlap')
        ax.legend()

        ax = plt.subplot(212)
        linecycler = cycle(lines)
        for k, v in pct_recovered.iteritems():
            ax.plot(pcts, v, next(linecycler), label=k)
        ax.set_xlabel('pct cut')
        ax.set_ylabel('pulsar fraction recovered')
        ax.legend(loc=3)
        
        plt.show()

    return pcts, performance, pct_recovered
