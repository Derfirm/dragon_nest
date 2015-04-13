import random 

class AAA(object):
    pass

pumpum = [AAA() for _ in xrange(10)]
target = random.choice(pumpum)
print target
pumpum = [unit for unit in pumpum if unit != target] 
print len(pumpum)