import sys

def make(file, order):
	import midi
	song=midi.read(file)
	gotkey=False
	gottime=False
	gotticks=False
	for event in song[0]:
		if event[1]==0:
			if event[0]=="key":
				key=event[2:4]
				gotkey=True
			if event[0]=="time":
				time=event[2:4]
				gottime=True
			if event[0]=="ticks":
				ticks=event[2]
				gotticks=True
	if not(gotkey and gottime and gotticks):
		return -1
	if ticks!=256:
		return -1
	midi.transpose(song,-midi.sharpstosemitones(key[0],key[1]))
	#append place in bar to state
	import copy
	songcopy=copy.deepcopy(song)
	midi.bar(songcopy)
	for i in range(1,len(songcopy)):
		k=0
		for j in range(len(songcopy[i])):
			if songcopy[i][j][0]!="bar":
				song[i][k]+=[songcopy[i][j][1]]
				k+=1
	#turn duration into end time
	for i in range(1,len(song)):
		for j in range(len(song[i])):
			song[i][j][2]+=song[i][j][1]
	#turn this mess into some statechains as specified by cmm
	statechains=[]
	for i in range(1,len(song)):
		statechains+=[[]]
		for j in range(len(song[i])):
			statechains[-1]+=[[song[i][j][1],song[i][j][2],[song[i][j][4],song[i][j][5]]]]	
	return song
	#writer = open("midinotes.txt", 'w')
	#writer.write(str(song))
	#writer.close()
	#import cmm
	#return [cmm.make(statechains, order),time]

#Make a concurrency with harmonies based on the harmonic series.
#The result concurrency will have the same rhythms as the given concurrency.
def harmonic(concurrency, weight):
	#Find each kind of rhythm in the concurrency
	rhythms=[]
	for entry in concurrency:
		rhythm=[[[state[0][0],state[0][1]],state[1]] for state in entry[0]]
		if rhythm not in rhythms:
			rhythms+=[rhythm]
	#For each rhythm, make an entry for each harmony
	for rhythm in rhythms:
		#[[[[["null","null",state],"null"],[["null","null",state],"null"]],frequency],...]
		0
	return

def use(model, filename="music.mid"):
	import cmm
	statemap=cmm.use(model[0])
	song=[[]]
	song[0]=[["ticks",0,256],["time",0,model[1][0],model[1][1]]]
	for i in range(len(statemap)):
		song+=[[]]
		for state in statemap[i]:
			song[-1]+=[["note",state[0],state[1]-state[0],i,state[2][0]]]
	import midi
	midi.write(filename,song)
	return

def add(model1, model2):
	if model1[1]!=model2[1]:
		return
	import cmm
	result=[cmm.add(model1[0],model2[0]),model1[1]]
	import copy
	result=copy.deepcopy(result)
	return result
