""" CrashTrakr is a test data retrieval tool built to work together 
    with Jenkins test automation projects.
    Copyright (C) 2017 Cosmin Ștefănică

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib
import pickle
import datetime
import os
import json

def loadTestData(project_code):
    """Loads the serialized pickle file that holds all the data we have on the test runs.

    Args:
        project_code: The internal code to the project we wish to load data for.
    """

    with open ("CrashTrakr_data_" + project_code, mode="rb") as test_data_file:
        test_data = pickle.load(test_data_file)
        print(test_data)
    return test_data

def plotTestData(project_code, plot_position, night_mode):
    """Plots the serialized test data we have saved.

    Args:
        project_code: The internal code to the project we wish to load data for.
        plot_position: matplotlib specific plot position. Available values: 311/312/313
    """

    failedTests = []
    builds = []
    completedTests = []
    test_data = []

    color_completed = "#18B5E8"
    color_failed = "#E53020"
    contour_completed = "#0BA7D6"
    contour_failed = "#BA1200"
    shown_builds = 15
    
    if night_mode:
        title_color = "white"
        axis_color = "white"
        tick_color = "white"
        plot_color = ".3"
    else:
        title_color = "black"
        axis_color = "black"
        tick_color = "black"
        plot_color = ".9"

    test_data = loadTestData(project_code)
    for item in test_data:
        builds.append(item[0])
        completedTests.append(item[1])
        failedTests.append(item[2])

    plt.subplot(plot_position, facecolor=plot_color).set_title(project_code, color=title_color)
    plt.axis([max(builds)-shown_builds+1, max(builds) + 5, 0, max(completedTests) + 10], color=axis_color)
    plt.grid(True,linewidth="0.5")
    plt.xticks(builds[0:shown_builds],color=tick_color)
    plt.yticks(color=tick_color)

    plt.fill_between(builds[0:shown_builds], completedTests[0:shown_builds], color=color_completed, antialiased=True)
    plt.fill_between(builds[0:shown_builds], failedTests[0:shown_builds], color=color_failed, antialiased=True)
    plt.plot(builds[0:shown_builds], completedTests[0:shown_builds], color=contour_completed, antialiased=True, linewidth="0.5")
    plt.plot(builds[0:shown_builds], failedTests[0:shown_builds], color=contour_failed, antialiased=True, linewidth="0.5")

    failed_patch = mpatches.Patch(color=color_failed, label="Failed Tests: " + str(test_data[0][2]))
    completed_patch = mpatches.Patch(color=color_completed, label="Completed Tests: " + str(test_data[0][1]))
    builds_patch = mpatches.Patch(color="gray", label="Last build no.: " + str(test_data[0][0]))
    generated_patch = mpatches.Patch(color="gray", label="Generated at: " + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))

    plt.legend(handles=[failed_patch, completed_patch, builds_patch, generated_patch])

def loadConfig():
    """Loads the projects from an external config file"""
    if os.path.isfile("CrashConfig.json"):
        project_data = json.load(open("CrashConfig.json"))
        return project_data
    else:
        return -1

def printLicense():
    print(  
        "CrashTrakr  Copyright (C) 2017 Cosmin Ștefănică\n\n"+
        "This program comes with ABSOLUTELY NO WARRANTY;\n"+
        "This is free software, and you are welcome to redistribute it\n"+
        "under certain conditions imposed by the MIT license."
        )

def main():
    now = datetime.datetime.now()
    print(now)
    night_mode = False
    printLicense()
    matplotlib.rcParams["toolbar"] = "None"

    if int(now.hour) in range(10,16):
        plt.figure(facecolor=".8")
        night_mode = False
    else:
        plt.figure(facecolor=".2")
        night_mode = True

    project_data = loadConfig()
    available_projects = []
    for project in project_data["Projects"]:
        available_projects.append(project["Code"])

    position = 311
    for project_code in available_projects:
        plotTestData(project_code, position, night_mode)
        position = position + 1
    plt.tight_layout(pad=0, w_pad=0, h_pad=0)
    mng = plt.get_current_fig_manager()
    mng.full_screen_toggle()
    plt.show()

if __name__ == "__main__":
    main()
