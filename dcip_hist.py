# Script to analyse the distribution of holders for the dcip token
# Author: Marcelo Cordova (cordova.mm@gmail.com)
# Date: 2022/01/02

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

# Read the holders list downloaded from bscscan
d = pd.read_csv('dcip_holders_2022.01.02.csv')
d.sort_values('Balance', ascending=False, inplace=True)

# The following is the list of addresses we don't want to include in the analysis
rem_addresses = ['0x0000000000000000000000000000000299792458', # burn
			'0xa198f09c8bdec0a70e6992083e71a7c97f7500b5', # owner
			'0x8d662ddc4234b578114adfb581b64e257d038a45', # investment wallet
			'0xe4e79248c36b6cb3670f63a39017efc60f0f80d9', # marketing
			'0x4799b0d36b421df620dafebde3ba19c2c2c2fc5c', # pancake pair
			'0x10ed43c718714eb63d5aa57b78b54704e256024e', # pancake router
			]

# Remove these lines from the dataframe
for l in rem_addresses:
	i = d.loc[d['HolderAddress'] == l,:].index
	d.drop(i, inplace=True)

# Now let's define dcip price and the threshold we'll consider to decide if a wallet is a holder or a ghost
price = 0.0000000128754 # as of 2022/01/02 12:41 (utc-3)
threshold_usd = 10
threshold_dcip = threshold_usd/price

# To simplify, let's add a column with the balance in usd for each wallet
d['Balance (usd)'] = d['Balance']*price

# Define a query to remove wallets below the threshold
q = f'`Balance (usd)` >= {threshold_usd}'
df = d.query(q)


print('Division between real holders and ghosts')
ranges = [[0,10], [10,1000000]]
for r in ranges:
	q = f'(`Balance (usd)` >= {r[0]}) and (`Balance (usd)` < {r[1]})'
	dcurr = d.query(q)
	print(f'Number of holders between {r[0]} and {r[1]} usd: {len(dcurr)} ({100*len(dcurr)/len(d):.2f}%)')
print('')

# Plotting

# Histogram (only holders above threshold)
bins = np.logspace(1, 6, 50)
fig, ax = plt.subplots(figsize=(10,6))
df.hist(column='Balance (usd)', bins=bins, ax=ax)
ax = plt.gca()
ax.set_yscale('log')
ax.set_xscale('log')
ax.set_xlabel('Balance (usd)')
ax.set_ylabel('Number of holders')
ax.set_xlim(10, 1e6)
ax.set_ylim(.5, 1e3)
ax.set_yticks([1, 2, 5, 10, 25, 50, 100, 250, 500])
ax.set_yticklabels([1, 2, 5, 10, 25, 50, 100, 250, 500])
ax.set_xticks([10, 100, 1e3, 10e3, 100e3, 1e6])
ax.set_xticklabels(['10','100', '1,000', '10,000', '100,000', '1,000,000'])
fig.tight_layout()
fig.savefig('hist_dcip_above_threshold.png', dpi=200)

# Histogram (including holders below threshold)
bins = np.logspace(-4, 6, 100)
fig, ax = plt.subplots(figsize=(10,6))
d.hist(column='Balance (usd)', bins=bins, ax=ax)
ax = plt.gca()
ax.set_yscale('log')
ax.set_xscale('log')

ax.set_xlabel('Balance (usd)')
ax.set_ylabel('Number of holders')
ax.set_xlim(1e-4, 1e6)
ax.set_ylim(.5, 1e3)
ax.set_yticks(		[1, 2, 5, 10, 25, 50, 100, 250, 500, 1000])
ax.set_yticklabels(	[1, 2, 5, 10, 25, 50, 100, 250, 500, 1000])
ax.set_xticks([1e-4, 1e-3, 1e-2, 1e-1, 1, 10, 100, 1e3, 10e3, 100e3, 1e6])
ax.set_xticklabels(['0.0001', '0.001', '0.01', '0.1', '1', '10','100', '1,000', '10,000', '100,000', '1,000,000'])

# Add rectangle for the area below threshold
rect = mpatches.Rectangle((1e-4, .5), 10, 1000, facecolor='brown', alpha=0.5)
ax.add_patch(rect)

fig.tight_layout()
fig.savefig('hist_dcip_complete.png', dpi=200)




# Pie plot
ranges = [	[0, 0.01], 
			[0.01, 1], 
			[1,10], 
			[10,100], 
			[100, 1000], 
			[1000, 10000], 
			[10000, 100000], 
			[100000, 1000000]
		]

# I tried doing a small hack so that all wedges below the threshold are red tinted,
# and all wedges above threshold are blue tinted
# It's an ugly hack, I just keep decreasing the alpha for each wedge. But it works
color_ok = 'teal'
color_ghost = 'brown'
colors = {}
last_blue = 0.1
last_red = 0.1

holders_range = {}
print('Number of holders for different ranges')
for r in ranges:
	# Query similar to what I've done above, but here I select only a range
	q = f'(`Balance (usd)` >= {r[0]}) and (`Balance (usd)` < {r[1]})'
	dcurr = d.query(q) 
	
	valcurr = len(dcurr) # number of holders in that range
	pctcurr = 100*valcurr/len(d) # percentage
	labelcurr = f'{r[0]}-{r[1]} usd ({pctcurr:.2f}%)'
	holders_range[labelcurr] = valcurr

	# Here is the color hack
	if r[1] > threshold_usd:
		colors[labelcurr] = list(mpl.colors.to_rgba(color_ok))
		colors[labelcurr][3] -= last_blue
		last_blue += 0.1
	else:
		colors[labelcurr] = list(mpl.colors.to_rgba(color_ghost))
		colors[labelcurr][3] -= last_red
		last_red += 0.1
	print(f'Number of holders between {r[0]} and {r[1]} usd: {valcurr} ({pctcurr:.2f}%)')

fig, ax = plt.subplots(figsize=(6,6))
ax.pie(holders_range.values(), labels=holders_range.keys(), colors=colors.values(), counterclock=True, labeldistance=None, startangle=90)
fig.legend(loc='center right', bbox_to_anchor=(1,0.5))
fig.savefig('pie_dcip.png')



