eventsget -
a script to fetch from Zedcloud the events stream for farther analizis.
Underneeth - is docker with zcli.
Retention period of events data on Zedcloud is quite short,
thus, events should be fetched often enough, at least daily via cron
In config files like events-ict-*-yesterday-config.txt
The main filter line is eventstemplate; it defines what type of events do we want to get for a particular report.

Requirements:
pip3 install docker
