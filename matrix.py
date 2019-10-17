import math


class Vector3D:
	def __init__(self, x=0.0, y=0.0, z=0.0):
		self.x = x
		self.y = y
		self.z = z

	def __str__(self):
		return '[%f, %f, %f]' % (self.x, self.y, self.z)

	def magnitude(self):
		return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z)

	def __add__(self, v):
		if isinstance(v, Vector3D):
			return Vector3D(self.x+v.x, self.y+v.y, self.z+v.z)
		else:
			raise Exception('*** Vector3D: error, add not with a vector! ***')

	def __sub__(self, v):
		if isinstance(v, Vector3D):
			return Vector3D(self.x-v.x, self.y-v.y, self.z-v.z)
		else:
			raise Exception('*** Vector3D: error, sub not with a vector! ***')

	def __neg__(self):
		return Vector3D(-self.x, -self.y, -self.z)
	
	def __mul__(self, val):
		if isinstance(val, int) or isinstance(val, float):
			return Vector3D(self.x*val, self.y*val, self.z*val)
		elif isinstance(val, Vector3D):
			return Vector3D(self.x*val.x, self.y*val.y, self.z*val.z)
		else:
			raise Exception('*** Vector3D: error, multiplication with not vector, int or float! ***')

	def __div__(self, val):
		if isinstance(val, int) or isinstance(val, float):
			if (val): 
				return Vector3D(self.x/val, self.y/val, self.z/val)
			else:
				raise Exception('*** Vector: error, divison with zero! ***')
		elif isinstance(val, Vector3D):
			if (val.x and val.y and val.z): 
				return Vector3D(self.x/val.x, self.y/val.y, self.z/val.z)
			else:
				raise Exception('*** Vector: error, divison with zero vector coord! ***')
		else:
			raise Exception('*** Vector: error, divison with not vector, int or float! ***')

		#	def __rmul__(self, other): #__mul__ is called in case of vector*int but in case of int*vector __rmul__ is called

	def normalize(self):
		mag = self.magnitude()
		if (mag > 0.0):
#			Vector3D.__mul__(self, 1/mag)
			self.x /= mag
			self.y /= mag
			self.z /= mag
		else:
			raise Exception('*** Vector: error, normalizing zero vector! ***')

	def dot(self, v): #dot product
		if isinstance(v, Vector3D):
			return self.x*v.x+self.y*v.y+self.z*v.z
		else:
			raise Exception('*** Vector: error, dot product not with a vector! ***')

	def cross(self, v): #cross product
		if isinstance(v, Vector3D):
			return Vector3D(self.y*v.z-self.z*v.y, self.z*v.x-self.x*v.z, self.x*v.y-self.y*v.x)
		else:
			raise Exception('*** Vector: error, cross product not with a vector! ***')


#The layout of the matrix (row- or column-major) matters only when the user reads from or writes to the matrix (indexing). For example in the multiplication function we know that the first components of the Matrix-vectors need to be multiplied by the vector. The memory-layout is not important
class Matrix:
	''' Column-major order '''

	def __init__(self, rows, cols, createidentity=True):# (2,2) creates a 2*2 Matrix
		if rows < 2 or cols < 2:
			raise Exception('*** Matrix: error, getitem((row, col)), row, col problem! ***')
		self.rows = rows
		self.cols = cols
		self.m = [[0.0]*rows for x in range(cols)]

		#If quadratic matrix then create identity one
		if self.isQuadratic() and createidentity:
			for i in range(self.rows):
				self.m[i][i] = 1.0

	def __str__(self):
		s = ''
		for row in self.m:
			s += '%s\n' % row

		return s

	def isQuadratic(self):
		return self.rows == self.cols

	def copy(self):
		r = Matrix(self.rows, self.cols, False)
		for i in range(self.rows):
			for j in range(self.cols):
				r.m[i][j] = self.m[i][j]
		return r

	def __getitem__(self, location):
		''' The value at (row, col) 
		For example, to get the element at 1,3 say
				m[(1,2)]'''
		row, col = location
		if self.rows > row and self.cols > col:
			return self.m[row][col]
		else:
			raise Exception('*** Matrix: error, getitem((row, col)), row, col problem! ***')

	def __setitem__(self, location, val):
		''' Sets the value at (row, col) 
		For example, to set the value of element at 1,3 say
				m[(1,2)] = 3 '''
		row, col = location

		if self.rows > row and self.cols > col:
			self.m[row][col] = val
		else:
			raise Exception('*** Matrix: error, setitem((row, col), val), row, col problem! ***')

	def rowsNum(self):
		return len(self.m)

	def colsNum(self):
		return len(self.m[0])

	def getRow(self, i):
		if i < self.rows:
			return self.m[i]
		else:
			raise Exception('*** Matrix: error, row(i), i > number of rows! ***')

	def getCol(self, j):
		if j < self.cols:
			return [row[j] for row in self.m] #(returns array of the vector)
		else:
			raise Exception('*** Matrix: error, col(j), j > columns! ***')

