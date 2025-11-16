*** Settings ***
Library           SeleniumLibrary
Library           OperatingSystem
Library           JSONLibrary
Library           Collections
Library           DateTime
Library           String
Library           ../src/weather_api.py
Library           ../src/excel_writer.py
Library           ../src/flashscore_scraper.py    WITH NAME    FlashscoreScraper

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
    [Documentation]    Scrapes league table from flashscore.com for the given league name
    
    ${table}=    FlashscoreScraper.Get League Table    ${leagueName}
    RETURN    ${table}

Get Weather Data
    [Arguments]    ${latitude}    ${longitude}
    ${weather}=    WeatherAPI.get_weather    ${latitude}    ${longitude}
    RETURN    ${weather}
