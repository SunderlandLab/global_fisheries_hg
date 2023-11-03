# Global Fisheries Hg

Code used for the publication Li et al. 2023 (in review).

Associated data can be found via Dataverse: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/KVC2WH
and downloaded to the "data" folder, which is used by the notebook "analysis.ipynb".

Python 3 Package Requirements (version used):
 - cartopy (0.22.0)
 - matplotlib (3.7.2)
 - numpy (1.24.3)
 - pandas (1.3.3)
 - scipy (1.9.3)
 - shapefile (2.3.1)
 - shapely (2.0.1)
 - xarray (0.19.0)

No special installation is required. Installing above packages normally takes a few minutes.

analysis.ipynb can be executed pointing to the analogous uncertainty scenario data downloaded from Dataverse (the scenario_data.zip file) and extracted to the "scenario_data" folder.
The notebook contains expected output by default. The entire analysis may take about 20 minutes on a "normal" desktop computer.

Other routines and functions are included in "catchtools.py"
