import pandas as pd
from flask import Flask, request, render_template, redirect, flash
import KDSP_Task3_V1 as kdsp

from flask_wtf import FlaskForm
from wtforms import IntegerField, FloatField, FieldList, FormField
from wtforms.validators import DataRequired

class AForm(FlaskForm):
    uid = IntegerField('uid', validators=[DataRequired()])
    lat = FloatField('lat', validators=[DataRequired()])
    lon = FloatField('lon', validators=[DataRequired()])

class MainForm(FlaskForm):
    forms = FieldList(FormField(AForm), min_entries=5, max_entries=5)

app = Flask(__name__)
app.secret_key = "super secret key"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/recommend1')
def recommend1():
    return render_template('recommend1.html')

@app.route('/recommend2')
def recommend2():
    return render_template('recommend2.html')

@app.route('/recommend3')
def recommend3():
    form = MainForm()
    return render_template('recommend3.html', form=form)

@app.route('/map')
def map():
    return render_template('r3_out_map.html')


@app.route('/method1', methods=['GET', 'POST'])
def method1():
    if request.method == 'POST':

        # set default uid ( = 1)
        if request.form["uid"] == '': inputUserID = 1
        else: inputUserID = int(request.form["uid"])
        inputCategory = request.form["category"]

        # if the input does not meet the criteria, redirect back to recommend1.html
        if kdsp.checkUserID(inputUserID) is False:
            flash('UserID should be in 1 to 1083', 'error')
            return redirect('recommend1')

        if (inputCategory := kdsp.checkCategory(inputCategory)) is False:
            flash('Enter a correct category name', 'error')
            return redirect('recommend1')

        # implement recommendation function
        recommended = kdsp.recommend_1_with_param(inputUserID, inputCategory)
        return render_template('recommend1_out.html', recommended = recommended)

@app.route('/method2', methods=['POST'])
def method2():

    # set default uid ( = 1)
    if request.form["uid"] == '':
        inputUserID = 1
    else:
        inputUserID = int(request.form["uid"])

    # if the input does not meet the criteria, redirect back to recommend2.html
    if kdsp.checkUserID(inputUserID) is False:
        flash('UserID should be in 1 to 1083', 'error')
        return redirect('recommend2')

    # implement recommendation function
    recommended = kdsp.recommend_2_with_param(inputUserID)
    return render_template('recommend2_out.html', recommended = recommended)



@app.route('/method3', methods=['POST'])
def method3():

    # get values from form fields
    form_keys = request.form.keys()
    inputUserIDs = list()
    data = list()
    lats = list()
    lons = list()

    for key in form_keys:
        if 'uid' in key:
            inputUserIDs.append(int(request.form.get(key)))
        elif 'lat' in key:
            lats.append(float(request.form.get(key)))
        elif 'lon' in key:
            lons.append(float(request.form.get(key)))

    # if the input does not meet the criteria, redirect back to recommend3.html
    for id in inputUserIDs:
        if kdsp.checkUserID(id) is False:
            flash('UserID should be in 1 to 1083', 'error')
            return redirect('recommend3')

    for i in range(5):
        if abs(lats[i])<=90 and abs(lons[i])<=180:
            data.append([lats[i], lons[i]])
        elif abs(lats[i]) > 90:
            flash('Latitude should be in -90 to 90', 'error')
            return redirect('recommend3')
        else:
            flash('Longitude should be in -180 to 180', 'error')
            return redirect('recommend3')

    # implement recommendation function
    inputLocs = pd.DataFrame(data, columns=['Latitude', 'Longitude'])
    recommended = kdsp.recommend_3_with_param(inputUserIDs, inputLocs)

    return render_template('recommend3_out.html', recommended = recommended)


if __name__ == '__main__':
    app.run(debug=True)