#!/usr/bin/env python3

import math
import sys
from random import choice
from timeit import default_timer as timer

class Game:

	def __init__(self, nc=7, nr=6, n=4):
		self.P = ['.', 'x', 'o', '-']
		self.nc, self.nr, self.n = nc, nr, n
		self.clear()

	def clear(self):
		self.p, self.winner = 1, 0
		self.cols = [[self.P[0]]*self.nr for _ in range(self.nc)]	# [col][row]

	def topFree(self, col):
		for r in range(self.nr):
			if col[r] != self.P[0]:
				return r - 1
		return self.nr - 1

	def canPlay(self, c):
		'Return whether play would be valid'
		return not self.over() and 0 <= c < self.nc and self.topFree(self.cols[c]) >= 0

	def play(self, c):
		'Play move'
		r = self.topFree(self.cols[c])
		assert(r >= 0)
		self.cols[c][r] = self.P[self.p]
		self.winner = self.calcWinner(c)
		self.p = {1: 2, 2: 1}[self.p]

	def over(self):
		'Return whether this game can no longer be played'
		return self.winner != 0

	def row(self, r):
		for c in range(self.nc):
			yield self.cols[c][r]

	def pdiag(self, d):
		'Yield elements on the d-th positive diagonal (str)'
		for c in range(self.nc):
			if 0 <= d - c < self.nr:
				yield self.cols[c][d - c]

	def ndiag(self, d):
		'Yield elements on the d-th negative diagonal (str)'
		for c in reversed(range(self.nc)):
			if 0 <= d - c < self.nr:
				# print('ndiag (d: %d, c: %d)'%(d, c), self.nc - 1 - c, d - c)
				yield self.cols[self.nc - 1 - c][d - c]

	def calcWinner(self, c0):
		r0 = self.topFree(self.cols[c0]) + 1
		me = self.cols[c0][r0]

		n = 1
		# Look left
		for c in reversed(range(c0)):
			if self.cols[c][r0] != me: break
			n += 1
		# Look right
		for c in range(c0+1, self.nc):
			if self.cols[c][r0] != me: break
			n += 1

		if n >= self.n: return self.p

		n = 1
		# Look up
		for r in reversed(range(r0)):
			if self.cols[c0][r] != me: break
			n += 1
		# Look down
		for r in range(r0+1, self.nr):
			if self.cols[c0][r] != me: break
			n += 1
		if n >= self.n: return self.p

		n = 1
		# Look up-left
		for d in range(1, min(c0, r0) + 1):
			if self.cols[c0-d][r0-d] != me: break
			n += 1
		# Look down-right
		for d in range(1, min(self.nc - c0, self.nr - r0)):
			if self.cols[c0+d][r0+d] != me: break
			n += 1
		if n >= self.n: return self.p

		n = 1
		# Look up-right
		for d in range(1, min(self.nc - c0, r0 + 1)):
			if self.cols[c0+d][r0-d] != me: break
			n += 1
		# Look down-left
		for d in range(1, min(c0 + 1, self.nr - r0)):
			if self.cols[c0-d][r0+d] != me: break
			n += 1
		if n >= self.n: return self.p

		# Check for draw
		if r0 == 0 and all(c != self.P[0] for c in self.row(0)):
			return 3

		return 0

	def bruteCalcWinner(self):
		'Return winner (idx)'
		P = self.P

		# Check cols
		s1, s2 = P[1]*self.n, P[2]*self.n
		for col in self.cols:
			colStr = ''.join(col)
			if s1 in colStr: return 1
			if s2 in colStr: return 2

		# Check rows
		for r in range(self.nr):
			rowStr = ''.join(self.row(r))
			if s1 in rowStr: return 1
			if s2 in rowStr: return 2

		# Check diagonals
		D = min(self.nc, self.nr)
		for d in range(self.n - 1, self.nc + self.nr - self.n):
			pdiagStr = ''.join(e for e in self.pdiag(d))
			if s1 in pdiagStr: return 1
			if s2 in pdiagStr: return 2
			ndiagStr = ''.join(e for e in self.ndiag(d))
			if s1 in ndiagStr: return 1
			if s2 in ndiagStr: return 2

		# Check full
		if all(c != self.P[0] for c in self.row(0)):
			return 3

		return 0

	def __repr__(self):
		s = ' '.join(map(str, range(self.nc))) + '\n'
		s += '\n'.join(' '.join(col[r] for col in self.cols) for r in range(self.nr))

		ss = ['Turn (%s)' % self.P[self.p]]
		if self.winner != 0: ss += ['Winner (%s)' % self.P[self.winner]]
		if self.over(): ss += ['Game over']

		s += '\n' + '\t'.join(ss)
		return s

	def copyFrom(self, other):
		for c in range(self.nc):
			for r in range(self.nr):
				self.cols[c][r] = other.cols[c][r]
		self.nc, self.nr, self.n = other.nc, other.nr, other.n
		self.p, self.winner = other.p, other.winner

	def actionSpace(self):
		return list(c for c in range(self.nc) if self.cols[c][0] == self.P[0])

