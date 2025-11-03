*** Settings ***
Resource    ../resources/Variables.robot
Resource    ../resources/Keywords.robot

Library    ../src/weather_api.py    WITH NAME    WeatherAPI
Library    ../src/excel_writer.py    WITH NAME    ExcelWriter

*** Test Cases ***
Football Fixtures Automation
    Open Browser Once
    ${input_files}=    List Files In Directory    ${INPUT_FOLDER}    *.json
    FOR    ${file}    IN    @{input_files}
        ${records}=    Read Input JSON    ${INPUT_FOLDER}/${file}
        FOR    ${record}    IN    @{records}
            ${folder}=    Create Output Folder    ${record['leagueName']}
            ${table}=     Get League Table        ${record['leagueName']}

            ${weather}=    WeatherAPI.Get Weather    ${record['latitude']}    ${record['longitude']}

            ExcelWriter.Write Excel File    ${folder}    ${record}    ${table}    ${weather}
            ExcelWriter.Write Weather Json  ${folder}    ${weather}
        END
    END
    Close Browser
