man -k . | grep '(2)' | cut -d ' ' -f1 > syscalls
mkdir -p caps
while read p; do
  echo "-- $p --"
  man 2 $p 2>/dev/null | tr ' ' '\n' |  grep -Eho 'CAP(_[[:upper:]]+)+' | sort | uniq > caps/$p
  # echo ""
done <syscalls

# docker build -t a .
# docker run \
#     --privileged \
#     -v /lib/modules:/lib/modules:ro \
#     -it \
#     a