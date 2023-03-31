from itertools import chain, combinations

def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(1,len(s)))

def test2(stuff):
    subsets = []
    for L in range(0,len(stuff)):
        for subset in combinations(stuff, L):
            subsets.append(subset)
    return list(map(list,subsets))

print(test2([1,2,3])[1])