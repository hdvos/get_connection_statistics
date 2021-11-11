# Connectionlogger

With this script I am logging my connection.
I will add an explanation on how it works later.

First the code needs some cleaning.

I added the following line to my crontab to make it collect data every 30 minutes

    */30 * * * * bash /home/hugo/MEGA/scripts/get_connection_statistics/run_it.sh > /home/hugo/MEGA/scripts/get_connection_statistics/mylog_hourly.txt
