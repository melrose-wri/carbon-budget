### This

from multiprocessing.pool import Pool
from functools import partial
import utilities
import annual_gain_rate
import pandas as pd
import subprocess

pd.options.mode.chained_assignment = None

### Need to update and install some packages on spot machine before running
### sudo pip install rasterio --upgrade
### sudo pip install pandas --upgrade
### sudo pip install xlrd

# Continent-ecozone and forest age category are needed for the forest age decision tree
age_cat = 's3://gfw2-data/climate/carbon_model/forest_age_category/20180921/'
cont_eco = 's3://gfw2-data/climate/carbon_model/fao_ecozones/ecozone_continent/20180912/'

biomass = 's3://gfw2-data/climate/WHRC_biomass/WHRC_V4/Processed/'
# biomass_tile_list = utilities.tile_list(biomass)
# biomass_tile_list = ['20S_110E', '30S_110E'] # test tiles
biomass_tile_list = ['20S_110E'] # test tiles
print biomass_tile_list

# # # For downloading all tiles in the input folders
# # download_list = [age_cat, cont_eco]
# #
# # for input in download_list:
# #     utilities.s3_folder_download('{}'.format(input), '.')

# For copying individual tiles to spot machine for testing
for tile in biomass_tile_list:

    utilities.s3_file_download('{0}forest_age_category_{1}.tif'.format(age_cat, tile), '.')             # forest age category tiles
    utilities.s3_file_download('{0}fao_ecozones_continents_{1}.tif'.format(cont_eco, tile), '.')        # continents and FAO ecozones 2000

# Table with IPCC Table 4.9 default gain rates
cmd = ['aws', 's3', 'cp', 's3://gfw2-data/climate/carbon_model/gain_rate_continent_ecozone_age_20180918.xlsx', '.']
subprocess.check_call(cmd)

# Imports the table with the ecozone-continent codes and the carbon gain rates
gain_table = pd.read_excel("gain_rate_continent_ecozone_age_20180918.xlsx",
                           sheet_name = "con-ezn-age gain, for model")

# Removes rows with duplicate codes (N. and S. America for the same ecozone)
gain_table_simplified = gain_table.drop_duplicates(subset='gainEcoCon', keep='first')

# Converts gain table from wide to long, so each continent-ecozone-age category has its own row
gain_table_cont_eco_age = pd.melt(gain_table_simplified, id_vars = ['gainEcoCon'], value_vars = ['growth_primary', 'growth_secondary_greater_20', 'growth_secondary_less_20'])
gain_table_cont_eco_age = gain_table_cont_eco_age.dropna()

# Creates a table that has just the continent-ecozone combinations for adding to the dictionary.
# These will be used whenever there is just a continent-ecozone pixel without a forest age pixel
gain_table_con_eco_only = gain_table_cont_eco_age
gain_table_con_eco_only = gain_table_con_eco_only.drop_duplicates(subset='gainEcoCon', keep='first')
gain_table_con_eco_only['value'] = 0
gain_table_con_eco_only['cont_eco_age'] = gain_table_con_eco_only['gainEcoCon']

# Creates a code for each age category so that each continent-ecozone-age combo can have its own unique value
age_dict = {'growth_primary': 10000, 'growth_secondary_greater_20': 20000, 'growth_secondary_less_20': 30000}

# Creates a unique value for each continent-ecozone-age category
gain_table_cont_eco_age = gain_table_cont_eco_age.replace({"variable": age_dict})
gain_table_cont_eco_age['cont_eco_age'] = gain_table_cont_eco_age['gainEcoCon'] + gain_table_cont_eco_age['variable']

# Merges the table of just continent-ecozone codes and the table of  continent-ecozone-age codes
gain_table_all_combos = pd.concat([gain_table_con_eco_only, gain_table_cont_eco_age])

# Converts the continent-ecozone-age codes and corresponding gain rates to a dictionary
gain_table_dict = pd.Series(gain_table_all_combos.value.values,index=gain_table_all_combos.cont_eco_age).to_dict()

# Adds a dictionary entry for where the ecozone-continent-age code is 0 (not in a continent)
gain_table_dict[0] = 0

# Adds a dictionary entry for each forest age code for pixels that have forest age but no continent-ecozone
for key, value in age_dict.iteritems():

    gain_table_dict[value] = 0

# Converts all the keys (continent-ecozone-age codes) to float type
gain_table_dict = {float(key): value for key, value in gain_table_dict.iteritems()}


# This configuration of the multiprocessing call is necessary for passing multiple arguments to the main function
# It is based on the example here: http://spencerimp.blogspot.com/2015/12/python-multiprocess-with-multiple.html
num_of_processes = 2
pool = Pool(num_of_processes)
pool.map(partial(annual_gain_rate.annual_gain_rate, gain_table_dict=gain_table_dict), biomass_tile_list)
pool.close()
pool.join()

# # For single processor use
# for tile in biomass_tile_list:
#
#     annual_gain_rate.annual_gain_rate(tile, gain_table_dict)

