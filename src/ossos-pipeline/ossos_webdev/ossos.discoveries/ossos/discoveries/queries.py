import sqlalchemy as sa
from ossos.overview.ossuary import OssuaryTable


class DiscoveriesQuery(object):

	def __init__(self):
		ot = OssuaryTable('discoveries')
		self.discoveries = ot.table
		self.conn = ot.conn


	def num_discoveries(self):
		it = self.discoveries
		ss = sa.select([sa.func.count(it.c.discovery_id)])
		retval = [n[0] for n in self.conn.execute(ss)][0]
		
		return retval 


	def mpc_informed(self):
		it = self.discoveries
		ss = sa.select([it.c.mpc_told])
		# CONFIRM THIS WORKS AFTER ADDING OBJECTS
		ss.append_whereclause(it.c.mpc_told == True)
		retval = [n[0] for n in self.conn.execute(ss)]  # might need to fix this

		return retval 


	def ossos_discoveries(self):
		it = self.discoveries
		cols = [it.c.discovery_id, it.c.a, it.c.e, it.c.i, it.c.q, it.c.h, 
				it.c.classification, it.c.mpc_told, it.c.discovery_im1,
				it.c.discovery_im2, it.c.discovery_im3]
		ss = sa.select(cols)

		# Confirm this formats correctly!
		retval = [n for n in self.conn.execute(ss)]  

		return retval