#	def setColumn(self, j, v):
#		if j < self.cols:
#			self.m[0][j] = v.x
#			self.m[1][j] = v.y
#			self.m[2][j] = v.z
#		else:
#			raise Exception('*** Matrix: error, setColumn(j, v), j > columns! ***')

	def __add__(self, right):
		if self.rows == right.rows and self.cols == right.cols:
			r = Matrix(self.rows, self.cols, False)
			for i in range(self.rows):
				for j in range(self.cols):
					r.m[i][j] = self.m[i][j]+right.m[i][j]
			return r
		else:
			raise Exception('*** Matrix: error, add() matrices are not of the same type ***')

	def __sub__(self, right):
		if self.rows == right.rows and self.cols == right.cols:
			r = Matrix(self.rows, self.cols, False)
			for i in range(self.rows):
				for j in range(self.cols):
					r.m[i][j] = self.m[i][j]-right.m[i][j]
			return r
		else:
			raise Exception('*** Matrix: error, sub() matrices are not of the same type ***')

	def __mul__(self, right):
		if isinstance(right, Matrix):
			if self.cols == right.rows:
				r = Matrix(self.rows, right.cols, False)
				for i in range(self.rows):
					for j in range(right.cols):
						for k in range(self.cols):
							r.m[i][j] += self.m[i][k]*right.m[k][j]
				return r
			else:
				raise Exception('*** Matrix: error, matrix multiplication with incompatible matrix! ***')
		elif isinstance(right, Vector3D): #Translation: the last column of the matrix. Remains unchanged due to the the fourth coord of the vector (1).
#			if self.cols == 4:
			r = Vector3D()
			addx = addy = addz = 0.0
			if self.rows == self.cols == 4:
				addx = self.m[0][3]
				addy = self.m[1][3]
				addz = self.m[2][3]
			r.x = self.m[0][0]*right.x+self.m[0][1]*right.y+self.m[0][2]*right.z+addx
			r.y = self.m[1][0]*right.x+self.m[1][1]*right.y+self.m[1][2]*right.z+addy
			r.z = self.m[2][0]*right.x+self.m[2][1]*right.y+self.m[2][2]*right.z+addz

			#In 3D game programming we use homogenous coordinates instead of cartesian ones in case of Vectors in order to be able to use them with a 4*4 Matrix. The 4th coord (w) is not included in the Vector-class but gets computed on the fly
			if self.rows == self.cols == 4:
				w = self.m[3][0]*right.x+self.m[3][1]*right.y+self.m[3][2]*right.z+self.m[3][3]
				if (w != 1 and w != 0):
					r.x = r.x/w;
					r.y = r.y/w;
					r.z = r.z/w;
			return r
#			else:
#				raise Exception('*** Matrix: error, matrix multiplication with incompatible vector! ***')
		elif isinstance(right, int) or isinstance(right, float):
			r = Matrix(self.rows, self.cols, False)
			for i in range(self.rows):
				for j in range(self.cols):
					r.m[i][j] = self.m[i][j]*right
			return r
		else:
			raise Exception('*** Matrix: error, matrix multiply with not matrix, vector or int or float! ***')

	def __div__(self, right):
		if isinstance(right, int) or isinstance(right, float):
			r = Matrix(self.rows, self.cols, False)
			for i in range(self.rows):
				for j in range(self.cols):
					r.m[i][j] = self.m[i][j]/right
			return r
		else:
			raise Exception('*** Matrix: error, matrix division with not int or float! ***')

	def transpose(self):
		t = Matrix(self.cols, self.rows, False)
		for j in range(self.cols):
			for i in range(self.rows):
				t.m[j][i] = self.m[i][j]

		return t

