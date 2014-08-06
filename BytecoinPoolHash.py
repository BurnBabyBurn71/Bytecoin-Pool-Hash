#!/usr/bin/env python
import requests
import json
import re
import datetime
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
 
 
# Get time and make string for title
utc = datetime.datetime.utcnow() 
utc_string = utc.strftime("%Y-%m-%d %H:%M:%S")
 
# Define regular pool list
server_dict = {
        'moneropool.com': 'http://api.moneropool.com:8080/live_stats',
        'moneropool.org': 'http://192.99.44.150:8117/live_stats',
        'minexmr.com': 'http://pool.minexmr.com:8117/live_stats',
        'cryptonotepool.org.uk': 'http://80.71.13.55:8117/live_stats',
        'hashinvest.net': 'http://xmr.hashinvest.net:8117/live_stats',
        'extremehash.com': 'http://xmr.extremehash.com:8117/live_stats',
        'monero.kippo.eu': 'http://monero.kippo.eu:8117/live_stats',
        'mro.extremepool.org': 'http://mro.extremepool.org:8117/live_stats',
        'monero.crypto-pool.fr': 'http://xmr.crypto-pool.fr:8090/live_stats',
        'xmr.poolto.be': 'http://mro.poolto.be:8117/live_stats',
        'xmr.farm': 'http://xmr.farm:8117/live_stats',
        'pool.cryptograben.com': 'http://xmr.cryptograben.com:8117/live_stats',
        'www2.coinmine.pl': 'http://mine1.coinmine.pl:8117/live_stats',
        'moneropool.ru': 'http://mine.moneropool.ru:8117/live_stats',
        'xmr.alimabi.cn': 'http://xmrapi.alimabi.cn:80/live_stats',
        'nomp.freeyy.me': 'http://nomp.freeyy.me:8117/live_stats'
        }
 
hashrate_list = []  #List of pool hashrates
name_list = []  #Ordered (to match hashrate) list of pool names
 
# Connect to each server and get pool hashrate
for key, val in server_dict.items():
    try: 
        resp = requests.get(val)
        output = json.loads(resp.text)
        name_list.append(key)
        hashrate_list.append(float(output[u'pool'][u'hashrate'])/1e6)
    except:
        print(key + " did not respond")
# Use last pool connects data to calculate network hashrate from diff
network_hash = float(output[u'network'][u'difficulty'])/60e6
 
# Begin hack for dwarfpool
dwarf_url = 'http://dwarfpool.com/'
resp = requests.get(dwarf_url)
lines = resp.text.encode("utf-8").split('\n')
target_line = -1
# Find XMR pool data and then grab hashrate
for line_number, line in enumerate(lines):
	if "Code: XMR" in line:
		target_line = line_number + 3
	if line_number == target_line:
		name_list.append('dwarfpool.com')
		hashrate_list.append(float(re.sub("[^0-9.]", "", line))/1e3)
 
# Calculate unknown hash
known_hash = sum(hashrate_list)
unknown_hash = network_hash - known_hash
print("Unkown hash = {0}".format(unknown_hash))
if unknown_hash < 0:
    unknown_hash = abs(unknown_hash)
    print("WARNING - negative nethash")
name_list.append('Unknown/Minergate')
hashrate_list.append(unknown_hash)
 
 
# Calculate normalized hash rates
normalized_list = [x/network_hash for x in hashrate_list]
 
# Setup lists
smallpools_names = []
smallpools_hash = []
smallpools_normhash = []
 
majorpools_names = []
majorpools_hash = []
majorpools_normhash = []
 
smalllabellist = []
majorlabellist = []
 
# Print pools and separate to small or major
print("Total network hash = " + str(network_hash))
for idx, val in enumerate(hashrate_list):
	print(name_list[idx], val)
	if normalized_list[idx] < 0.035:
		smallpools_names.append(name_list[idx])
		smallpools_hash.append(val)
		smallpools_normhash.append(normalized_list[idx])
		smalllabellist.append("{0}\n{1:.3f} Mh/s".format(
						 name_list[idx], val))
	else:
		majorpools_names.append(name_list[idx])
		majorpools_hash.append(val)
		majorpools_normhash.append(normalized_list[idx])		
		majorlabellist.append("{0}\n{1:.2f} Mh/s".format(
						 name_list[idx], val))
 
# Make normalized small hash for plot                         
smallpool_hashtotal = sum(smallpools_hash)
smallpool_normtotal = smallpool_hashtotal/network_hash
smallpool_smallnorm = [x/smallpool_hashtotal for x in smallpools_hash]
 
# Add small pool total to major pools
majorpools_names.append('Small pools (<3.5%)')
majorpools_hash.append(smallpool_hashtotal)
majorpools_normhash.append(smallpool_normtotal)
majorlabellist.append("{0}\n{1:.2f} Mh/s".format(
				 'Small pools', smallpool_hashtotal))
 
# Make color list                 
colors = ('b', 'g', 'r', 'c', 'm', 'y', 'w', 'DeepPink', 'ForestGreen')
                 
#Plot and save major pools                 
plt.figure(1, figsize=(12,10))
ax = plt.axes([0.15, 0.15, 0.75, 0.75])
pie_wedge_collection = ax.pie(majorpools_normhash, 
    explode=[0.07]*len(majorlabellist), 
    labels=majorlabellist, 
    labeldistance=1.07,
    autopct='%1.0f%%', 
    shadow=True, 
    startangle=90, 
    colors=colors)
for pie_wedge in pie_wedge_collection[0]:
    pie_wedge.set_edgecolor('0.3')
plt.title('Monero network hashrate: {0:.1f} Mh/s\nTime recorded:{1}'.format(network_hash, utc_string))
plt.savefig('bigpools.png')
plt.close()
 
# Reorder slices to try and accomodate tiny pools
tmp_norm, tmp_names = (list(t) for t in zip(*sorted(zip(smallpool_smallnorm, smalllabellist))))
large = tmp_norm[:len(tmp_norm) / 2]
small = tmp_norm[len(tmp_norm) / 2:]
reordered = large[::2] + small[::2] + large[1::2] + small[1::2]
 
# Plot and save minor pool figure
plt.figure(2, figsize=(12,10))  
ax = plt.axes([0.15, 0.15, 0.65, 0.65])
ax.pie(smallpool_smallnorm, 
#    explode=[0.08]*len(smalllabellist), 
    explode=[0.023*(1/z**0.4) for z in smallpool_smallnorm], 
    labels=smalllabellist,
    labeldistance=1.06,
    autopct='%1.1f%%', 
    shadow=True, 
#    startangle=90, 
    colors=colors)
plt.title('Monero smaller pools (<3.5%)\nSmall pool hash: {0:.1f} Mh/s'.format(smallpool_hashtotal))
plt.savefig('smallpools.png')
plt.close()
