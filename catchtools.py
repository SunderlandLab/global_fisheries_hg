import pylab as pl
import matplotlib.pyplot as plt
import numpy as np
# from mpl_toolkits.basemap import Basemap
import pandas as pd

from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection, LineCollection
from matplotlib.patches import PathPatch
from matplotlib import cm
import shapefile

import matplotlib.gridspec as gridspec
import matplotlib.colors as mcolors
from matplotlib.colors import Normalize

# Catch categories and corresponding depth ranges
names = ['Very low', 'Low', 'Medium', 'High',
        'Albacore tuna', 'Bigeye tuna', 'Skipjack tuna', 'Yellowfin tuna', 
        'Other tunas', 'Blue marlin', 'Billfish', 'King mackerel', 
        'Pollock', 'Salmon', 'Shark_high', 'Shark_low']
depth_choices = ['0-50m', '0-200m', '0-1000m', '0-1000m',
            '0-600m', '0-1500m', '0-250m', '0-250m',
            '0-200m', '0-1000m', '0-3000m', '0-140m',
            '0-1300m', '0-250m', '0-1000m', '0-200m']

# Name translators
species_names = {'very low':'Very low','low':'Low','medium':'Medium',
                 'high':'High','albacore':'Albacore tuna','bigeye':'Bigeye tuna',
                 'skipjack':'Skipjack tuna','yellowfin':'Yellowfin tuna',
                 'other tunas':'Other tunas','blue marlin':'Blue marlin',
                 'billfish':'Billfish','king mackerel':'King mackerel',
                 'pollock':'Pollock','salmon':'Salmon','shark_high':'Shark_high',
                 'shark_low':'Shark_low'}
species_names_r = {val:key for key,val in species_names.items()}

# Empirical values (mean, min, max)
hgstats = {'Yellowfin tuna':(0.26,0.03,0.65),'Bigeye tuna':(0.55,0.11,1.15),
           'Albacore tuna':(0.3,0.03,0.5),'Very low':(0.016,0.0145,0.021),
           'Low':(0.055,0.021,0.084),'Medium':(0.145,0.085,0.24),
           'High':(0.259,0.24,0.49),'Skipjack tuna':(0.19,0.06,0.45),
           'Other tunas':(0.21,0.057,3.03),'Blue marlin':(2.34,0.19,10.52),
           'Billfish':(0.85,0.14,3.31),'King mackerel':(1.05,0.11,1.51),
           'Pollock':(0.048,0.005,0.14),'Salmon':(0.046,0.005,0.19),
           'Shark_high':(0.77,0.08,8.25),'Shark_low':(0.17,0.05,2.07)
          }

# Scaling factors for regression lower and upper bounds.
scale_lower = {'Very low': 0.011/0.016, 'Low': 0.031/0.055,
    'Medium': 0.071/0.145, 'High': 0.117/0.259}
scale_upper = {'Very low': 0.023/0.016, 'Low': 0.097/0.055,
    'Medium': 0.297/0.145, 'High': 0.573/0.259}

# Routines to spatially distribute Hg concentrations
def calc_scaling(hg,catch):
    """Calculate normalized scaling factor."""
    cwm = np.nansum(hg*catch)/np.nansum(catch)
    scaling = hg/cwm
    print(np.nansum(scaling*catch)/np.nansum(catch), 'should ~equal 1.0')
    return scaling

def get_catch_limits(hg,catch):
    """Calculate min and max where catch happens."""
    wherecatch = (catch>0) & (hg>0)
    hgwhere = hg[wherecatch]
    return np.min(hgwhere), np.max(hgwhere)

