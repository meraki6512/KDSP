import pandas as pd
import numpy as np
import math
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import folium

PATH = "Project3_Data\dataset_NYC.txt"
columns = ['UserID', 'VenueID', 'VenueCategoryID', 'VenueCategoryName', 'Latitude', 'Longitude', 'TimezoneOffsetInMin',
           'UTCTime']
df = pd.read_csv(PATH, sep="\t", encoding_errors='ignore', names=columns)


# 1.
# goal of the task: recommend 10 unvisited locations to given UID having similar category with given CategoryID
# @input: random UID, CategoryID
# @output: VenueID(location) list

def recommendVenueFromIDandCategory(inputUserID, inputCategory):
    clustered = clusterCategories()
    corr = getSimilarCategories(inputCategory, clustered)
    freq_category = getFreqCategory(inputUserID)
    freq_loc = getFreqLoc(freq_category)
    h, l = getOutlier(freq_loc['per'])

    # To select places that are not outliers calculated previously, create a standard value 'per' as a latitude/longitude ratio
    df['per'] = df['Latitude'] / df['Longitude']
    # Places close to previously found places & places not visited by the entered user ID
    candidate = df.loc[(l < df['per']) & (h > df['per']) & (df['UserID'] != inputUserID)]

    # Sorting in the order of places in the category found initially: The reason for sorting rather than selecting is that the selected places have similar conditions, so randomly selecting 10 of them can provide more diverse recommendations to users.
    i = 0
    for i in range(len(corr)):
        if i == 0:
            recommend = candidate[candidate['VenueCategoryName'] == corr.index[i]]
        else:
            recommend = pd.concat([recommend, candidate[candidate['VenueCategoryName'] == corr.index[i]]], axis=0)

    # To recommend VenueID(location) list, drop duplicates of VenueID
    recommend.drop_duplicates('VenueID', inplace=True)
    recommend = recommend[['VenueID', 'VenueCategoryName', 'Latitude', 'Longitude']]

    # it now recommends 10 top places from the df
    # might be fixed to recommend in various way
    recommend = recommend.head(10).values.tolist()
    return recommend


def getFreqCategory(inputUserID):
    # reframe data from UserID and VenueCategoryID
    gdf_categoryID = df.groupby(['UserID', 'VenueCategoryID']).size().reset_index()
    gdf_categoryID.columns = ['UserID', 'VenueCategoryID', 'N']
    re_user = pd.pivot_table(gdf_categoryID, index='UserID', columns='VenueCategoryID', values='N', fill_value=0)

    # make temporal data frame to count how many times inputUserId visit each places
    temp = re_user[re_user.index == inputUserID].transpose()
    # drop places where count = 0
    temp = temp[temp[inputUserID] != 0]

    # VenueCategoryID -> VenueCategoryName (to show data easily)
    temp_id = list()
    for _id in temp.index:
        temp_id.append(find_category_name_by_id(_id))
    temp['VenueCategoryName'] = temp_id

    # sort by visit frequencies
    temp = temp.sort_values(inputUserID, ascending=False)
    # drop places where freqeuncy < mean
    m = temp[inputUserID].mean()
    temp = temp[m < temp[inputUserID]]

    return temp


# Function that returns a data frame containing latitude and longitude information of places that inputUserID frequently visits
def getFreqLoc(freq_category):
    ## Based on frequency data, extract radius data of places frequented by users from actual latitude and longitude data

    # lat, lon info from places that inputUserID frequently visits data (freq.index: Category info of frequently visited places)
    freq_loc = pd.DataFrame()
    for _id in freq_category.index:
        _temp = df[df['VenueCategoryID'] == _id][['Latitude', 'Longitude']]
        freq_loc = pd.concat([freq_loc, _temp], axis=0)

    # drop duplicates of lat, lon (precise location info) : location info rather than frequency info will be used
    freq_loc = freq_loc.drop_duplicates(['Latitude', 'Longitude'])

    # Removing outliers (excluding too far places)
    # To calculate outliers, use the ratio of latitude and longitude to create a reference value
    freq_loc['per'] = freq_loc['Latitude'] / freq_loc['Longitude']

    return freq_loc