# Bad move: if played, the opponent has a sure win move afterwards (so don't play it)
def badMoves(g, g2, g3):
	bad = set()
	me = g.p
	for c in g.actionSpace():
		g2.copyFrom(g)
		g2.play(c)
		if g2.winner == me:
			bad = g.actionSpace()
			bad.remove(c)
			return set(bad)
		opp = g2.p
		for c2 in g2.actionSpace():
			g3.copyFrom(g2)
			g3.play(c2)
			if g3.winner == opp:
				bad.add(c)
				break
	return bad

def human(*, name='Human'):
	def f(g):
		while True:
			i = input('%s: ' % name)
			try:
				return int(i)
			except ValueError:
				pass
	return f

def smartNoise(*, name='Smart noise', verbose=True):
	def f(g):
		def out(c):
			if verbose: print('%s: %s' % (name, c))
			return c

		g2, g3 = Game(), Game()
		acs = g.actionSpace()
		cs = list(set(acs) - badMoves(g, g2, g3))
		cs = cs or acs
		return out(choice(cs))

	return f

def mcs(*, name='MCS', timeout=5.0, verbose=True):
	'''
	timeout: seconds
	'''
	def f(g):
		start = timer()

		def out(c):
			if verbose: print('%s: %s' % (name, c))
			return c

		nc = g.nc
		me = g.p
		opp = {1: 2, 2: 1}[me]

		cs = g.actionSpace()
		totals = {c: 0 for c in cs}
		wins = {c: 0 for c in cs}

		g2, g3, g4 = Game(), Game(), Game()

		# Prune obviously bad moves 1 step ahead
		cs = list(set(cs) - badMoves(g, g2, g3))
		if verbose: print('After pruning: %s' % sorted(cs))

		if not cs: return out(choice(g.actionSpace()))
		if len(cs) == 1: return out(cs[0])

		it = 0
		while True:
			c1 = choice(cs)

			g2.copyFrom(g)
			g2.play(c1)

			acs2 = g2.actionSpace()
			cs2 = list(set(acs2) - badMoves(g2, g3, g4))
			c2 = choice(cs2 if cs2 else acs2)

			g3.copyFrom(g2)
			g3.play(c2)

			while not g3.winner:
				g3.play(choice(g3.actionSpace()))

			totals[c1] += 1
			if g3.winner == me:
				wins[c1] += 1

			it += 1
			if it & (128 - 1) == 1 and timer() - start > timeout:
				if verbose: print('%d iters (~%f turns ahead)' % (it, math.log(it, len(cs))))
				break

		scores = {c: wins[c] / totals[c] for c in cs}
		if verbose: print(scores)
		if verbose: print('Win prob: %.2f%%' % (max(scores.values()) * 100))
		return out(max(scores, key=scores.get))

	return f

g = Game()

mode = 'play'
players = {1: mcs(timeout=5.0), 2: human()}

if len(sys.argv) > 1:
	if sys.argv[1] == 'human':
		players = {1: human(), 2: mcs(timeout=5.0)}
	elif sys.argv[1] == 'stats':
		mode = 'stats'
		timeout = 10.0
		players = {1: mcs(timeout=timeout, verbose=False), 2: mcs(timeout=timeout, verbose=False)}

if mode == 'play':
	print(g)
	while not g.winner:
		print(g.P[g.p], end=' ')
		mv = players[g.p](g)
		if not g.canPlay(mv):
			continue
		g.play(mv)
		print(g)
		print()

elif mode == 'stats':
	wins = {1: 0, 2: 0, 3: 0}

	if len(sys.argv) > 2:
		wins[1] = int(sys.argv[2])
	if len(sys.argv) > 3:
		wins[2] = int(sys.argv[3])
	if len(sys.argv) > 4:
		wins[3] = int(sys.argv[4])

	t = sum(wins.values())
	while True:
		g.clear()
		start = timer()
		seq = []
		while not g.winner:
			c = players[g.p](g)
			if not g.canPlay(c):
				continue
			g.play(c)
			seq += [c]
		end = timer()
		wins[g.winner] += 1
		t += 1
		print('%d\t[%.3fs]\t%d wins (1: %d (%.1f%%), 2: %d (%.1f%%), draw: %d (%.1f%%))\t%s' % (t, end - start, g.winner, wins[1], wins[1]/t*100, wins[2], wins[2]/t*100, wins[3], wins[3]/t*100, ''.join(map(str, seq))))
