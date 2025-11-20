Prosta instrukcja dotycząca uruchomienia automatyzacji
--
1. Przejdź do Variables.robot - ${FLASHSCORE_URL} -> upewnij się, że jest ustawione na flashscore.pl (dla polskich selektorów)
2. Należy zainstalować wszystkie biblioteki z pliku requirements.txt - pip install -r requirements.txt
3. ${BROWSER} - Ustaw na przeglądarkę z której korzystasz np. Chrome czy Firefox
5. Następnie upewnij się, że plik input.json ma następującą strukturę

```json
{
  "footballFixturesAutomationInput": [
    {
      "date": "2025-11-03",
      "country": "Polska",
      "leagueName": "Ekstraklasa",
      "latitude": 52.23,
      "longitude": 21.01
    },
    {
      "date": "2025-11-04",
      "country": "Anglia",
      "leagueName": "Premier League",
      "latitude": 51.50,
      "longitude": -0.12
    }
  ]
}
```

5. do uruchomienia automatyzacji należy wpisać komendę - robot tests/FootballFixtures.robot
