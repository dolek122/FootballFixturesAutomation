*** Settings ***
Library           SeleniumLibrary
Library           OperatingSystem
Library           JSONLibrary
Library           Collections
Library           DateTime
Library           String
Library           ../src/weather_api.py
Library           ../src/excel_writer.py

*** Variables ***
${FLASHSCORE_URL}    https://www.flashscore.com
${BROWSER}           Chrome
${TIMEOUT}           5s

*** Keywords ***
Open Browser Once
    Open Browser    ${FLASHSCORE_URL}    ${BROWSER}
    Maximize Browser Window
    Run Keyword And Ignore Error    Click Button    id:onetrust-accept-btn-handler

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
    ${success}=    Navigate To League Page    ${leagueName}
    Run Keyword If    not ${success}    Fail    Could not find league: ${leagueName}
    Ensure Standings Tab Active
    ${table}=    Parse Standings Table
    RETURN    ${table}

Get Weather Data
    [Arguments]    ${latitude}    ${longitude}
    ${weather}=    WeatherAPI.get_weather    ${latitude}    ${longitude}
    RETURN    ${weather}

Navigate To League Page
    [Arguments]    ${leagueName}
    ${direct_success}=    Try Direct URLs    ${leagueName}
    Return From Keyword If    ${direct_success}    ${True}
    ${search_success}=    Search For League    ${leagueName}
    RETURN    ${search_success}

Try Direct URLs
    [Arguments]    ${league_name}
    ${league_slug}=    Convert To Lower Case    ${league_name}
    ${league_slug}=    Replace String    ${league_slug}    ${SPACE}    -

    &{mappings}=    Create Dictionary
    ...    ekstraklasa=poland/ekstraklasa
    ...    premier-league=england/premier-league
    ...    pko-bp=poland/ekstraklasa

    ${path}=    Get From Dictionary    ${mappings}    ${league_slug}    default=${EMPTY}
    @{attempts}=    Create List    ${path}    poland/${league_slug}    england/${league_slug}    spain/${league_slug}

    FOR    ${attempt}    IN    @{attempts}
        Continue For Loop If    '${attempt}' == '${EMPTY}'
        Go To    https://www.flashscore.com/football/${attempt}/standings/
        ${is_valid}=    Check If Page Is Valid
        Return From Keyword If    ${is_valid}    ${True}
    END
    RETURN    ${False}

Search For League
    [Arguments]    ${league_name}
    Click Element    css:.header__buttonIcon--search, .searchIcon
    Input Text    css:input[type='search']    ${league_name}
    Sleep    1s

    ${result_locator}=    Set Variable    xpath://div[contains(@class,'searchResult')]//a[1]
    Wait Until Element Is Visible    ${result_locator}    timeout=${TIMEOUT}
    Click Element    ${result_locator}

    ${is_valid}=    Check If Page Is Valid
    RETURN    ${is_valid}

Check If Page Is Valid
    ${status}=    Run Keyword And Return Status    Wait Until Element Is Visible    css:.ui-table, .standings    timeout=3s
    RETURN    ${status}

Ensure Standings Tab Active
    ${url}=    Get Location
    ${needs_standings}=    Run Keyword And Return Status    Should Not Contain    ${url}    standings

    IF    ${needs_standings}
        ${standings_btn}=    Run Keyword And Return Status    Click Element    xpath://a[contains(text(),'Standings') or contains(text(),'Tabela')]
        Run Keyword If    not ${standings_btn}    Go To    ${url}standings/
        Wait Until Element Is Visible    css:.ui-table    timeout=${TIMEOUT}
    END

Parse Standings Table

    Wait Until Page Contains Element    css:.ui-table    timeout=10s
    Execute Javascript    window.scrollTo(0, 300)
    Sleep    1s

    @{rows_data}=    Create List
    @{rows}=    Create List
    @{rows}=    Get WebElements    css:.ui-table__row
    ${count}=   Get Length    ${rows}

    IF    ${count} == 0
        Log    Nie znaleziono po .ui-table__row    WARN
        @{rows}=    Get WebElements    xpath://div[contains(@class, 'ui-table')]//div[contains(@class, 'row')]
        ${count}=   Get Length    ${rows}
    END

    IF    ${count} > 0
        ${first_text}=    Get Text    ${rows}[0]
        Log    Przykładowy tekst wiersza: ${first_text}
    END

    FOR    ${row}    IN    @{rows}
        ${text}=    Get Text    ${row}
        ${row_dict}=    Parse Row Text    ${text}

        Run Keyword If    $row_dict is not None    Append To List    ${rows_data}    ${row_dict}
    END

    ${data_count}=    Get Length    ${rows_data}
    Run Keyword If    ${data_count} == 0    Fail    Nie udało się pobrać żadnych danych z tabeli.

    RETURN    ${rows_data}

Parse Row Text
    [Arguments]    ${full_text}

    ${clean_text}=    Replace String    ${full_text}    \n    ${SPACE}
    ${is_header}=    Evaluate    'MP' in '''${clean_text}''' or 'Mecze' in '''${clean_text}''' or 'Team' in '''${clean_text}'''
    Return From Keyword If    ${is_header}    ${None}
    @{parts}=    Split String    ${clean_text}    ${SPACE}
    ${count}=    Get Length    ${parts}
    Return From Keyword If    ${count} < 4    ${None}
    ${points}=    Set Variable    ${None}

    FOR    ${i}    IN RANGE    1    ${count}
        ${idx}=    Evaluate    -${i}
        ${item}=   Get From List    ${parts}    ${idx}

        ${is_digit}=    Evaluate    '${item}'.isdigit()

        IF    ${is_digit}
            ${points}=    Set Variable    ${item}
            BREAK
        END
    END

    Return From Keyword If    '${points}' == '${None}'    ${None}

    ${games}=    Set Variable    ${None}
    ${team_end_index}=    Set Variable    1

    FOR    ${index}    IN RANGE    1    ${count}-1
        ${item}=    Get From List    ${parts}    ${index}

        ${is_digit}=    Evaluate    '${item}'.isdigit()
        ${is_games}=    Evaluate    ${is_digit} and 0 <= int('${item}') <= 50

        IF    ${is_games}
            ${games}=    Set Variable    ${item}
            ${team_end_index}=    Set Variable    ${index}
            BREAK
        END
    END

    Return From Keyword If    '${games}' == '${None}'    ${None}

    ${first_part}=    Get From List    ${parts}    0
    ${is_position}=   Evaluate    '.' in '${first_part}'
    ${start_index}=   Set Variable If    ${is_position}    1    0
    ${team_parts}=    Get Slice From List    ${parts}    ${start_index}    ${team_end_index}
    ${team_name}=     Evaluate    " ".join($team_parts)

    Return From Keyword If    '${team_name}' == '${EMPTY}'    ${None}

    ${result}=    Create Dictionary    Club=${team_name}    Games=${games}    Points=${points}
    RETURN    ${result}

WaitForTable
    Wait Until Page Contains Element    css:.ui-table, .table    timeout=10s
    Execute Javascript    window.scrollTo(0, 200)