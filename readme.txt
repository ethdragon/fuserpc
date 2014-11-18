This project is done by Yang Liu, Ruimin Sun and Risheng Wang. All contribute equally.

This is introduction to the run_me.sh script that is used to test our fuserpc implementation.
The test script has several flag that can be used for different test purpose.
-p is used to set the port that the first server will listen to, the following server will 
   listen to the next port in nature order. The default port is set to 2222. In this case
   the next started server will listen to 2223 and the next will listen to 2224 and so on
   so forth. 
-n is used to indicate how many servers that should be set up. The default number of servers
   is set to 3. For the fault tolerance design, n is not allow to set to any numbers that is
   smaller than 2.
-m is used for manual tests. With is flag on, the script will set up the servers according to
   the -p and -n flag and mounted to the whole file system. Then you can use command line or
   a gui to access the file system.
-k this flag will kill all the servers listening to the port according to the -n -p flag
-h show help information

example use case:
./run_me.sh -n 4 -p 3000
This will start 4 servers listening to 3000 3001 3002 and 3003. The auto test will create
several files ranging from 10K-100K, 100K-1000K. Script will automatically do copy, paste,
symbolic links, head, tail and so on.

./run_me.sh -n 4 -p 3000 -m
This will automatically deploy and mounted the system, but will not do any test. You can
use command line or GUI to interact with the file system.

./run_me.sh -n 4 -p 3000 -k
This will clear the server deployment, but before doing this you have to manually umount
the file system.