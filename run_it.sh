echo -en "\007"
date
date > test.txt
sleep 1
echo "before python" >> test.txt
echo "before python"
python3 /home/hugo/MEGA/scripts/get_connection_statistics/analyze_internet_connection.py blah
exit_code=$?
echo "exit code $exit_code" >> test.txt
echo "after python" >> test.txt
echo "after python"
