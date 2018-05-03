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

from urllib import request, parse
import urllib.request
import ast
import datetime
import os
import pickle
import subprocess
import sys
import psutil
import json

def checkLogExistence():
    """Checks to see if the CrashTrakr_Log file exists and creates it if it does
    not."""

    if not os.path.isfile("CrashTrakr_Log.txt"):
        log_start=["LOG START @ {0}\n".format(str(datetime.datetime.now()))]      
        log_file = open("CrashTrakr_Log.txt", mode="wt", encoding="utf-8")
        log_file.writelines(log_start)
        log_file.close()

def log(message, project_code="MAIN", message_type="Notice"):
    """Logs custom messages to a separate CrashTrakr_log.txt file.

    Args:
        message: The message we wish to log
        project_code: The internal code to the project we wish to save data for. 
            MAIN default if the log is not related to a project.
        message_type: The type of message we are logging.
            e.g.: Notice, Error, Warning
    """

    complete_message = "[{0}][{1}] {2}, {3}\n".format(message_type,
                                                     project_code, 
                                                     str(datetime.datetime.now()), 
                                                     message)

    checkLogExistence()
    log_file = open("CrashTrakr_Log.txt", mode="at+", encoding="utf-8")
    log_file.writelines(complete_message)
    log_file.close()

def printTestData(project_code):
    """Prints the available test data to the console.

    Args:
         project_code: The internal code to the project data we wish to show.
    """

    with open("CrashTrakr_data_" + project_code, mode="rb") as fp:
        log_data = pickle.load(fp)
    for log in log_data:
        print(log)

def saveTestData(project_code, last_build_number, completed_tests, failed_tests):
    """Saves the serialized pickle file that holds all the data we have on the 
    test runs for a specific project.

    Args:
        project_code: The internal code to the project we wish to save data for.
        data_to_be_saved: The test data we want to save.
    """
    if last_build_number == "-1":
        log("Data not logged", project_code, "HTTP Error")
    elif last_build_number == "-2":
        log("Data not logged", project_code, "URL Error")
    else:
        complete_data = [last_build_number, completed_tests, failed_tests]
        test_data = []
        if os.path.isfile("CrashTrakr_data_" + project_code):
            with open ("CrashTrakr_data_" + project_code, mode="rb") as data_file:
                test_data = pickle.load(data_file)
                log("Received test data from file!", project_code)
                
                data_file.close()

        if(test_data[0][0]) != last_build_number:
            test_data.insert(0, complete_data)

        with open("CrashTrakr_data_" + project_code, mode="wb") as data_file:
            pickle.dump(test_data, data_file)
            log("Test data saved succesfully!", project_code)
            data_file.close()

def loadTestData(project_code):
    """Loads the serialized pickle file that holds all the data we have on the 
    test runs.

    Args:
        project_code: The internal code to the project we wish to load data for.
    """

    with open ("CrashTrakr_data_" + project_code, mode="rb") as data_file:
        test_data = pickle.load(data_file)
        log("Received test data!", project_code)
        data_file.close()
    return test_data

def getProjectLink(project_code):
    """Gets the link to the Jenkins project with the specified internal project 
    code.

    Args:
        project_code: The internal code to the project we wish to check.

    Raises:
        ValueError: If the received project code is not in the available project
            list.
    """
    
    project_data = loadConfig()
    project_dictionary = {}

    for project in project_data["Projects"]:
        project_dictionary[project["Code"]] = project_data["ServerLink"] + project["Link"] + '/'

    if project_code not in project_dictionary:
        log("Project code '{0}' is unknown".format(project_code), 
            project_code, 
            "Error")
        raise ValueError("Project code is unknown!")

    return project_dictionary[project_code]

