def cproduct(lists):
	import copy
	lists=copy.deepcopy(lists)
	partial=[[x] for x in lists[0]]
	del lists[0]
	while len(lists):
		newpartial=[]
		for i in partial:
			for j in lists[0]:
				newpartial+=[copy.deepcopy(i)+[copy.deepcopy(j)]]
		partial=copy.deepcopy(newpartial)
		del lists[0]
	return partial