# Function that calculate IQR from given data and return its reference value
def getOutlier(data):

    # Q1 - 1.5 * IQR = lowest, Q3 + 1.5 * IQR = highest (IQR = Q3 - Q1)
    q1 = data.quantile(0.25)
    q3 = data.quantile(0.75)
    iqr = q3 - q1

    h = q3 + 1.5 * iqr
    l = q1 - 1.5 * iqr

    return h, l


# Function that extracts only data belonging to the same cluster as inputCategory and returns data sorted in a similarity.
def getSimilarCategories(inputCategory, similar):
    # Extract frequently visited categories belonging to the same cluster as inputCategory
    # get cluster of inputCategory
    inputCluster = similar[similar.index == inputCategory]['cluster'][inputCategory]

    # pick data which have same cluster as input cluster
    similar = similar[similar['cluster'] == inputCluster]

    # sort by abs of differences
    similar['diff'] = similar['sum'].sub(similar[similar.index == inputCategory]['sum'][inputCategory]).abs()
    similar = similar.sort_values('diff')

    # drop where the value >= mean
    m = similar['diff'].mean()
    similar = similar[m > similar['diff']]

    return similar


# Function that clusters based on the frequency of visits for each place category and returns numbered data for places with similar visit frequencies
def clusterCategories():
    # reframe data by UserID, VenueCategoryName, and the frequency of visiting
    gdf = df.groupby(['UserID', 'VenueCategoryName']).size().reset_index()
    gdf.columns = ['UserID', 'VenueCategoryName', 'N']
    re_category = pd.pivot_table(gdf, index='VenueCategoryName', columns='UserID', values='N', fill_value=0)

    # Value correction: Find the percentage of frequency for each place category.
    corr = re_category.div(re_category.sum(axis=0)).mul(100)
    # to make calculations more convenient later, add up the numbers for each location.
    corr['sum'] = corr.sum(axis=1)

    ## cluster by corr['sum'] (= added freq for each location)

    # 10% sampling
    X_sample = corr[['sum']].sample(frac=0.1)
    # n in KMeans = sqrt of (data length/2)
    n = math.ceil(math.sqrt(corr.shape[0] / 2))
    # KMeans Clustering
    kmeans = KMeans(n_clusters=n, init='k-means++')
    kmeans.fit(X_sample)
    y = kmeans.labels_
    # add cluster number to data
    corr['cluster'] = kmeans.predict(corr[['sum']])

    return corr


# Function that finds VenueCategoryName by venueCategoryID
def find_category_name_by_id(_id):
    # drop duplicates of venueCategoryID: to find matching venueCategoryName easily
    df_unique_categoryID = df.drop_duplicates('VenueCategoryID')

    temp_cat = df_unique_categoryID[df_unique_categoryID['VenueCategoryID'] == _id]
    temp_cat.reset_index(drop=True, inplace=True)

    return temp_cat['VenueCategoryName'][0]


# 2.
# goal of the task: recommend the 10 most similar users with a randomly given user
# @input param: randomly given UserID
# @expected output: top 10 UserIds list with the most similar, interests match

def recommendUsersFromID(inputUserID):
    gdf = df.groupby(['UserID', 'VenueCategoryName']).size().reset_index()
    gdf.columns = ['UserID', 'VenueCategoryName', 'N']
    re_category = pd.pivot_table(gdf, index='VenueCategoryName', columns='UserID', values='N', fill_value=0)
    freq_id = re_category.transpose()

    # Cosine similarity: A method of calculating similarity using the angle between vectors; the closer the value is to 1, the more similar it is.
    # Calculate cosine similarity for each ID and retrieve the cosine similarity vector corresponding to the input userID
    freq_id['cos'] = cosine_similarity(freq_id)[inputUserID]

    # Sort the values in descending order, exclude the entered userID, and select the remaining top 10.
    most_similar = freq_id.sort_values('cos', ascending=False)[1:11].index

    return most_similar.values.tolist()


# 3.
# goal of the task: recommend meeting point with 5 randomly given users and their locations
# @input param: randomly given 5 UserIDs and their locations (Latitude, Longitude)
# @expected output: the location of recommended meeting point

