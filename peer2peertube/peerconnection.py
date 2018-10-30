#!/usr/bin/python

import socket
import struct
import threading
import time
import traceback
import os
import vlc

def debug( msg ):
	""" Prints a messsage to the screen with the name of the current thread 
	"""
	
	print "[%s] %s" % ( str(threading.currentThread().getName()), msg )


class Peer:
	""" Implements the core functionality that might be used by a peer in a
	P2P network.
	"""

	def __init__( self, maxpeers, serverport, myid=None, serverhost = None ):
		""" Initializes a peer servent (sic.) with the ability to catalog
		information for up to maxpeers number of peers (maxpeers may
		be set to 0 to allow unlimited number of peers), listening on
		a given server port , with a given canonical peer name (id)
		and host address. If not supplied, the host address
		(serverhost) will be determined by attempting to connect to an
		Internet host like Google.
		"""

		self.debug = 1

		self.maxpeers = int(maxpeers)
		self.serverport = int(serverport)
		if serverhost: self.serverhost = serverhost
		else: self.__initserverhost()

		if myid: self.myid = myid
		else: self.myid = '%s:%d' % (self.serverhost, self.serverport)

		self.peerlock = threading.Lock()  # ensure proper access to
									# peers list (maybe better to use
									# threading.RLock (reentrant))
		self.peers = {}        # peerid ==> (host, port) mapping
		self.shutdown = False  # used to stop the main loop

		self.handlers = {}
		self.router = None


	def __initserverhost( self ):
		""" Attempt to connect to an Internet host in order to determine the
		local machine's IP address.
		"""

		s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
		s.connect( ( "www.google.com", 80 ) )
		self.serverhost = s.getsockname()[0]
		s.close()

	 
	def __debug( self, msg ):
		if self.debug:
			debug( msg )


	def __handlepeer( self, clientsock ):
		"""
		handlepeer( new socket connection ) -> ()

		Dispatches messages from the socket connection
		"""

		self.__debug( 'New child ' + str(threading.currentThread().getName()) )
		self.__debug( 'Connected ' + str(clientsock.getpeername()) )

		host, port = clientsock.getpeername()
		peerconn = PeerConnection( None, host, port, clientsock, debug=False )
		
		try:
			msgtype, msgdata = peerconn.recvdata()
			if msgtype: msgtype = msgtype.upper()
			if msgtype not in self.handlers:
				self.__debug( 'Not handled: %s: %s' % (msgtype, msgdata) )
			else:
				self.__debug( 'Handling peer msg: %s: %s' % (msgtype, msgdata) )
				self.handlers[ msgtype ]( peerconn, msgdata )
		except KeyboardInterrupt:
			raise
		except:
			if self.debug:
				traceback.print_exc()
		
		self.__debug( 'Disconnecting ' + str(clientsock.getpeername()) )
		peerconn.close()
	 
	def __runstabilizer( self, stabilizer, delay ):
		while not self.shutdown:
			stabilizer()
			time.sleep( delay )


	def setmyid( self, myid ):
		self.myid = myid


	def startstabilizer( self, stabilizer, delay ):
		""" Registers and starts a stabilizer function with this peer. 
		The function will be activated every <delay> seconds. 
		"""

		t = threading.Thread( target = self.__runstabilizer, 
					  args = [ stabilizer, delay ] )
		t.start()


	def addhandler( self, msgtype, handler ):
		""" Registers the handler for the given message type with this peer 
		"""

		assert len(msgtype) == 4
		self.handlers[ msgtype ] = handler


	def addrouter( self, router ):
		""" Registers a routing function with this peer. The setup of routing
		is as follows: This peer maintains a list of other known peers
		(in self.peers). The routing function should take the name of
		a peer (which may not necessarily be present in self.peers)
		and decide which of the known peers a message should be routed
		to next in order to (hopefully) reach the desired peer. The router
		function should return a tuple of three values: (next-peer-id, host,
		port). If the message cannot be routed, the next-peer-id should be
		None.
		"""
		self.router = router
	 
	def addpeer( self, peerid, host, port ):
		""" Adds a peer name and host:port mapping to the known list of peers.
		"""
		if peerid not in self.peers and (self.maxpeers == 0 or len(self.peers) < self.maxpeers):
			self.peers[ peerid ] = (host, int(port))
			return True
		else:
			return False


	def getpeer( self, peerid ):
		""" Returns the (host, port) tuple for the given peer name 
		"""
		assert peerid in self.peers    # maybe make this just a return NULL?
		return self.peers[ peerid ]


	def removepeer( self, peerid ):
		""" Removes peer information from the known list of peers. 
		"""
		if peerid in self.peers:
			del self.peers[ peerid ]


	def addpeerat( self, loc, peerid, host, port ):
		""" Inserts a peer's information at a specific position in the 
		list of peers. The functions addpeerat, getpeerat, and removepeerat
		should not be used concurrently with addpeer, getpeer, and/or 
		removepeer. 
		"""
		self.peers[ loc ] = (peerid, host, int(port))

	def getpeerat( self, loc ):
		if loc not in self.peers:
			return None
		return self.peers[ loc ]

	def removepeerat( self, loc ):
		removepeer( self, loc )


	def getpeerids( self ):
		""" Return a list of all known peer id's. 
		"""
		return self.peers.keys()


	def numberofpeers( self ):
		""" Return the number of known peer's. 
		"""
		return len(self.peers)


	def maxpeersreached( self ):
		""" Returns whether the maximum limit of names has been added to the
		list of known peers. Always returns True if maxpeers is set to
		0.
		"""
		assert self.maxpeers == 0 or len(self.peers) <= self.maxpeers
		return self.maxpeers > 0 and len(self.peers) == self.maxpeers


	def makeserversocket( self, port, backlog=5 ):
		""" Constructs and prepares a server socket listening on the given 
		port.
		"""
		s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
		s.setsockopt( socket.SOL_SOCKET, socket.SO_REUSEADDR, 1 )
		s.bind( ( '', port ) )
		s.listen( backlog )
		return s


	def sendtopeer( self, peerid, msgtype, msgdata, waitreply=True ):
		"""
		sendtopeer( peer id, message type, message data, wait for a reply )
		 -> [ ( reply type, reply data ), ... ] 

		Send a message to the identified peer. In order to decide how to
		send the message, the router handler for this peer will be called.
		If no router function has been registered, it will not work. The
		router function should provide the next immediate peer to whom the 
		message should be forwarded. The peer's reply, if it is expected, 
		will be returned.

		Returns None if the message could not be routed.
		"""

		if self.router:
			nextpid, host, port = self.router( peerid )
		if not self.router or not nextpid:
			self.__debug( 'Unable to route %s to %s' % (msgtype, peerid) )
			return None
		#host,port = self.peers[nextpid]
		return self.connectandsend( host, port, msgtype, msgdata,pid=nextpid,waitreply=waitreply )
		

	def connectandsend( self, host, port, msgtype, msgdata, pid=None, waitreply=True ):
		"""
		connectandsend( host, port, message type, message data, peer id,
		wait for a reply ) -> [ ( reply type, reply data ), ... ]

		Connects and sends a message to the specified host:port. The host's
		reply, if expected, will be returned as a list of tuples.
		"""
		file_recv = False
		if msgtype=="FGET":
			file_recv=True
		msgreply = []
		try:
			peerconn = PeerConnection( pid, host, port, debug=self.debug )
			peerconn.senddata( msgtype, msgdata )
			self.__debug( 'Sent %s: %s' % (pid, msgtype) )
			
			if waitreply:
				onereply = peerconn.recvdata(file_recv, msgdata)
				while (onereply != (None,None)):
					msgreply.append( onereply )
					self.__debug( 'Got reply %s: %s' 
						  % ( pid, str(msgreply) ) )
					onereply = peerconn.recvdata(file_recv, msgdata)
			peerconn.close()
		except KeyboardInterrupt:
			raise
		except:
			if self.debug:
				traceback.print_exc()
		
		return msgreply

	# end connectsend method

	def checklivepeers( self ):
		""" Attempts to ping all currently known peers in order to ensure that
		they are still active. Removes any from the peer list that do
		not reply. This function can be used as a simple stabilizer.
		"""
		todelete = []
		for pid in self.peers:
			isconnected = False
			try:
				self.__debug( 'Check live %s' % pid )
				host,port = self.peers[pid]
				peerconn = PeerConnection( pid, host, port, debug=self.debug )
				peerconn.senddata( 'PING', '' )
				isconnected = True
			except:
				todelete.append( pid )
			if isconnected: peerconn.close()

		self.peerlock.acquire()
		try:
			for pid in todelete: 
				if pid in self.peers: del self.peers[pid]
		finally:
			self.peerlock.release()


	def mainloop( self ):
		s = self.makeserversocket( self.serverport )
		s.settimeout(2)
		self.__debug( 'Server started: %s (%s:%d)'
				  % ( self.myid, self.serverhost, self.serverport ) )
		
		while not self.shutdown:
			try:
				self.__debug( 'Listening for connections...' )
				clientsock, clientaddr = s.accept()
				clientsock.settimeout(None)

				t = threading.Thread( target = self.__handlepeer,
							  args = [ clientsock ] )
				t.start()
			except KeyboardInterrupt:
				print 'KeyboardInterrupt: stopping mainloop'
				self.shutdown = True
				continue
			except:
				if self.debug:
					traceback.print_exc()
					continue

		# end while loop
		self.__debug( 'Main loop exiting' )

		s.close()