def getApiLink(project_code, version=-1, last_successful_build=False, last_build=False):
    """Generates the link to the Jenkins REST API that we use to get the test 
    results.

    Args:
        project_code: The internal code to the project we wish to check.
        version: The build number we wish to check.
        last_successful_build: Flag which when set to true, instructs the script to access the test results
        from the last succesful build.
        last_build: Flag which when set to true, instructs the script to access the test results
        from the last known build. Not recommended as a build might be in progress when the scripts are ran.

    Raises:
        TypeError: If the build number is not an integer.
    """

    if type(version) is not int:
        log("Version number must be an integer", project_code, "Error")
        raise TypeError("Version number must be an integer!")

    if version == (-1):
        if last_successful_build:
            return getProjectLink(project_code) + "lastSuccessfulBuild/testReport/api/python?tree=failCount,passCount,duration,skipCount"
        elif last_build:
            return getProjectLink(project_code) + "lastBuild/testReport/api/python?tree=failCount,passCount,duration,skipCount"
        else:
            return getProjectLink(project_code) + "lastCompletedBuild/testReport/api/python?tree=failCount,passCount,duration,skipCount"
    else:
        return getProjectLink(project_code) + str(version) + "/testReport/api/python?tree=failCount,passCount,duration,skipCount"

def getLastCompletedBuildNumber(project_code):
    """Sends a GET request to the REST API provided by Jenkins to see what the 
    last completed build ID is.

    Args:
        project_code: The internal code to the project we wish to check.
    """

    build_link = getProjectLink(project_code)+"lastCompletedBuild/api/python?tree=id"

    try:
        apiResponse = ast.literal_eval(urllib.request.urlopen(build_link).read().decode("windows-1252"))
    except urllib.error.HTTPError as HTTP_Error:
        log("Error fetching {0} last completed build number: {1}: {2}".format(project_code, HTTP_Error.code, HTTP_Error.reason),
            project_code,
            "HTTP Error")
        apiResponse = {"_class": "HTTP Error", "id": "-1"}

    except urllib.error.URLError as URL_Error:
        log("Error fetching {0} last completed build number. {1}".format(project_code, URL_Error.reason),
            project_code,
            "URL Error")
        apiResponse = {"_class": "URL Error", "id": "-2"}
    return int(apiResponse["id"])

def getLastBuildNumber(project_code):
    """Sends a GET request to the REST API provided by Jenkins to see what the 
    last build ID is.

    Args:
        project_code: The internal code to the project we wish to check.
    """

    build_link = getProjectLink(project_code)+"lastBuild/api/python?tree=id"

    try:
        apiResponse = ast.literal_eval(urllib.request.urlopen(build_link).read().decode("windows-1252"))
    except urllib.error.HTTPError as HTTP_Error:
        log("Error fetching {0} last build number: {1}: {2}".format(project_code, HTTP_Error.code, HTTP_Error.reason),
            project_code,
            "HTTP Error")
        apiResponse = {"_class": "HTTP Error", "id": "-1"}

    except urllib.error.URLError as URL_Error:
        log("Error fetching {0} last build number. {1}".format(project_code, URL_Error.reason),
            project_code,
            "URL Error")
        apiResponse = {"_class": "URL Error", "id": "-2"}
    return int(apiResponse["id"])

def compareBuildNumbers(project_code):
    lastSavedBuildNumber = loadTestData(project_code)[0][0]
    print("LastSavedIs")
    print(lastSavedBuildNumber)
    lastJenkinsBuildNumber = getLastCompletedBuildNumber(project_code)
    print("LastJenkinsIs")
    print(lastJenkinsBuildNumber)
    return lastJenkinsBuildNumber - lastSavedBuildNumber

