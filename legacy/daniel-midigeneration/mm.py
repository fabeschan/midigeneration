#Look in table for an element [curr,next,anything] and return the index.
#return -1 if not found.
def match(curr,next,table):
	for i in range(len(table)):
		if(curr==table[i][0] and next==table[i][1]):
			return i
	return -1

#Normalize the matrix so each set of transition frequencies adds up to 1.
def normalize(table):
	listofstates=[]#Get a list of possible previous states from the table
	for x in table:
		if x[0] not in listofstates:
			listofstates+=[x[0]]
	for state in listofstates:#For each possible state
		emissions=0
		for transition in table:#Sum its transition frequency
			if transition[0]==state:
				emissions+=transition[2]
		for i in range(len(table)):#Then divide by the result
			if table[i][0]==state:
				table[i][2]/=float(emissions)
	return

#Make a Markov model out of data with specified order.
#statechains should be a list of lists, the inner lists each represent one real chain of states.
#The states themselves can be anything, but keep in mind lists are copied by referece.
#The value returned will have the structre [previous,next,frequency]
#Where previous is a list of previous states, it's length equal to the specified order,
#next is the state that comes after the previous states,
#and frequency is the probability of this transition.
#starttoken specifies a value that will not be inside the possible given states, so that is can be used to mean start.
#endtoken is the same, but for the end.
def make(statechains, order, starttoken="start", endtoken="end"):
	table=[]
	for statechain in statechains:
		previous=[starttoken]*order#Start with all the previous states set to "start".
		for next in statechain:
			i=match(previous,next,table)
			if i>=0:#If a match was found, increment the frequency.
				table[i]=[table[i][0],table[i][1],table[i][2]+1]
			else:#Otherwise, add a new state transition.
				table.append([previous,next,1])
			previous=previous[1:]+[next]#Get rid of the oldest and bring in the latest state.
		#Done with a statechain now
		table.append([previous,endtoken,1])#Add in a transition to "end".
	#Done with all the statechains
	import copy
	table=copy.deepcopy(table)
	return table

def possiblestarts(states, order, starttoken="start", current=[]):
	result=[]
	if current==[]:
		current=[starttoken]*order
		result+=[current]
	if starttoken not in current:
		return []
	for state in states:
		newcurrent=current[1:]+[state]
		result+=[newcurrent]
		result+=possiblestarts(states,order,starttoken,newcurrent)
	return result

def permutations(states, order, current=[]):
	if len(current)==order:
		return [[state for state in current]]
	current=current+[[]]
	result=[]
	for state in states:
		current[-1]=state
		result+=permutations(states,order,current)
	return result

def uniform(states, order, starttoken="start", endtoken="end"):
	table=[[previous,next,1.0] for previous in possiblestarts(states,order,starttoken) for next in states]
	table+=[[previous,"end",1.0] for previous in permutations(states,order)]
	return table

#Add two Markov models together.
#The weight specifies how much of each Markov model is desired.
#A weight of 0 returns the left Markov model exactly.
#A weight of 1 returns the right Markov model exactly.
#A weight of 0.5 exactly averages the two models.
#If normalize is false, the result is not normalized.
def add(left, right, leftweight=1.0, rightweight=1.0):
	result=[[x[0],x[1],x[2]*leftweight] for x in left]#Start off with just the left Markov model, taking weight into account
	#Now add in the right, taking weight into account, but make sure not to produce duplicate transitions.
	for iright in right:#For all elements in the right Markov model
		found=False#Assume it is not in our result until we find it.
		for i in range(len(result)):#Try to find it in our result.
			if result[i][0:2]==iright[0:2]:#If the transition was found,
				result[i][2]=result[i][2]+iright[2]*rightweight#Add in the transition probability
				found=True#Say we found it
				break#Get out; we're done
		if not found:#If the transition wasn't found, add it in.
			result+=[[iright[0],iright[1],iright[2]*rightweight]]
	import copy
	result=copy.deepcopy(result)
	return result

#Produce a random traversal of the Markov model represented by the given transition table.
def traverse(table, starttoken="start", endtoken="end"):
	statechain=[]
	current=[starttoken]*len(table[0][0])
	import random
	while True:
		choices=0
		for transition in table:
			if transition[0]==current:
				choices+=transition[2]
		choice=random.random()*choices
		choicemade=False
		for transition in table:
			if transition[0]==current:
				choice-=transition[2]
				if choice<choices/1000.0:
					current=current[1:]+[transition[1]]
					choicemade=True
					break
		if not choicemade:
			print choice
			print current
			return -1
		if current[-1]==endtoken:
			break
		statechain+=[current[-1]]
	import copy
	statechain=copy.deepcopy(statechain)
	return statechain

#Produce a list of possible next states, with frequency
def next(table, current):
	next=[]
	for transition in table:
		if transition[0]==current:
			next+=[transition[1:]]
	return next
