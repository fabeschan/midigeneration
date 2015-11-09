def statesintime(statemap, time, nulltoken="null"):
	states=[]
	minoffset=[]
	for statechain in statemap:
		states+=[[]]
		laststate=nulltoken
		for i in range(len(statechain)):
			if statechain[i][0]>time:
				break
			length=statechain[i][1]-statechain[i][0]
			if i+1<len(statechain):
				length=statechain[i+1][0]-statechain[i][0]
			if statechain[i][0]<=time and statechain[i][1]>time:
				states[-1]+=[[[statechain[i][1]-statechain[i][0],length,statechain[i][2]],statechain[i][0]-time]]
				if minoffset==[] or states[-1][-1][1]<minoffset:
					minoffset=states[-1][-1][1]
			laststate=[[statechain[i][1]-statechain[i][0],length,statechain[i][2]],statechain[i][0]-time]
		if states[-1]==[]:
			if laststate==nulltoken:
				import pdb
				pdb.set_trace()
			states[-1]=[laststate]
			if minoffset==[] or states[-1][-1][1]<minoffset:
				minoffset=states[-1][-1][1]
	#for i in range(len(states)):
		#for j in range(len(states[i])):
			#states[i][j][1]-=minoffset
	return states

#Make a concurrent Markov model out of data with specified order.
#statemap should be a list of lists, each inner list represents one statechain that is happening concurrently with the others.
#The elements of a statechain must have the following form: [start time, end time, state].
#All times should be nonnegative
#They should be sorted by start time.
#order is the Markov model order for each statechain
#starttoken specifies a value that will not be inside the possible given states, so that is can be used to mean start.
#endtoken is the same, but for the end.
#nulltoken is the same, but means no state.
def make(statemap, order, starttoken="start", endtoken="end", nulltoken="null"):
	#Find state transitions of each chain independently
	tables=[]
	import copy
	statemap=copy.deepcopy(statemap)
	latestend=0
	for statechain in statemap:
		if len(statechain)>0:
			if statechain[-1][1]>latestend:
				latestend=statechain[-1][1]
	#Stick in null state if a statechain is empty
	for i in range(len(statemap)):
		if len(statemap[i])==0:
			statemap[i]=[[0,latestend,nulltoken]]
	#pad statechains that don't end at same time with null states
	for i in range(len(statemap)):#Pad
		if statemap[i][-1][1]<latestend:
			statemap[i]+=[[statemap[i][-1][1],latestend,nulltoken]]
		#pad statechains that don't begin at time 0 with null states
		if statemap[i][0][0]>0:
			statemap[i]=[[0,statemap[i][0][0],nulltoken]]+statemap[i]
	for statechain in statemap:
		tables+=[[]]
		previous=[starttoken]*order#Start with previous states set to "start".
		for i in range(len(statechain)):#For all states
			next=copy.deepcopy(statechain[i])
			#Turn start and end times into duration and length.
			temp=next[0]
			next[0]=next[1]-next[0]#duration
			if i<len(statechain)-1:#length
				next[1]=statechain[i+1][0]-temp
			else:#If there's no state after, set length equal to duration
				next[1]=next[0]
			if [previous, next] in [transition[0:2] for transition in tables[-1]]:#Transition in the table already?
				tables[-1][[transition[0:2] for transition in tables[-1]].index([previous,next])][2]+=1#If so, increment frequency
			else:#Otherwise, add a new state transition.
				tables[-1].append([previous,next,1])
			previous=previous[1:]+[next]#Get rid of the oldest and bring in the latest state.
		#Done with a statechain now
		tables[-1].append([previous,endtoken,1])#Add in a transition to "end".
	#Finished all Markov models
	tables=copy.deepcopy(tables)#To eliminate duplicate references
	#See which states happen concurrently.
	i=[0]*len(statemap)#an index for each statechain
	concurrency=[]
	import rel
	while True:
		#find smallest start times
		minstart=[]#smallest start time, initialized to flag value,
		minstarti=0.0#and its index, initialized to poison value.
		for j in range(len(i)):#For each index
			if i[j]<len(statemap[j]) and (statemap[j][i[j]][0]<minstart or minstart==[]):#See if the start time is smallest
				minstart=statemap[j][i[j]][0]#If it is, update smallest value
				minstarti=[j]
			elif i[j]<len(statemap[j]) and (statemap[j][i[j]][0]==minstart):
				minstarti+=[j]
		if minstart==[]:#In case of error
			print "no minimum start time found."
			import pdb
			pdb.set_trace()
		#find concurrent states
		concurrents=rel.cproduct(statesintime(statemap, minstart))
		#add them in, accounting for collisions.
		for states in concurrents:
			if states in [element[0] for element in concurrency]:
				concurrency[[element[0] for element in concurrency].index(states)][1]+=1
			else:
				concurrency+=[[states,1]]
		#increment the index we just looked at so we don't count it again
		for j in minstarti:
			i[j]+=1
		#see if we need to quit
		quit=True
		for j in range(len(i)):
			if i[j]<len(statemap[j]):
				quit=False
		if quit:
			break
	concurrency=copy.deepcopy(concurrency)
	return [tables, concurrency]