# visualization
# Function that visually displays the locations of the original userID and suggested locations
def showMap(inputUserIDs, inputLocs, meetingPoint):
    mid = inputLocs.transpose().mean(axis=1)
    m = folium.Map(location=mid, zoom_start=10)

    for i in range(5):
        folium.Marker(inputLocs[i], tooltip=inputUserIDs[i]).add_to(m)

    folium.Marker(meetingPoint,
                  icon=folium.Icon(color='red', icon='star'),
                  tooltip='suggestPoint').add_to(m)

    return m


# Function that suggests the optimal meeting location from 5 userIDs and each location
def recommendMeetingPointFromIDsandLocs(inputUserIDs, inputLocs):
    # find mid point from 5 locations
    mid = inputLocs.transpose().mean(axis=1)

    # find VenueCategoryNames that suit each userID's tastes
    freq_categories = pd.DataFrame(columns=inputUserIDs)
    for i in range(5):
        temp = getFreqCategory(inputUserIDs[i])['VenueCategoryName']
        freq_categories = pd.concat([freq_categories, temp], axis=1)

    ## Select one category with the most overlap between categories
    temp_list = list(freq_categories)
    temp_set = list(set(temp))
    max = 0
    most_freq_category = temp_set[0]
    # find overlapping categories and their number, and find the category with the most overlap.
    for i in range(len(temp_set)):
        cnt = temp_list.count(temp_set[i])
        if cnt > max:
            max = cnt
            most_freq_category = temp_set[i]

    if max == 1:
        # If NO overlapping categories -> just recommend the closest location from mid.
        data = np.array(df[['Latitude', 'Longitude']])
    else:
        # If overlapping categories (O) -> recommend appropriate location by the most overlapping categories and mid location info
        data = np.array(df[df['VenueCategoryName'] == most_freq_category][['Latitude', 'Longitude']])

    meetingPoint = findNearestLoc(mid, data)

    return meetingPoint


# Function that finds the closest x,y to a random x,y among the x,y in the given data
def findNearestLoc(point, data):

    mn = 10000
    idx = 0

    for i in range(len(data)):

        # Euclidean distance
        s = np.sum((point - data[i]) ** 2)

        if s < mn:
            mn = s
            idx = i

    return data[i]


# Function that gets a UserID from the user
def getUserID():
    # 수정 1083
    while ((inputUserID := int(input("Enter UserID (from 1 to 1083): "))) < 1 or inputUserID > 1083):
        print("UserID Error")
        continue

    return inputUserID


# Function that gets a VenueCategoryName from the user
def getCategoryName():
    cnt = 0
    CategoryType = df['VenueCategoryName'].value_counts().index

    # Repeat until the data frame contains a CategoryName that contains the characters entered by the user
    while cnt >= 0:

        inputCategory = input("Enter VenueCategoryName: ")

        if inputCategory.strip() == "":
            pass

        # If a CategoryName contains characters entered by the user, return the exact CategoryName
        for _type in CategoryType:
            if inputCategory.strip() in _type:
                inputCategory = _type
                cnt = -1
                break

        if cnt >= 0:
            print("CategoryName Error")
            cnt += 1

    return inputCategory


# Function that gets 5 UserIDs from the user
def get_5_UserIDs():
    inputCheck = False

    while inputCheck == False:

        temp = input("Enter 5 UserID(from 1 to 1083)s: ").split()
        for i in range(len(temp)):
            temp[i] = temp[i].rstrip(r',$')
        inputUserIDs = list(map(int, temp))

        if (len(inputUserIDs) != 5):
            print("UserID Error (input 5 user ids)")
            continue

        i = 0
        for n in inputUserIDs:
            if n < 1 or n > 1083:
                print("UserID Error (" + n + " could not be accepted)")
                i += 1

        if i < 1:
            inputCheck = True

    return inputUserIDs