def map_hg_for_fish(fish, swdata, category_catch):
    """Spatially map Hg for fish category based on seawater Hg (swdata) and catch."""
    fmin,fmax = hgstats[fish][1:] 
    if fish not in ['Very low', 'Low', 'Medium', 'High']:
        fmin,fmax = fmin*0.95, fmax*0.95 # convert limits to mehg
    # spatial scaling limits
    mmin,mmax = get_catch_limits(swdata[fish],category_catch[species_names_r[fish]])
    # make max:min ratio equal empirical
    prescl = swdata[fish]*(fmax-fmin)/mmax+fmin
    # calculate normalized spatial scaling
    scl = calc_scaling(prescl,category_catch[species_names_r[fish]])
    cwm = hgstats[fish][0]
    
    # scale normalized spatial to empirical mean
    hgmap = scl*cwm
    mid = hgmap
    low = hgmap * scale_lower.get(fish, 1.0)
    high = hgmap * scale_upper.get(fish, 1.0)

    return mid, low, high


# Country and EEZ info
eezname_to_index = {
    'Albania' : 8 ,
    'Algeria' : 12 ,
    'American Samoa' : 16 ,
    'Angola' : 24 ,
    'Antigua & Barbuda' : 28 ,
    'Argentina' : 32 ,
    'Australia' : 36 ,
    'Macquarie Isl. (Australia)' : 37 ,
    'Lord Howe Isl. (Australia)' : 38 ,
    'Bahamas' : 44 ,
    'Bahrain' : 48 ,
    'Bangladesh' : 50 ,
    'Barbados' : 52 ,
    'Belgium' : 56 ,
    'Bermuda (UK)' : 60 ,
    'Bosnia & Herzegovina' : 70 ,
    'Bouvet Isl. (Norway)' : 74 ,
    'Brazil' : 76 ,
    'Trindade & Martim Vaz Isl. (Brazil)' : 77 ,
    'Belize' : 84 ,
    'Chagos Archipelago (UK)' : 86 ,
    'British Virgin Isl. (UK)' : 92 ,
    'Brunei Darussalam' : 96 ,
    'Bulgaria' : 100 ,
    'Myanmar' : 104 ,
    'Eritrea' : 111 ,
    'Cambodia' : 116 ,
    'Cameroon' : 120 ,
    'Cape Verde' : 132 ,
    'Cayman Isl. (UK)' : 136 ,
    'Sri Lanka' : 144 ,
    'Easter Isl. (Chile)' : 153 ,
    'Desventuradas Isl. (Chile)' : 154 ,
    'Juan Fernandez Islands (Chile)' : 155 ,
    'China' : 156 ,
    'Taiwan' : 157 ,
    'Christmas Isl. (Australia)' : 162 ,
    'Cocos (Keeling) Isl. (Australia)' : 166 ,
    'Comoros Isl.' : 174 ,
    'Mayotte (France)' : 175 ,
    'Congo, R. of' : 178 ,
    'Congo (ex-Zaire)' : 180 ,
    'Cook Islands' : 184 ,
    'Croatia' : 191 ,
    'Cuba' : 192 ,
    'Cyprus (North)' : 197 ,
    'Cyprus (South)' : 198 ,
    'Benin' : 204 ,
    'Dominica' : 212 ,
    'Dominican Republic' : 214 ,
    'Ecuador' : 218 ,
    'Galapagos Isl. (Ecuador)' : 219 ,
    'El Salvador' : 222 ,
    'Equatorial Guinea' : 226 ,
    'Estonia' : 233 ,
    'Faeroe Isl. (Denmark)' : 234 ,
    'Falkland Isl. (UK)' : 238 ,
    'South Georgia & Sandwich Isl. (UK)' : 239 ,
    'Fiji' : 242 ,
    'Mozambique Channel Isl. (France)' : 251 ,
    'Tromelin Isl. (France)' : 252 ,
    'French Guiana' : 254 ,
    'French Polynesia' : 258 ,
    'Djibouti' : 262 ,
    'Gabon' : 266 ,
    'Georgia' : 268 ,
    'Gambia' : 270 ,
    'Gaza Strip' : 274 ,
    'Germany (North Sea)' : 277 ,
    'Germany (Baltic Sea)' : 278 ,
    'Ghana' : 288 ,
    'Greece' : 300 ,
    'Greenland' : 304 ,
    'Grenada' : 308 ,
    'Guam (USA)' : 316 ,
    'Guinea' : 324 ,
    'Guyana' : 328 ,
    'Haiti' : 332 ,
    'Heard & McDonald Isl. (Australia)' : 334 ,
    'Hong Kong (China)' : 344 ,
    'Iceland' : 352 ,
    'India (mainland)' : 356 ,
    'Andaman & Nicobar Isl. (India)' : 357 ,
    'Iraq' : 368 ,
    'Italy' : 380 ,
    "Côte d'Ivoire" : 384 ,
    'Jamaica' : 388 ,
    'Japan (main islands)' : 390 ,
    'Japan (Daito Islands)' : 393 ,
    'Johnston Atoll (USA)' : 396 ,
    'Kenya' : 404 ,
    'Korea (North)' : 408 ,
    'Korea (South)' : 410 ,
    'Kuwait' : 414 ,
    'Lebanon' : 422 ,
    'Latvia' : 428 ,
    'Liberia' : 430 ,
    'Libya' : 434 ,
    'Lithuania' : 440 ,
    'Madagascar' : 450 ,
    'Malaysia (Peninsula West)' : 459 ,
    'Malaysia (Peninsula East)' : 460 ,
    'Malaysia (Sabah)' : 461 ,
    'Maldives' : 462 ,
    'Malaysia (Sarawak)' : 463 ,
    'Malta' : 470 ,
    'Martinique (France)' : 474 ,
    'Mauritania' : 478 ,
    'Mauritius' : 480 ,
    'Hawaii Northwest Islands (USA)' : 488 ,
    'Montserrat (UK)' : 500 ,
    'Mozambique' : 508 ,
    'Oman' : 512 ,
    'Namibia' : 516 ,
    'Nauru' : 520 ,
    'Netherlands' : 528 ,
    'New Caledonia (France)' : 540 ,
    'Vanuatu' : 548 ,
    'New Zealand' : 554 ,
    'Kermadec Isl. (New Zealand)' : 555 ,
    'Nigeria' : 566 ,
    'Niue (New Zealand)' : 570 ,
    'Norfolk Isl. (Australia)' : 574 ,
    'Norway' : 578 ,
    'Jan Mayen Isl. (Norway)' : 579 ,
    'Northern Marianas (USA)' : 580 ,
    'Micronesia (Federated States of)' : 583 ,
    'Marshall Isl.' : 584 ,
    'Pakistan' : 586 ,
    'Papua New Guinea' : 598 ,
    'Peru' : 604 ,
    'Philippines' : 608 ,
    'Pitcairn (UK)' : 612 ,
    'Poland' : 616 ,
    'Portugal' : 620 ,
    'Madeira Isl. (Portugal)' : 621 ,
    'Azores Isl. (Portugal)' : 622 ,
    'Guinea-Bissau' : 624 ,
    'Timor Leste' : 626 ,
    'Puerto Rico (USA)' : 630 ,
    'Qatar' : 634 ,
    'Réunion (France)' : 638 ,
    'Romania' : 642 ,
    'Russia (Black Sea)' : 647 ,
    'Russia (Baltic Sea)' : 648 ,
    'Russia (Far East)' : 649 ,
    'Saint Helena (UK)' : 654 ,
    'Saint Kitts & Nevis' : 659 ,
    'Anguilla (UK)' : 660 ,
    'Saint Lucia' : 662 ,
    'Saint Pierre & Miquelon (France)' : 666 ,
    'Saint Vincent & the Grenadines' : 670 ,
    'Sao Tome & Principe' : 678 ,
    'Saudi Arabia (Red Sea)' : 683 ,
    'Saudi Arabia (Persian Gulf)' : 684 ,
    'Senegal' : 686 ,
    'Seychelles' : 690 ,
    'Sierra Leone' : 694 ,
    'Singapore' : 702 ,
    'Vietnam' : 704 ,
    'Slovenia' : 705 ,
    'Somalia' : 706 ,
    'Canary Isl. (Spain)' : 723 ,
    'Sudan' : 736 ,
    'Suriname' : 740 ,
    'Svalbard Isl. (Norway)' : 744 ,
    'Syria' : 760 ,
    'Togo' : 768 ,
    'Tokelau (New Zealand)' : 772 ,
    'Tonga' : 776 ,
    'Trinidad & Tobago' : 780 ,
    'United Arab Emirates' : 784 ,
    'Tunisia' : 788 ,
    'Turkey (Mediterranean Sea)' : 793 ,
    'Turkey (Black Sea)' : 794 ,
    'Turks & Caicos Isl. (UK)' : 796 ,
    'Tuvalu' : 798 ,
    'Ukraine' : 804 ,
    'Channel Isl. (UK)' : 830 ,
    'Tanzania' : 834 ,
    'Hawaii Main Islands (USA)' : 842 ,
    'Palmyra Atoll & Kingman Reef (USA)' : 844 ,
    'Jarvis Isl. (USA)' : 845 ,
    'Howland & Baker Isl. (USA)' : 846 ,
    'US Virgin Islands' : 850 ,
    'Ascension Isl. (UK)' : 855 ,
    'Tristan da Cunha Isl. (UK)' : 856 ,
    'Uruguay' : 858 ,
    'Venezuela' : 862 ,
    'Wake Isl. (USA)' : 872 ,
    'Wallis & Futuna Isl. (France)' : 876 ,
    'Samoa' : 882 ,
    'Montenegro' : 891 ,
    'St Paul & Amsterdam Isl. (France)' : 895 ,
    'Crozet Isl. (France)' : 896 ,
    'Kerguelen Isl. (France)' : 897 ,
    'Clipperton Isl.  (France)' : 898 ,
    'Corsica (France)' : 899 ,
    'Crete (Greece)' : 900 ,
    'Sicily (Italy)' : 901 ,
    'Sardinia (Italy)' : 902 ,
    'Balearic Island (Spain)' : 903 ,
    'Bonaire (Netherlands)' : 907 ,
    'Saba & Sint Eustaius (Netherlands)' : 908 ,
    'Sint Maarten (Netherlands)' : 909 ,
    'South Orkney Islands (UK)' : 910 ,
    'Oman (Musandam)' : 911 ,
    'Russia (Kara Sea)' : 912 ,
    'Sweden (Baltic)' : 914 ,
    'Sweden (West Coast)' : 915 ,
    'Yemen (Red Sea)' : 916 ,
    'Yemen (Arabian Sea)' : 917 ,
    'France (Mediterranean)' : 918 ,
    'France (Atlantic Coast)' : 919 ,
    'Honduras (Pacific)' : 920 ,
    'Honduras (Caribbean)' : 921 ,
    'Iran (Persian Gulf)' : 922 ,
    'Iran (Sea of Oman)' : 923 ,
    'Canada (East Coast)' : 926 ,
    'Colombia (Caribbean)' : 927 ,
    'Colombia (Pacific)' : 928 ,
    'Costa Rica (Caribbean)' : 929 ,
    'Costa Rica (Pacific)' : 930 ,
    'Denmark (North Sea)' : 932 ,
    'Egypt (Mediterranean)' : 933 ,
    'Egypt (Red Sea)' : 934 ,
    'Guatemala (Caribbean)' : 935 ,
    'Guatemala (Pacific)' : 936 ,
    'Indonesia (Indian Ocean)' : 938 ,
    'Israel (Mediterranean)' : 939 ,
    'Kiribati (Gilbert Islands)' : 941 ,
    'Kiribati (Line Islands)' : 942 ,
    'Kiribati (Phoenix Islands)' : 943 ,
    'Mexico (Atlantic)' : 944 ,
    'Mexico (Pacific)' : 945 ,
    'Morocco (Central)' : 946 ,
    'Morocco (Mediterranean)' : 947 ,
    'Morocco (South)' : 948 ,
    'Nicaragua (Caribbean)' : 949 ,
    'Nicaragua (Pacific)' : 950 ,
    'Panama (Caribbean)' : 951 ,
    'Panama (Pacific)' : 952 ,
    'South Africa (Atlantic Coast)' : 953 ,
    'South Africa (Indian Ocean Coast)' : 954 ,
    'South Africa (Prince Edward Islands)' : 711 ,
    'Thailand (Andaman Sea)' : 956 ,
    'Thailand (Gulf of Thailand)' : 957 ,
    'USA (Alaska, Subarctic)' : 959 ,
    'Spain (Mediterranean and Gulf of Cadiz)' : 962 ,
    'Spain (Northwest)' : 963 ,
    'Turkey (Marmara Sea)' : 966 ,
    'Aruba (Netherlands)' : 967 ,
    'United Arab Emirates (Fujairah)' : 968 ,
    'Brazil (Fernando de Noronha)' : 969 ,
    'Brazil (St Paul and St. Peter Archipelago)' : 970 ,
    'Japan (Ogasawara Islands)' : 971 ,
    'Glorieuse Islands (France)' : 972 ,
    'Curaçao (Netherlands)' : 906 ,
    'Saint Martin (France)' : 905 ,
    'St Barthelemy (France)' : 904 ,
    'Guadeloupe (France)' : 312 ,
    'USA (Alaska, Arctic)' : 958 ,
    'Jordan' : 400 ,
    'Israel (Red Sea)' : 940 ,
    'Canada (Pacific)' : 925 ,
    'Canada (Arctic)' : 924 ,
    'Russia (Barents Sea)' : 645 ,
    'Denmark (Baltic Sea)' : 931 ,
    'Solomon Isl.' : 90 ,
    'Palau' : 585 ,
    'Finland' : 246 ,
    'United Kingdom' : 826 ,
    'Indonesia (Eastern)' : 361 ,
    'Indonesia (Central)' : 937 ,
    'Chile' : 152 ,
    'Ireland' : 372 ,
    'USA (West Coast)' : 848 ,
    'USA (Gulf of Mexico)' : 852 ,
    'USA (East Coast)' : 851 ,
    'Russia (Laptev to Chukchi Sea)' : 912 ,
}