class PeerConnection:
	def __init__( self, peerid, host, port, sock=None, debug=False ):
	# any exceptions thrown upwards

		self.id = peerid
		self.debug = debug

		if not sock:
			self.s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
			self.s.connect( ( host, int(port) ) )
		else:
			self.s = sock

		self.sd = self.s.makefile( 'rw', 0 )

	 
	def __makemsg( self, msgtype, msgdata ):
		msglen = len(msgdata)
		msg = struct.pack( "!4sL%ds" % msglen, msgtype, msglen, msgdata )
		return msg


	def __debug( self, msg ):
		if self.debug:
			debug( msg )


	def senddata( self, msgtype, msgdata ):
		"""
		senddata( message type, message data ) -> boolean status

		Send a message through a peer connection. Returns True on success
		or False if there was an error.
		"""

		try:
			msg = self.__makemsg( msgtype, msgdata )
			self.sd.write( msg )
			self.sd.flush()
		except KeyboardInterrupt:
			raise
		except:
			if self.debug:
				traceback.print_exc()
			return False
		return True		

	 
	def recvdata( self, file_recv=False , fname=None):
		"""
		recvdata() -> (msgtype, msgdata)

		Receive a message from a peer connection. Returns (None, None)
		if there was any error.
		"""
		if not fname and file_recv:
			fname = os.path.join(os.getcwd(), fname)
		try:
			msgtype = self.sd.read( 4 )
			if not msgtype: return (None, None)
			
			lenstr = self.sd.read( 4 )
			msglen = int(struct.unpack( "!L", lenstr )[0])
			msg = ""
			while len(msg) != msglen:
				data = self.sd.read( min(2048, msglen - len(msg)) )
				if file_recv:
					if not os.path.isfile(fname):
						fd = open(fname, 'w')
						fd.write(data)
						fd.close()
						print 'reading data'
						vlc_instance = vlc.Instance('--fullscreen')
						player = vlc_instance.media_player_new()
						media = vlc_instance.media_new(fname)
						player.set_fullscreen(True)
						player.set_media(media)
						player.play()
					else:
						fp = open(fname, 'a')
						fp.write(data)
						fp.close()	
				
				if not len(data):
					print 'Data is none'
					break
				msg += data

			if len(msg) != msglen:
				return (None, None)

		except KeyboardInterrupt:
			raise
		except:
			if self.debug:
				traceback.print_exc()
			return (None, None)

		return ( msgtype, msg )

	 
	def close( self ):
		"""
		close()

		Close the peer connection. The send and recv methods will not work
		after this call.
		"""

		self.s.close()
		self.s = None
		self.sd = None
	 
	def __str__( self ):
		return "|%s|" % peerid
