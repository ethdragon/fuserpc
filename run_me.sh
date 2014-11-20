#!/bin/bash
# by Yang LIU
fuserpc="fuserpc.py"
proxy="Proxy.py"
mount_point="fusemount"
start_port=2222
server_number=3
file_size=10000 # Do not change this value
manual=0

killports() {
	echo "Killing ports"
	sleep 1
	for ((i=0; i<server_number; i++))
	do
		((port=$start_port+$i))
		kill -TERM $(netstat -tlnp 2> /dev/null | grep $port | awk '{print $7}' | grep -Eo "[0-9]+")
	done
	sleep 1
	netstat -ntlp
}

USAGE="-p [port number the first server will listen]\n-n [number of
servers]\n-h  help\n-m  manual test\n-k  kill ports that from start_port
to start_port+ server_number"
while getopts "p:n:hmk" OPTIONS
do
  case $OPTIONS in
    p ) start_port=$OPTARG;;
    n ) server_number=$OPTARG;;
    h ) echo -e $USAGE; exit;;
	m ) manual=1;;
	k ) killports; exit;;
    \? ) echo -e $usage; exit 1;;
	: ) echo -e $usage; exit 1;;
	* ) echo -e $usage; exit 1;;
  esac
done

if ((server_number < 2))
then
	echo "Please start no less than 2 servers!"
	exit
fi

if [ ! -f simpleht.py ]
then
    echo "simpleht.py not found"
    exit 1
fi

if [ ! -f fuse.py ]
then
	echo "fuse.py not found"
	exit 1
fi

if [ ! -d $mount_point ]
then
    echo "director $mount_point created"
    mkdir $mount_point
fi

if [ ! -f $fuserpc ]
then
	echo "$fuserpc not found"
	exit 1
fi

if [ ! -f $proxy ]
then
	echo "$proxy not found"
	exit
fi

echo "Starting simpleht.py"
for ((i=0; i<$server_number-1; i++))
do
	((port = $start_port+$i))
	((nport = $port+1))
	python simpleht.py --port $port --addr http://localhost:$nport &> zout_$port.txt &
done
((port = $nport))
((nport = $start_port))
python simpleht.py --port $port --addr http://localhost:$nport &> zout_$port.txt &

# wait for all port listener starts
sleep 2
netstat -ntlp

echo "Starting $fuserpc"
arg1=""
for ((i=0; i<$server_number; i++))
do
    ((port = $start_port+$i))
    arg1="$arg1 http://localhost:$port "
done

python $fuserpc $mount_point $arg1 &> zout_fuse.txt &

if ((manual == 1))
then
	echo -e "\nWarning: simpleht.py running at background!\nfuse mounted, you need to umount manual!"
	exit
fi

sleep 2

if [ ! -d proj_test_file ]
then
    echo "director proj_test_file created"
    mkdir proj_test_file
    cd proj_test_file
	echo "Creating file for test"
	((end=$file_size/40))
	for ((i=0; i<$end; i++))
	do
    	openssl rand -hex 20 >> 10K.file
	done
	cat * * > 20K.file
	cat 1* 2* > 30K.file
	cat 2* 2* > 40K.file
	cat 2* 3* > 50K.file
	cat 3* 3* > 60K.file
	cat 3* 4* > 70K.file
	cat 4* 4* > 80K.file
	cat 4* 5* > 90K.file
	cat 5* 5* > 100K.file
	cat 100* 100* > 200K.file
	cat 100* 200* > 300K.file
	cat 200* 200* > 400K.file
	cat 200* 300* > 500K.file
	cat 300* 300* > 600K.file
	cat 300* 400* > 700K.file
	cat 400* 400* > 800K.file
	cat 400* 500* > 900K.file
	cat 500* 500* > 1000K.file
	cd ..
fi

echo "Start testing"
cd $mount_point
ls -l
echo "=== cp ../simpleht.py . ==="
cp ../simpleht.py . 
ls -l
echo "=== cp ../proj_test_file/* . ==="
time1=$(date +"%s")
cp ../proj_test_file/* .
time2=$(date +"%s")
((gap=$time2-$time1))
echo "Time elapse: $gap"
ls -l
echo "=== cat 10K.file simpleht.py > test.py ==="
cat 10K.file simpleht.py > test.py
ls -l
echo "=== ln -s test.py sym_test.py ==="
ln -s test.py sym_test.py
ls -l
echo "=== chmod 755 test.py ==="
chmod 755 test.py
ls -l
echo "=== chown 1000 test.py ==="
chown 1000 test.py
ls -l
echo "=== head sym_test.py ==="
head test.py
ls -l
echo "=== tail sym_test.py ==="
tail test.py
ls -l
echo "=== mv 10K.file a10K.file ==="
mv 10K.file a10K.file
ls -l
echo "=== head a10K.file ==="
head a10K.file
ls -l
echo "=== tail a10K.file ==="
tail a10K.file
ls -l
echo "=== rm sym_test.py ==="
rm sym_test.py
ls -l --full-time
echo "=== touch test.py ==="
touch test.py
ls -l --full-time
echo "===rm *===="
rm *.*

cd ..
echo "fusermount -u $mount_point"
sleep 1
fusermount -u $mount_point

killports