eezname_to_faoname = {
    'Antigua & Barbuda' : 'Antigua and Barbuda' ,
    'Macquarie Isl. (Australia)' : 'Australia' ,
    'Lord Howe Isl. (Australia)' : 'Australia' ,
    'Bosnia & Herzegovina' : 'Bosnia and Herzegovina',
    'Bouvet Isl. (Norway)' : 'Islands' ,
    'Trindade & Martim Vaz Isl. (Brazil)' : 'Brazil' ,
    'Chagos Archipelago (UK)' : 'Islands' ,
    'Easter Isl. (Chile)' : 'Islands' ,
    'Desventuradas Isl. (Chile)' : 'Islands' ,
    'Juan Fernandez Islands (Chile)' : 'Islands' ,
    'Cape Verde': 'Cabo Verde',
    'Christmas Isl. (Australia)' : 'Islands' ,
    'Cocos (Keeling) Isl. (Australia)' : 'Islands' ,
    'Comoros Isl.' : 'Comoros' ,
    'Mayotte (France)' : 'Islands' ,
    'Congo, R. of' : 'Congo' ,
    'Cyprus (North)' : 'North Cyprus' ,
    'Cyprus (South)' : 'Cyprus' ,
    'Galapagos Isl. (Ecuador)' : 'Islands' ,
    'South Georgia & Sandwich Isl. (UK)' : 'South Georgia and the South Sandwich Isl.',
    'Mozambique Channel Isl. (France)' : 'Islands' ,
    'Tromelin Isl. (France)' : 'Islands' ,
    'Gaza Strip' : 'Israel' ,
    'Germany (North Sea)' : 'Germany' ,
    'Germany (Baltic Sea)' : 'Germany' ,
    'Heard & McDonald Isl. (Australia)' : 'Heard Isl. And McDonald Isl.' ,
    'Hong Kong (China)' : 'Hong Kong' ,
    'India (mainland)' : 'India' ,
    'Andaman & Nicobar Isl. (India)' : 'India' ,
    "Côte d'Ivoire" : "Cote d'Ivoire" ,
    'Japan (main islands)' : 'Japan' ,
    'Japan (Daito Islands)' : 'Japan' ,
    'Johnston Atoll (USA)': 'Johnson Atoll (USA)',
    'Malaysia (Peninsula West)' : 'Malaysia' ,
    'Malaysia (Peninsula East)' : 'Malaysia' ,
    'Malaysia (Sabah)' : 'Malaysia' ,
    'Malaysia (Sarawak)' : 'Malaysia' ,
    'Northern Marianas (USA)': 'North Marianas (USA)',
    'Hawaii Northwest Islands (USA)' : 'Islands' ,
    'Kermadec Isl. (New Zealand)' : 'New Zealand',
    'Niue (New Zealand)' : 'New Zealand' ,
    'Jan Mayen Isl. (Norway)' : 'Jan Maven' ,
    'Micronesia (Federated States of)' : 'Micronesia' ,
    'Russia (Black Sea)' : 'Russian Federation' ,
    'Russia (Baltic Sea)' : 'Russian Federation' ,
    'Russia (Far East)' : 'Russian Federation' ,
    'Saudi Arabia (Red Sea)' : 'Saudi Arabia' ,
    'Saudi Arabia (Persian Gulf)' : 'Saudi Arabia' ,
    'Canary Isl. (Spain)' : "Spain" ,
    'Tokelau (New Zealand)' : "New Zealand" ,
    'Turkey (Mediterranean Sea)' : "Turkey" ,
    'Turkey (Black Sea)' : 'Turkey' ,
    'Channel Isl. (UK)' : 'United Kingdom' ,
    'Hawaii Main Islands (USA)' : 'Islands' ,
    'Palmyra Atoll & Kingman Reef (USA)' : 'Islands' ,
    'Jarvis Isl. (USA)' : 'Islands' ,
    'Howland & Baker Isl. (USA)' : 'Islands' ,
    'US Virgin Islands' : 'US Virgin Isl.' ,
    'Tristan da Cunha Isl. (UK)' : 'Islands' ,
    'Wake Isl. (USA)' : 'Islands' ,
    'St Paul & Amsterdam Isl. (France)' : 'Islands' ,
    'Kerguelen Isl. (France)' : 'Islands' ,
    'Clipperton Isl.  (France)' : 'Islands' ,
    'Corsica (France)' : "France" ,
    'Crete (Greece)' : 'Greece' ,
    'Sicily (Italy)' : 'Italy' ,
    'Sardinia (Italy)' : 'Italy' ,
    'Balearic Island (Spain)' : 'Spain' ,
    'Saba & Sint Eustaius (Netherlands)' : 'Islands' ,
    'Sint Maarten (Netherlands)' : 'Sint Maarten' ,
    'South Orkney Islands (UK)' : 'Islands' ,
    'Oman (Musandam)' : 'Oman' ,
    'Russia (Kara Sea)' : 'Russian Federation' ,
    'Sweden (Baltic)' : 'Sweden' ,
    'Sweden (West Coast)' : 'Sweden' ,
    'Yemen (Red Sea)' : 'Yemen' ,
    'Yemen (Arabian Sea)' : 'Yemen' ,
    'France (Mediterranean)' : 'France' ,
    'France (Atlantic Coast)' : 'France',
    'Honduras (Pacific)' : 'Honduras' ,
    'Honduras (Caribbean)' : 'Honduras' ,
    'Iran (Persian Gulf)' : 'Iran' ,
    'Iran (Sea of Oman)' : 'Iran' ,
    'Canada (East Coast)' : 'Canada' ,
    'Colombia (Caribbean)' : 'Colombia' ,
    'Colombia (Pacific)' : 'Colombia' ,
    'Costa Rica (Caribbean)' : 'Costa Rica' ,
    'Costa Rica (Pacific)' : 'Costa Rica' ,
    'Denmark (North Sea)' : 'Denmark' ,
    'Egypt (Mediterranean)' : 'Egypt' ,
    'Egypt (Red Sea)' : 'Egypt' ,
    'Guatemala (Caribbean)' : 'Guatemala' ,
    'Guatemala (Pacific)' : 'Guatemala' ,
    'Indonesia (Indian Ocean)' : 'Indonesia' ,
    'Israel (Mediterranean)' : 'Israel' ,
    'Kiribati (Gilbert Islands)' : 'Kiribati' ,
    'Kiribati (Line Islands)' : 'Kiribati' ,
    'Kiribati (Phoenix Islands)' : 'Kiribati' ,
    'Mexico (Atlantic)' : 'Mexico' ,
    'Mexico (Pacific)' : 'Mexico' ,
    'Morocco (Central)' : 'Morocco' ,
    'Morocco (Mediterranean)' : 'Morocco' ,
    'Morocco (South)' : 'Morocco' ,
    'Nicaragua (Caribbean)' : 'Nicaragua' ,
    'Nicaragua (Pacific)' : 'Nicaragua' ,
    'Panama (Caribbean)' : 'Panama' ,
    'Panama (Pacific)' : 'Panama' ,
    'South Africa (Atlantic Coast)' : 'South Africa' ,
    'South Africa (Indian Ocean Coast)' : 'South Africa' ,
    'South Africa (Prince Edward Islands)' : 'South Africa' ,
    'Thailand (Andaman Sea)' : 'Thailand' ,
    'Thailand (Gulf of Thailand)' : 'Thailand' ,
    'USA (Alaska, Subarctic)' : 'USA' ,
    'Spain (Mediterranean and Gulf of Cadiz)' : 'Spain' ,
    'Spain (Northwest)' : 'Spain' ,
    'Syria': 'Syrian Arab Republic',
    'Turkey (Marmara Sea)' : 'Turkey' ,
    'United Arab Emirates (Fujairah)' : 'United Arab Emirates' ,
    'Brazil (Fernando de Noronha)' : 'Brazil' ,
    'Brazil (St Paul and St. Peter Archipelago)' : 'Brazil' ,
    'Japan (Ogasawara Islands)' : 'Japan' ,
    'Glorieuse Islands (France)' : 'Islands' ,
    'Curaçao (Netherlands)' : 'Curacao' ,
    'Saint Martin (France)' : 'Islands',
    'St Barthelemy (France)' : 'Islands' ,
    'Guadeloupe (France)' : 'Islands' ,
    'USA (Alaska, Arctic)' : 'USA' ,
    'Israel (Red Sea)' : 'Israel' ,
    'Canada (Pacific)' : 'Canada' ,
    'Canada (Arctic)' : 'Canada' ,
    'Russia (Barents Sea)' : 'Russian Federation',
    'Denmark (Baltic Sea)' : 'Denmark' ,
    'Indonesia (Eastern)' : 'Indonesia' ,
    'Indonesia (Central)' : 'Indonesia' ,
    'USA (West Coast)' : 'USA' ,
    'USA (Gulf of Mexico)' : 'USA' ,
    'USA (East Coast)' : 'USA' ,
    'Russia (Laptev to Chukchi Sea)' : 'Russian Federation' ,
    'Vietnam': 'Viet Nam',
    'Wallis & Futuna Isl. (France)': 'Wallis and Futuna Isl. (France)',
}

