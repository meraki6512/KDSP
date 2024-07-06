## Contents
1. [ Brief description of the project ](#-Brief-description-of-the-project)
2. [ how to use the project ](#-how-to-use-the-project)
3. [requirements of the project](#-requirements-of-the-project)

## Brief description of the project 
#### 3 Recommendation Tasks that addressed
1. **10 unvisited places** should be recommended based on specific users and categories.
2. **10 other users** with the most similar interests to a specific user must be found in the entire data set.
3. From 5 users and each location, **a place to meet** for them should be provided.

### Data Info

#### summary
- contents: <u>Location history of users</u> (userID, venueID, lat, long, ...)
- RangeIndex: **227428** entries, 0 to 227427 <br>
- Data columns: **8** columns in total <br>

#### details
<details><summary> UserID </summary>
id of each user<br>
range: 1 to 1083 <br>
dtype: int64 
</details>
<details><summary> 
VenueID</summary>
id of each venue
unique: 38333 <br>
dtype: object <br>
not used in this project
</details>
<details><summary> VenueCategoryID</summary>
id of each venue category <br>
unique: 400   <br>
dtype: object
</details>
<details><summary> VenueCategoryName</summary>
semantic meaning of each venue category id (i.e. bar, park etc.)<br>
unique: 251   <br>
dtype: object
</details>
<details><summary> Latitude</summary>
latitude of each location from the user log <br>
range: 40.550852 to 40.988332 <br>
dtype: float64
</details>
<details><summary> Longitude</summary>
longitude of each location from the user log <br>
range: -74.274766 to -73.683825 <br>
dtype: float64  
</details>
<details><summary> TimezoneOffsetInMin</summary>
timezone offset (min) <br>
range: -420 to 660   <br>
dtype: int64 <br>
not used in this project
</details>
<details><summary> UTCTime</summary>
utc time of the log (date, month, day, time, year) <br>
unique: 224653 <br>
dtype: object <br>
not used in this project
</details>



## how to use the project

1. Activate virtual environment <br>
`cd venv/Scripts` <br>
`activate` <br><br>
2. Implement app.py <br>
`python app.py`<br><br>
3. Connect localhost and choose a link to access between 3 functions below

   - recommend1 : recommend 10 unvisited locations to given UID having similar category with given CategoryID
   - recommend2 : recommend the 10 most similar users with a randomly given user
   - recommend3 : recommend meeting point with 5 randomly given users and their locations

## requirements of the project 

Python and some libraries are used in this project. If you don't have any of modules, please install them additionally.

```python
import pandas as pd
import numpy as np
import math
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import folium

from flask import Flask, request, render_template, redirect, flash
from flask_wtf import FlaskForm
from wtforms import IntegerField, FloatField, FieldList, FormField
from wtforms.validators import DataRequired
```