def getApiTestResults(project_code, version=-1):
    """Sends a GET request to the REST API provided by Jenkins with the link 
    generated by the getApiLink method.

    Args:
        project_code: The internal code to the project we wish to check.
        version: The build number we wish to check.
    """

    try:
        apiResponse = ast.literal_eval(urllib.request.urlopen(getApiLink(project_code, version)).read().decode("windows-1252"))
    except urllib.error.HTTPError as HTTP_Error:
        log("Error fetching {0} test results: {1}: {2}".format(project_code, HTTP_Error.code, HTTP_Error.reason),
            project_code,
            "HTTP Error")
        apiResponse = {"_class": "HTTP Error", 
                       "duration": -1, 
                       "failCount": -1, 
                       "passCount": -1, 
                       "skipCount": -1}
    except urllib.error.URLError as URL_Error:
        log("Error fetching {0} test results. {1}".format(project_code, URL_Error.reason),
            project_code,
            "URL Error")
        apiResponse = {"_class": "URL Error", 
                       "duration": -1, 
                       "failCount": -1, 
                       "passCount": -1, 
                       "skipCount": -1}
    return apiResponse

def getPastTestResults(project_code, number_of_builds=6):
    """Gets the last test results for a certain project.

    Args:
        project_code: The internal code to the project we wish to check.
        number_of_builds: How many builds in the past we wish to get results for.

    Raises:
        TypeError: If the requested number of builds is not an integer.
    """

    complete_build_data = []

    if type(number_of_builds) is not int:
        log("Number of builds must be an integer",project_code,"Error")
        raise TypeError("Number_of_builds must be an integer!")

    for build in range(number_of_builds):
        complete_build_data.append(getApiTestResults(project_code, 
            getLastCompletedBuildNumber(project_code) - build))

    return complete_build_data

def consolePrintTestResults(project_code):
    """Prints the results got from the REST API to the console

    Args:
        project_code: The internal code to the project we wish to check.
    """
    
    test_results = getApiTestResults(project_code)
    saved_results = []

    if test_results["_class"] == "HTTP Error":
        print("=-=-=-=-=-=-=-HTTP-=-=-=-=-=-=-=\n"
              "Project Code: {0}\n".format(project_code)+
              "Total Tests: ???\n"+
              "Failed Tests: ???\n"+
              "Fail Percentage: ???%\n"+
              "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n\n")
        log("Console output, unknown results, HTTP Error", project_code)
        saveTestData(project_code, getLastCompletedBuildNumber(project_code), -1, -1)
        
    elif test_results["_class"] == "URL Error":
        print("=-=-=-=-=-=-=URL=-=-=-=-=-=-=\n"
              "Project Code: {0}\n".format(project_code)+
              "Total Tests: ???\n"+
              "Failed Tests: ???\n"+
              "Fail Percentage: ???%\n"+
              "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n\n")
        log("Console output, unknown results, URL Error", project_code)

    else:
        fail_percentage = test_results["failCount"] / (test_results["failCount"] + test_results["passCount"]) * 100
        total_tests = test_results["failCount"] + test_results["passCount"]
        print("=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n"
              "Project Code: {0}\n".format(project_code)+
              "Total Tests: {0}\n".format(total_tests)+
              "Failed Tests: {0}\n".format(test_results["failCount"])+
              "Fail Percentage: {0}%\n".format(format(fail_percentage, ".2f"))+
              "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=\n\n")
        log("Console output, known results", project_code)

        saveTestData(project_code, getLastCompletedBuildNumber(project_code), 
                    total_tests, 
                    test_results["failCount"])

def savePastTestResults(project_code, number_of_builds=0):

    test_data = getPastTestResults(project_code,number_of_builds)
    counter = number_of_builds
    for test_results in test_data:
        saved_results = []
        if test_results["_class"] is not "Error":
            fail_percentage = test_results["failCount"] / (test_results["failCount"] + test_results["passCount"]) * 100
            total_tests = test_results["failCount"] + test_results["passCount"]
            saveTestData(project_code, getLastCompletedBuildNumber(project_code)-counter, 
                        total_tests, 
                        test_results["failCount"])
            log("Loaded past test data, with known data",project_code)
        else:
            saveTestData(project_code, getLastCompletedBuildNumber(project_code)-counter, -1, -1)
            log("No test data available", project_code)
        counter = counter-1
        print(counter)