def grid_species_catch(species,catchdata,region,cellid_grid=None,cellx=720,celly=360,
                       regionheader='Reg'):
    cellids = catchdata['CellID']\
        [catchdata['Hg_category'] == species][catchdata[regionheader] == region].values
    catch = catchdata['Catch'][catchdata['Hg_category'] == species]\
        [catchdata[regionheader] == region].values
    gridded = np.zeros_like(cellid_grid)
    celltotal = cellx*celly
    gridded_flat = np.zeros(celltotal)
    for i,cid in enumerate(cellids):
        if cellid_grid:
            gridded = np.where(cellid_grid==float(cid),float(catch[i]),gridded)
        else:
            gridded_flat[int(cid)+1] = catch[i]
    if not cellid_grid:
        gridded = np.reshape(gridded_flat,(celly,cellx))
    gridded_out = np.zeros_like(gridded)
    gridded_out[:,:-1] = gridded[:,1:]
    gridded_out[:,-1] = gridded[:,0]

    return gridded_out


def regrid_down(gridded, intrinsic=1):
    gridlength,gridwidth = np.shape(gridded);
    regridded = np.zeros((gridlength*2,gridwidth*2));
    
    if intrinsic:
        A = 1.
    else:
        A = 4.

    for i in range(gridlength):
        for j in range(gridwidth):
            regridded[2*i-1,2*j-1] = gridded[i,j]/A
            regridded[2*i,2*j-1] = gridded[i,j]/A
            regridded[2*i-1,2*j] = gridded[i,j]/A
            regridded[2*i,2*j] = gridded[i,j]/A
    #regridded = regridded[2:gridlength*2-1,:]
    regridded = regridded[:,:]

    return regridded