# Function that finds each Location from 5 UserIDs
def get_5_Locations(inputUserIDs):
    # get locations (lat, lon) for each UserID
    inputLocs = pd.DataFrame(columns=['Latitude', 'Longitude'])

    for i in range(5):

        while True:
            temp = list(input("Enter the location of UserID:" + str(inputUserIDs[i]) + " (lat, lon): ").split())

            if len(temp) != 2:
                print("Location Error (input latitude and longitude)")
                continue

            temp[0] = temp[0].rstrip(r',$')
            temp[1] = temp[1].rstrip(r',$')

            lat, lon = map(float, temp)

            if abs(lat) > 90:
                print("Latitude Range Error (it must be in range of (-90, 90))")
            elif abs(lon) > 180:
                print("Longitude Range Error (it must be in range of (-180, 180))")
            else:
                break

        inputLocs = pd.concat([inputLocs, pd.DataFrame({'Latitude': [lat], 'Longitude': [lon]})])

    inputLocs.index = inputUserIDs

    return inputLocs


############################## functions to operate in command line (for test)

# Task1
# recommend 10 unvisited locations to given UID having similar category with given CategoryID
def recommend_1():
    inputUserID = getUserID()
    inputCategory = getCategoryName()

    recommendedVenueIDs = recommendVenueFromIDandCategory(inputUserID, inputCategory)

    print(recommendedVenueIDs)

# Task2
# recommend the 10 most similar users with a randomly given user
def recommend_2():
    inputUserID = getUserID()

    recommendedUserIDs = recommendUsersFromID(inputUserID)

    print(recommendedUserIDs)

# Task3
# recommend meeting point with 5 randomly given users and their locations
def recommend_3():
    inputUserIDs = get_5_UserIDs()
    inputLocs = np.array(get_5_Locations(inputUserIDs))

    meetingPoint = recommendMeetingPointFromIDsandLocs(inputUserIDs, inputLocs)
    m = showMap(inputUserIDs, inputLocs, meetingPoint)

    print(meetingPoint)
    print(m)


# def main():
#
#     #clusterCategories()
#     #getSimilarCategories()
#     #recommend_1() # 1. recommend 10 unvisited locations to given UID having similar category with given CategoryID
#     #recommend_2() # 2. recommend the 10 most similar users with a randomly given user
#     #recommend_3() # 3. recommend meeting point with 5 randomly given users and their locations
#
#
# if __name__ == "__main__":
#     main()



#################################### functions to use in app.py
### functions to operate when parameters are given

# Task1
# recommend 10 unvisited locations to given UID having similar category with given CategoryID
def recommend_1_with_param(inputUserID, inputCategory):
    recommendedVenueIDs = recommendVenueFromIDandCategory(inputUserID, inputCategory)
    print(recommendedVenueIDs)
    return recommendedVenueIDs

# Task2
# recommend the 10 most similar users with a randomly given user
def recommend_2_with_param(inputUserID):
    recommendedUserIDs = recommendUsersFromID(inputUserID)
    print(recommendedUserIDs)
    return recommendedUserIDs

# Task3
# recommend meeting point with 5 randomly given users and their locations
def recommend_3_with_param(inputUserIDs, inputLocs):
    inputLocs = np.array(inputLocs)
    meetingPoint = recommendMeetingPointFromIDsandLocs(inputUserIDs, inputLocs)
    m = showMap(inputUserIDs, inputLocs, meetingPoint)

    m.save('templates/r3_out_map.html')

    # # save img
    # options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    # # options.add_experimental_option("detach", True)
    # service = Service(executable_path=r"C:/chromedriver/chromedriver.exe")
    # driver = webdriver.Chrome(service=service, options=options)
    #
    # img_data = m._to_png(5, driver=driver)
    # img = Image.open(io.BytesIO(img_data))
    # img.save('r3_out_map.png')

    return meetingPoint.tolist()

def checkUserID(inputUserID):

    # inputUserID range : 1 ~ 1083
    if inputUserID < 1 or inputUserID > 1083:
        return False
    else:
        return True

def checkCategory(inputCategory):

    # every category type given
    CategoryType = df['VenueCategoryName'].value_counts().index

    # If a CategoryName contains characters entered by the user, return the exact CategoryName
    for _type in CategoryType:
        if inputCategory.strip() in _type:
            inputCategory = _type
            return inputCategory

    # If there is no matching category, return false
    return False