#For Quadratic Matrices:
#isSymetric(): A=Atransposed
#isNormal(): Atransposed*A = A*Atransposed

	def det(self):#Only for quadratic matrices
		if not self.isQuadratic():
			raise Exception('*** Matrix: error, determinant of non-quadratic matrix! ***')
		if self.rows == 2:
			return self.m[0][0]*self.m[1][1]-self.m[0][1]*self.m[1][0]

		return self.expandByMinorsOnRow(0)

	def expandByMinorsOnRow(self, row):#used by det()
		assert(row < self.rows)
		d = 0
		for col in xrange(self.cols):
			d += (-1)**(row+col)*self.m[row][col]*self.minor(row, col).det()

		return d

	def expandByMinorsOnCol(self, col):#used by det()
		assert(col < self.cols)
		d = 0
		for row in xrange(self.rows):
			d += (-1)**(row+col)*self.m[row][col]*self.minor(row, col).det()

		return d

	def minor(self, i, j): #used by det()
		''' A minor of the matrix. Return the minor given by 
			striking out row i and column j of the matrix '''

		if i < 0 or i >= self.rows:
			raise Exception('*** Matrix: error, Determinant-row value is out of range! ***')
		if j < 0 or j >= self.cols:
			raise Exception('*** Matrix: error, Determinant-col value is out of range! ***')
		mat = Matrix(self.rows-1, self.cols-1)
		#Loop through the matrix, skipping over the row and column specified
		#by i and j
		minor_row = minor_col = 0
		for self_row in xrange(self.rows):
			if not self_row == i: #skip row i
				for self_col in xrange(self.cols):
					if not self_col == j: #Skip column j
						mat.m[minor_row][minor_col] = self.m[self_row][self_col]
						minor_col += 1

				minor_col = 0
				minor_row += 1

		return mat

	def invert(self): 
		if not self.isQuadratic():
			raise Exception('*** Matrix: error, determinant of non-quadratic matrix! ***')
		else:
			N = self.cols
			mat = Matrix(N, N)
			mo = self.copy()
			for column in range(N):
				# Swap row in case our pivot point is not working
				if (mo.m[column][column] == 0):
					big = column
					for row in range(N):
						if (math.fabs(mo.m[row][column]) > math.fabs(mo.m[big][column])):
							big = row
					# Print this is a singular matrix, return identity ?
					if (big == column):
						print("Singular matrix\n") #To stderr
					# Swap rows                               
					else: 
						for j in range(N):
							mo.m[column][j], mo.m[big][j] = mo.m[big][j], mo.m[column][j]
							mat.m[column][j], mat.m[big][j] = mat.m[big][j], mat.m[column][j] 

				#Set each row in the column to 0  
				for row in range(N):
					if (row != column):
						coeff = mo.m[row][column]/mo.m[column][column]
						if (coeff != 0):
							for j in range(N):
								mo.m[row][j] -= coeff*mo.m[column][j]
								mat.m[row][j] -= coeff*mat.m[column][j]

							#Set the element to 0 for safety
							mo.m[row][column] = 0

			# Set each element of the diagonal to 1
			for row in range(N):
				for column in range(N):
					mat.m[row][column] /= mo.m[row][row]

			return mat


if __name__ == "__main__":
	m1 = Matrix(3, 3)
	m1[(0,0)] = 1
	m1[(0,1)] = 6
	m1[(0,2)] = 8
	m1[(1,0)] = 2
	m1[(1,1)] = 5
	m1[(1,2)] = 7
	m1[(2,0)] = 3
	m1[(2,1)] = 4
	m1[(2,2)] = 9
	m2 = Matrix(3, 3)
	m2[(0,0)] = 5
	m2[(0,1)] = 8
	m2[(0,2)] = 1
	m2[(1,0)] = 6
	m2[(1,1)] = 1
	m2[(1,2)] = 4
	m2[(2,0)] = 3
	m2[(2,1)] = 2
	m2[(2,2)] = 7

	m = m1*m2
	print(str(m))





