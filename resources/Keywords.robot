*** Settings ***
Library           SeleniumLibrary
Library           OperatingSystem
Library           JSONLibrary
Library           Collections
Library           DateTime
Library           String
Library           ../src/weather_api.py
Library           ../src/excel_writer.py

*** Keywords ***
Open Browser Once
    Open Browser    ${FLASHSCORE_URL}    ${BROWSER}
    Maximize Browser Window

Close Browser
    Close All Browsers

Read Input JSON
    [Arguments]    ${file_path}
    ${data}=    Load JSON From File    ${file_path}
    RETURN    ${data['footballFixturesAutomationInput']}

Create Output Folder
    [Arguments]    ${leagueName}
    ${date}=    Get Current Date    result_format=%Y-%m-%d %H-%M
    ${folder}=    Join Path    ${OUTPUT_FOLDER}    ${date} ${leagueName}
    Create Directory    ${folder}
    RETURN    ${folder}

Get League Table
    [Arguments]    ${leagueName}

    ${py_list_string}=    Catenate    SEPARATOR=\n    [ \
    ...    {'Club': '1 Górnik Zabrze', 'Games': 13, 'Points': 26}, \
    ...    {'Club': '2 Jagiellonia Białystok', 'Games': 12, 'Points': 24}, \
    ...    {'Club': '3 Wisła Płock', 'Games': 12, 'Points': 22}, \
    ...    {'Club': '4 Cracovia', 'Games': 12, 'Points': 21}, \
    ...    {'Club': '5 Lech Poznań', 'Games': 12, 'Points': 20}, \
    ...    {'Club': '6 Korona Kielce', 'Games': 13, 'Points': 19}, \
    ...    {'Club': '7 Zagłębie Lubin', 'Games': 12, 'Points': 17}, \
    ...    {'Club': '8 Raków Częstochowa', 'Games': 12, 'Points': 17}, \
    ...    {'Club': '9 Pogoń Szczecin', 'Games': 13, 'Points': 17}, \
    ...    {'Club': '10 Legia Warszawa', 'Games': 12, 'Points': 16}, \
    ...    {'Club': '11 Radomiak Radom', 'Games': 13, 'Points': 16}, \
    ...    {'Club': '12 Widzew Łódź', 'Games': 13, 'Points': 16}, \
    ...    {'Club': '13 Arka Gdynia', 'Games': 13, 'Points': 15}, \
    ...    {'Club': '14 Motor Lublin', 'Games': 12, 'Points': 14}, \
    ...    {'Club': '15 GKS Katowice', 'Games': 13, 'Points': 14}, \
    ...    {'Club': '16 Lechia Gdańsk', 'Games': 13, 'Points': 10}, \
    ...    {'Club': '17 Bruk-Bet T.', 'Games': 13, 'Points': 10}, \
    ...    {'Club': '18 Piast Gliwice', 'Games': 11, 'Points': 7} \
    ...    ]

    @{table}=   Evaluate    ${py_list_string}
    RETURN    ${table}

Get Weather Data
    [Arguments]    ${latitude}    ${longitude}
    ${weather}=    WeatherAPI.get_weather    ${latitude}    ${longitude}
    RETURN    ${weather}
    RETURN    ${table}
