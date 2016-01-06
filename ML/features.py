# -*- coding: utf8 -*-
import scipy
import librosa
import numpy as np
import wave

NMFCC = 13
K = 7

class Char:
	def __init__(self, name, url):
		self.name = name.encode('big5')
		self.url = url
		(y, fs) = getSignal(url)	
		self.mfcc = getMFCC(y, fs)
	@staticmethod
	def createFromSig(y, fs):
		t = type('test', (), {})()
		t.name = 'unknown'
		t.url = ''
		t.mfcc = getMFCC(y, fs)
		return t

class CharPair:
	def __init__(self, c1, c2):
		self.label = (c1.name == c2.name)
		self.url1 = c1.url
		self.url2 = c2.url
		self.dist = getDTW(c1.mfcc, c2.mfcc)
		print("%f %s %s %s" % (self.dist, c1.name, c2.name, self.label))

def getSignal(url):
	f = wave.open(url, "rb")
	params = f.getparams()
	nchannels, sampwidth, framerate, nframes = params[:4]
	str_data = f.readframes(nframes)
	f.close()
	y = np.fromstring(str_data, dtype=np.short)
	if nchannels == 2:
		y.shape = -1, 2
		y = y.T
		y = y[0]
	return (y, framerate)

def getMFCC(y, framerate, path=None):
	return librosa.feature.mfcc(y, framerate, n_mfcc=NMFCC)

def getDist(p1, p2):
	#Both of dimention NMFCC
	t = 0
	for i in range(1, NMFCC-1):
		a = (p1[i]-p1[i-1] + (p1[i+1]-p1[i-1])/2)/2
		b = (p2[i]-p2[i-1] + (p2[i+1]-p2[i-1])/2)/2
		t += (a-b)**2
	return t**0.5

def getDTW(mfcc1, mfcc2): #tail free!?
	n = len(mfcc1.T)
	m = len(mfcc2.T)
	d = np.zeros(shape=(n, m))-1
	cnt = np.zeros(shape=(n, m))-1
	recursiveGetDTW(n-1, m-1, d, cnt, mfcc1, mfcc2)

	mini = np.inf
	for i in range(0, n):
		mini = min(mini, d[i][m-1])
	for i in range(0, m):
		mini = min(mini, d[n-1][i])
	return mini

def recursiveGetDTW(i, j, d, cnt, mfcc1, mfcc2):
	if i < 0 or j < 0:
		return np.inf
	if i == j and i == 0:
		cnt[0][0] = 0
		return 0
	if d[i][j] > 0:
		return d[i][j]

	a = recursiveGetDTW(i-1, j, d, cnt, mfcc1, mfcc2)
	b = recursiveGetDTW(i, j-1, d, cnt, mfcc1, mfcc2)
	c = recursiveGetDTW(i-1, j-1, d, cnt, mfcc1, mfcc2)
	dist = getDist(mfcc1.T[i], mfcc2.T[j])
	if i > 0:
		a = (cnt[i-1][j]*a + dist)/(1+cnt[i-1][j])
		if j > 0:
			c = (cnt[i-1][j-1]*c + dist)/(1+cnt[i-1][j-1])
	if j > 0:
		b = (cnt[i][j-1]*b + dist)/(1+cnt[i][j-1])
	d[i][j] = min(a, b, c)
	index = [a, b, c].index(d[i][j])
	if index == 0:
		cnt[i][j] = cnt[i-1][j] + 1
	elif index == 1:
		cnt[i][j] = cnt[i][j-1] + 1
	else:
		cnt[i][j] = cnt[i-1][j-1] + 1
	return d[i][j]

def kNN(chars, char):
	buff = [[np.inf, None] for i in range (0, K)]
	for c in chars:
		if c.url == char.url:
			continue
		dist = getDTW(c.mfcc, char.mfcc)
		maxb = max(buff, key=lambda x : x[0])
		if(maxb[0] > dist):
			maxb[0] = dist
			maxb[1] = c.name
	buff = sorted(buff, key=lambda x : x[0])
	for b in buff:
		print("%s, %f" % (b[1], b[0]))
	print(char.name)

def classify(chars, char):
	d = {}
	cnt = 0
	name = None
	for c in chars:
		if c.url == char.url:
			continue
		dist = getDTW(c.mfcc, char.mfcc)
		if c.name not in d:
			if name:
				d[name] /= cnt
			d[c.name] = 0
			cnt = 0
		cnt += 1
		name = c.name
		d[name] += dist

	for k in d:
		print("%s, %f" % (k, d[k]))
	print("%s, %f" % (char.name, d[char.name]))