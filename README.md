# A decentralized, scalable peer-to-peer video sharing platform to achieve efficient live-streaming.


- We have implemented a peer-to-peer network architecture to overcome the common problems of server-failure and overloading in the client server model. **The project mainly focusses on scalability and achieving minimum source to end delay with playback continuity in live streaming.** 
- The video file from the sender side is sent in chunks of 2048 bytes to the peer requesting it instantly. At the receiver side, the content is simultaneously buffered and starts streaming for which we have made use of python-vlc.
- Currently, to locate a file, the client needs to go through the network of all the peers to find whether a file is present or not. To avoid this, the backend of central tracker is implemented which will keep a list of ip addresses ***vs*** files stored by all the users present in the network. 
- Now, instead of going to each peer to check for the file, the tracker can be used to get the users who have the requested file, and download the files simultaneously from them.

### Usage
```
python main.py <server-port> <max-peers> <peer-ip>:<peer-port>

server-port : Port to listen for incoming requests.
max-peers : Max number of peers you wish to have in the swarm.
peer-ip/peer-port: IP address/port of any existing peer in the swarm (known beforehand).
```

### Future Prospects
- Along with live streaming, the video file also gets downloaded. A better option could be to have the video being played directly without having any download space requirements, i.e. as the chunk is played, it gets deleted for the next chunk to be recieved at the same location.
- The implementation is in python (an interpreter). Converting the code into a compiler oriented language like C++ may improve the performance.

### References
- Computer Networks: A Top-down Approach by Behrouz A. Forouzan
- [Peerflix - Streaming torrent client for Node.js](https://github.com/mafintosh/peerflix)
- https://perso.telecom-paristech.fr/drossi/paper/rossi13p2p-b.pdf
- [Python VLC](https://pypi.org/project/python-vlc/)

### Contributors
- [Aniket Singh](https://github.com/aniketsingh03)
- [Harshal Mittal](https://github.com/harshalmittal4)
- [Harshit Bansal](https://github.com/harshitbansal05)
- [Vishal Sharma](https://github.com/VishalCR7)