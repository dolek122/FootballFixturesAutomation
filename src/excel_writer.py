import os
import json
from openpyxl import Workbook
from robot.api.deco import keyword
from datetime import datetime

@keyword
def write_excel_file(folder, record, table, weather):

    wb = Workbook()
    ws = wb.active
    ws.title = "LeagueData"

    ws.append([
        'Date', 'Country', 'LeagueName', 'Latitude', 'Longitude',
        'Temperature [°C]', 'Temperature [°F]'
    ])

    ws.append([
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        record.get('country', ''),
        record.get('leagueName', ''),
        record.get('latitude', ''),
        record.get('longitude', ''),
        weather.get('celsius', ''),
        weather.get('fahrenheit', '')
    ])

    ws.append([])
    ws.append(['Position', 'Club', 'Games', 'Points'])

    for index, row in enumerate(table, start=1):
        ws.append([
            index,
            row.get('Club', ''),
            row.get('Games', ''),
            row.get('Points', '')
        ])

    excel_file_path = os.path.join(folder, 'results.xlsx')
    wb.save(excel_file_path)

@keyword
def write_weather_json(folder, weather):
    json_file_path = os.path.join(folder, 'weather.json')
    full_response = weather.get('full_response', weather)
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(full_response, f, indent=4, ensure_ascii=False)