def regrid_lon_25_2(gridded,intrinsic=1):
    gridlength,gridwidth = np.shape(gridded);
    downgridded = np.zeros((gridlength,gridwidth*5));
    newgridwidth = gridwidth*5//4
    regridded = np.zeros((gridlength,newgridwidth))
    if intrinsic:
        A = 1.
    else:
        A = 5.

    for i in range(gridlength):
        for j in range(gridwidth):
            downgridded[i,5*j-2] = gridded[i,j]/A
            downgridded[i,5*j-1] = gridded[i,j]/A
            downgridded[i,5*j+2] = gridded[i,j]/A
            downgridded[i,5*j+1] = gridded[i,j]/A
            downgridded[i,5*j] = gridded[i,j]/A
    for i in range(gridlength):
        for j in range(newgridwidth):
            if intrinsic > 1:
                regridded[i,j] = downgridded[i,4*j-3]
            elif intrinsic:
                regridded[i,j] = np.mean(downgridded[i,4*j-3:4*j+1])
            else:
                regridded[i,j] = np.sum(downgridded[i,4*j-3:4*j+1])
    #regridded = regridded[2:gridlength*2-1,:]
    regridded = regridded[:,:]

    
    return regridded

def fillinzeros(mask, fillthreshold=1):
    masklength,maskwidth = np.shape(mask)
    for i in range(masklength):
        for j in range(maskwidth):
            if mask[i,j] < fillthreshold:
                a = mask[i,j-1]
                b = mask[i-1,j]
                if a == b:
                    mask[i,j] = a
                elif b > 0:
                    mask[i,j] = b
                else:
                    mask[i,j] = a           

    return mask

def fill_nearest(grid):
    out = np.zeros_like(grid)
    ny,nx = grid.shape
    for j in range(1,ny-1):
        for i in range(1,nx-1):
            if np.isnan(grid[j,i]):
                out[j,i] = np.nanmean(grid[j-1:j+2,i-1:i+2])
            else:
                out[j,i] = grid[j,i]
    return out 

def gridbox_areas(lats,lons):
    areas = np.ones((len(lats),len(lons)))
    dlat = lats[1]-lats[0]
    dlon = lons[1]-lons[0]
    dx = dlon*111321.0 # m
    dy = dlat*111321.0 # m
    area_at_eq = dx*dy
    areas = area_at_eq*areas
    areas = areas*np.cos(lats*np.pi/180)[:,None]
    return areas