def use(model, starttoken="start", endtoken="end", nulltoken="null"):
	import copy
	model=copy.deepcopy(model)
	tables=model[0]#The Markov models of each concurrent statechain
	concurrency=model[1]#The concurrency between them
	order=len(tables[0][0][0])#Order of the Markov models
	statechains=len(tables)#Number of concurrent statechains
	previous=[[starttoken]*order for i in range(statechains)]#Previous states for each statechain, initialized to starttoken
	times=[0]*statechains#The next time a state starts for each statechain being generated
	statemap=[[] for i in range(statechains)]#The result, initialized to empty
	import rel
	import random
	while True:
		#Find the possible transitions for each statechain we are appending to and get the cartesian product
		#We're appending to all statechains with are furthest behind
		transitions=[]#List of options for each statechain
		for i in range(statechains):#For each statechain
			if times[i]==min(times):#If the statechains is one of the furthest back ones,
				transitions+=[[]]#In a new slot,
				for transition in tables[i]:#Stick in every possible next state and its frequency
					if transition[0]==previous[i]:
						transitions[-1]+=[[transition[1],transition[2]]]
			else:#If it's not, stick in the most recent state
				transitions+=[[[previous[i][-1],1]]]
		#Right now transitions is a list of alternative transitions for each statechain
		transitions=rel.cproduct(transitions)
		#Now transitions is a list of alternative overall transitions, but
		#we need to calculate overall probability.
		for i in range(len(transitions)):#for each overall transition
			frequency=1#multiply-accumulator
			for j in range(statechains):#for each statechain's transition
				frequency*=transitions[i][j][1]#multiply frequency
				transitions[i][j]=transitions[i][j][0]#get rid of the partial frequency
			transitions[i]=[transitions[i],frequency]#add the overall frequency in
		#Multiply transition frequencies by concurrency frequencies
		for i in range(len(transitions)):#For each overall transition
			ct=[]#concurrency of the transition
			for j in range(statechains):#for each statechain's transition
				if previous[j][-1]==starttoken or times[j]==min(times):#if it's the beginning or a statechain we're appending to
					ct+=[[transitions[i][0][j],0]]#the offset is 0
				else:#otherwise, calculate the offset
					ct+=[[transitions[i][0][j],times[j]-previous[j][-1][1]-min(times)]]
			if ct in [x[0] for x in concurrency]:
				transitions[i][1]*=concurrency[[x[0] for x in concurrency].index(ct)][1]
			else:#If it doesn't show up in the concurrency, it might be because it's an end state
				possibleend=False
				for overalltransition in transitions:#see if there's an end state
					for transition in overalltransition[0]:
						if transition==endtoken:
							possibleend=True
							break
					if possibleend:#If it's an end state, get out, preserve frequency
						break
				if not possibleend:#If it's not an end state, it's genuinely impossible
					transitions[i][1]=0
		choices=0
		for transition in transitions:#count choices
			choices+=transition[1]
		choice=random.random()*choices#make a choice
		choicemade=False
		for transition in transitions:#find the choice
			choice-=transition[1]
			if choice<choices/1000.0:
				#update previous
				for i in range(statechains):
					if times[i]==min(times):
						previous[i]=previous[i][1:]+[transition[0][i]]
				choicemade=True
				break
		if not choicemade:
			import pdb
			pdb.set_trace()
		if endtoken in [x[-1] for x in previous]:
			break
		#update statemap and times
		mintimes=min(times)
		for i in range(statechains):
			if times[i]==mintimes:
				statemap[i]+=copy.deepcopy([previous[i][-1]])
				temp=statemap[i][-1][1]
				statemap[i][-1][1]=times[i]+statemap[i][-1][0]
				statemap[i][-1][0]=times[i]
				times[i]+=temp
	#unpad
	for i in range(statechains):
		if statemap[i][0][2]==nulltoken:
			del statemap[i][0]
		if statemap[i][-1][2]==nulltoken:
			del statemap[i][-1]
	return statemap

def add(model1, model2):
	if len(model1[0])!=len(model2[0]):
		return
	import copy
	model1=copy.deepcopy(model1)
	for i in range(len(model2[0])):
		for entry in model2[0][i]:
			transition=entry[0:2]
			if transition in [x[0:2] for x in model1[0][i]]:
				model1[0][i][[x[0:2] for x in model1[0][i]].index(transition)][2]+=entry[2]
			else:
				model1[0][i]+=[entry]
	for entry in model2[1]:
		concurrency=entry[0]
		if concurrency in [x[0] for x in model1[1]]:
			model1[1][[x[0] for x in model1[1]].index(concurrency)][1]+=entry[1]
		else:
			model1[1]+=[entry]
	return model1
