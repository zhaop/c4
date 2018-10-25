#!/usr/bin/env python3

import math
import sys
from random import choice
from timeit import default_timer as timer

class Game:

	def __init__(self, nc=7, nr=6, n=4):
		self.P = ['.', '🔵', '🔴', '-']
		self.nc, self.nr, self.n = nc, nr, n
		self.clear()

	def clear(self):
		self.p, self.winner = 1, 0
		self.cols = [[self.P[0]]*self.nr for _ in range(self.nc)]	# [col][row]

	def topFree(self, col):
		for r, v in enumerate(col):
			if v != self.P[0]:
				return r - 1
		return len(col) - 1

	def canPlay(self, c):
		'Return whether move would be legal'
		return not self.over() and 0 <= c < self.nc and self.topFree(self.cols[c]) >= 0

	def play(self, c):
		'Play move c'
		r = self.topFree(self.cols[c])
		assert(r >= 0)
		self.cols[c][r] = self.P[self.p]
		self.winner = self.calcWinner(c)
		self.p = {1: 2, 2: 1}[self.p]

	def unplay(self, c):
		'Unplay move c'
		r = self.topFree(self.cols[c]) + 1
		assert(r >= 0)
		self.winner = 0
		self.cols[c][r] = self.P[0]
		self.p = {1: 2, 2: 1}[self.p]

	def over(self):
		'Return whether this game can no longer be played'
		return self.winner != 0

	def row(self, r):
		for c in range(self.nc):
			yield self.cols[c][r]

	def calcWinner(self, c0):
		'''
		Return who wins given that the current player played at c0 (call AFTER c0 is placed)
		0: nobody, 1: player 1, 2: player 2, 3: ends in a draw
		'''
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
		if r0 == 0 and all(v != self.P[0] for v in self.row(0)):
			return 3

		return 0

	def __repr__(self):
		ss = [] if self.winner else ['Turn %s' % self.P[self.p]]
		if self.winner != 0: ss += ['Winner %s' % self.P[self.winner]]
		if self.over(): ss += ['Game over']

		return '\n'.join([
			'\t'.join(ss),
			' '.join(map(str, range(self.nc))),
			'\n'.join(' '.join(col[r] for c, col in enumerate(self.cols)) for r in range(self.nr))
		])

	def copyFrom(self, other):
		for c in range(self.nc):
			for r in range(self.nr):
				self.cols[c][r] = other.cols[c][r]
		self.nc, self.nr, self.n = other.nc, other.nr, other.n
		self.p, self.winner = other.p, other.winner

	def actionSpace(self):
		return list(c for c in range(self.nc) if self.cols[c][0] == self.P[0])

# List of all valid moves except bad moves (which if played, the opponent has a sure win move afterwards)
# Except if there is a sure win move for us, in which case return only that (if multiple, return one of them)
# moves: if provided, will filter on a copy of this list instead
def reasonableMoves(g, g2, *, moves=None):
	if moves is None: moves = g.actionSpace()
	moves, bad, me = set(moves), set(), g.p

	g2.copyFrom(g)
	for c in moves:
		g2.play(c)
		if g2.winner == me:
			return [c]
		opp = g2.p
		for c2 in g2.actionSpace():
			g2.play(c2)
			if g2.winner == opp:
				bad.add(c)
				g2.unplay(c2)
				break
			g2.unplay(c2)
		g2.unplay(c)

	return list(moves - bad)

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
		acs = g.actionSpace()
		cs = reasonableMoves(g, Game(), moves=acs)
		if verbose: print('Reasonable moves: %s' % cs)
		return out(choice(cs or acs))

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

		g2, g3 = Game(), Game()

		cs = reasonableMoves(g, g2, moves=cs)
		if not cs: return out(choice(g.actionSpace()))
		if len(cs) == 1: return out(cs[0])

		it = 0
		while True:
			c1 = choice(cs)

			g2.copyFrom(g)
			g2.play(c1)

			acs2 = g2.actionSpace()
			cs2 = reasonableMoves(g2, g3, moves=acs2)

			c2 = choice(cs2 or acs2)
			g2.play(c2)

			while not g2.winner:
				g2.play(choice(g2.actionSpace()))

			totals[c1] += 1
			wins[c1] += (g2.winner == me)

			it += 1
			if it & (32 - 1) == 0 and timer() - start > timeout:
				dt = timer() - start
				if verbose: print('%d rollouts in %.3fs (~%.3f rol/s; ~%.3f turns ahead)' % (it, dt, it/dt, math.log(it, len(cs))))
				break

		scores = {c: wins[c] / totals[c] for c in cs}
		if verbose: print('{' + ', '.join('%d: %.2f%%' % (k, v * 100) for k, v in sorted(scores.items(), key=lambda t: -t[1])) + '}')
		if verbose: print('Win prob: %.2f%%' % (max(scores.values()) * 100))
		return out(max(scores, key=scores.get))

	return f

g = Game()
mode = 'play'
if len(sys.argv) > 1:
	mode = sys.argv[1]


if mode == 'play':
	timeout = 2.0
	# players = {1: mcs(timeout=timeout), 2: human()}
	players = {1: mcs(timeout=5.0), 2: mcs(timeout=5.0)}
	# players = {1: smartNoise(), 2: smartNoise()}
	if len(sys.argv) > 2 and sys.argv[2] == 'human':
		players = {1: human(), 2: mcs(timeout=timeout)}

	while not g.winner:
		print(g)
		print()
		print(g.P[g.p], end=' ')
		mv = players[g.p](g)
		if not g.canPlay(mv):
			continue
		g.play(mv)
		print()
	print(g)


elif mode == 'stats':
	wins = {1: 0, 2: 0, 3: 0}
	if len(sys.argv) > 2:
		wins[1] = int(sys.argv[2])
	if len(sys.argv) > 3:
		wins[2] = int(sys.argv[3])
	if len(sys.argv) > 4:
		wins[3] = int(sys.argv[4])

	timeout = 10.0
	players = {1: mcs(timeout=timeout, verbose=False), 2: mcs(timeout=timeout, verbose=False)}

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


elif mode == 'replay':
	moves = list(map(int, sys.argv[2]))

	print('Replaying with %s' % moves)
	print(g)

	for mv in moves:
		g.play(mv)
		print(g)