def populateFreshResults(project_code):
    """Populates the CrashTrakr test results in case we are running a fresh 
    instance with no previous data.

    Args:
        project_code: The internal code to the project data we wish to save.
    """

    maxBuild = getLastCompletedBuildNumber(project_code)
    for buildNumber in list(range(1 , maxBuild+1)):
        test_results = getApiTestResults(project_code, buildNumber)
        saved_results = []
        if test_results["_class"] is not "Error":
            fail_percentage = test_results["failCount"] / (test_results["failCount"] + test_results["passCount"]) * 100
            total_tests = test_results["failCount"] + test_results["passCount"]

            saved_results.append(buildNumber)
            saved_results.append(total_tests)
            saved_results.append(test_results["failCount"])
            
            print(saved_results)
            saveTestData(project_code, buildNumber, 
                    total_tests, 
                    test_results["failCount"])
        else:
            saved_results.append(buildNumber)
            saved_results.append(-1)
            saved_results.append(-1)
            print(saved_results)
            saveTestData(project_code, buildNumber, 
                    -1, 
                    -1)

def retryAutomatedTestBuild(project_code):
    """Retries the automated tests build if the previous build ended up with more errors than before.

    Args:
        project_code: The internal code to the project we wish to rebuild.
    """

    project_data = loadConfig()

    project_data = loadConfig()
    token_dictionary = {}

    for project in project_data["Projects"]:
        token_dictionary[project["Code"]] = project["BuildToken"]

    query_data = {  "token": token_dictionary[project_code],
                    "delay": 0}

    encoded_data = parse.urlencode(query_data).encode()
    req = request.Request(getProjectLink() + "/build", data=encoded_data)
    resp = request.urlopen(req)
    print(resp)

def compareTestResultsToPreviousBuild(project_code, current_failed_tests, threshold=100):
    if getApiTestResults(project_code) - getApiTestResults(project_code, getLastCompletedBuildNumber(project_code)-1) > threshold:
        return True

def startPlotter():
    """Starts the CrashTrakr_plot script that shows the data to the screen"""

    subprocess.Popen("CrashTrakr_plot.py", shell=True)

def killPlotter():
    """Searches for and closes the CrashTrakr_plot script that shows the data to
    the screen"""

    thisPID = os.getpid()
    for proc in psutil.process_iter():
        process = psutil.Process(proc.pid)
        pname = process.name()
        if pname == "python.exe" and proc.pid != thisPID:
            proc.terminate()
            log("Restarted plotter")
            break

def restartPlotter():
    """Restarts the CrashTrakr_plot script that shows data to the screen"""

    killPlotter()
    startPlotter()

def printLicense():
    print(  """CrashTrakr Copyright (C) 2018 Cosmin Ștefănică
This program comes with ABSOLUTELY NO WARRANTY;
This is free software, and you are welcome to redistribute it
under certain conditions imposed by the MIT license.\n\n""")
    log("Printed license to console.")

def loadConfig():
    """Loads the projects from an external config file"""
    if os.path.isfile("CrashConfig.json"):
        project_data = json.load(open("CrashConfig.json"))
        log("Loaded configuration data.")
        return project_data
    else:
        log("Config file not found, cannot load data.")

def main():
    project_data = loadConfig()
    available_projects = []
    for project in project_data["Projects"]:
        available_projects.append(project["Code"])

    printLicense()

    for project_code in available_projects:
        difference = compareBuildNumbers(project_code)
        print(difference)
        if difference == 0:
            consolePrintTestResults(project_code)
        if difference > 0:
            savePastTestResults(project_code,difference)
            consolePrintTestResults(project_code)
        printTestData(project_code)
        #populateFreshResults(project_code)
    restartPlotter()

if __name__ == "__main__":
    main()
