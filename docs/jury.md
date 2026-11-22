# Misja AED – instrukcja dla jury

Rozwiązanie działa jako moduł wewnątrz portalu dane.gov.pl (kopia portalu na naszym serwerze) oraz jako publiczna mapa AED.

## Adresy i dostęp

| Co | Adres | Logowanie |
|---|---|---|
| Publiczna mapa AED (aplikacja dla obywateli) | http://2.29.205.102:3002/ | — |
| Portal dane.gov.pl (kopia z naszym modułem) | https://mcod.2.29.205.102.sslip.io | — |
| Panel administracyjny portalu | https://admin.mcod.2.29.205.102.sslip.io | `admin@mcod.local` / `testadmin123!` |
| API portalu | https://api.mcod.2.29.205.102.sslip.io/1.4/standards | — |

Konto administratora jest kontem testowym, przygotowanym tylko na czas oceny.

## Co warto sprawdzić (ok. 5 minut)

1. **Mapa AED.** Otwórz http://2.29.205.102:3002/ i zobacz najbliższy defibrylator. Kliknij pinezkę, żeby zobaczyć szczegóły urządzenia, przycisk „Prowadź” i źródła danych. Lokalizacja jest demonstracyjna: Bydgoskie Centrum Targowo-Wystawiennicze.
2. **Zbiory zbiorcze w portalu.** Oba zbiory publikuje sam portal i oba mają tabelę, CSV, XLSX i API.
   - Defibrylatory AED, ok. 18 776 urządzeń z 6 źródeł: https://mcod.2.29.205.102.sslip.io/pl/dataset/4217 (zasób CSV ma też zakładkę „Mapa”).
   - Żłobki i kluby dziecięce, 85 placówek z 8 instytucji: https://mcod.2.29.205.102.sslip.io/pl/dataset/4226
3. **Standardy danych.** Zaloguj się do panelu i otwórz https://admin.mcod.2.29.205.102.sslip.io/aed/datastandard/ (menu „Standardy danych”). Każdy standard ma pola, regułę scalania duplikatów, zbiór zbiorczy i przycisk „Uruchom agregację”.
4. **Walidacja → akceptacja → agregacja.** Dodaj nowy zasób (https://admin.mcod.2.29.205.102.sslip.io/resources/resource/add/), wybierz typ „plik” i wgraj plik do zbioru:
   - „Defibrylatory zlokalizowane w Mieście Krosno” (standard AED),
   - „Żłobki publiczne” (standard Żłobki).

   Plik z błędami zostanie odrzucony, a portal wskaże błędne wiersze i pola. Plik poprawny zostanie opublikowany, a po ok. 30–60 s jego dane trafią automatycznie do zbioru zbiorczego. Komunikat pojawi się na stronie zasobu po odświeżeniu.

   Przykładowe pliki są w repozytorium w katalogu `docs/demo/samples/`:
   - `aed-krosno-nowe-bledny.csv` / `aed-krosno-nowe-poprawiony.csv`
   - `zlobki-krosno-nowe-bledny.csv` / `zlobki-krosno-nowe-poprawiony.csv`
5. **API walidacji dla właścicieli danych.** Każdy może sprawdzić swój plik przed publikacją:

   ```bash
   curl -F file=@aed-krosno-nowe-bledny.csv https://api.mcod.2.29.205.102.sslip.io/1.4/aed/validate
   curl -F file=@zlobki-krosno-nowe-bledny.csv https://api.mcod.2.29.205.102.sslip.io/1.4/standards/zlobki-pl/validate
   ```

   Schemat standardu: `/1.4/standards/{kod}/schema`. Źródła zbioru zbiorczego: `/1.4/standards/{kod}/sources`. Kody standardów: `aed-pl`, `zlobki-pl`.

## Film demonstracyjny

`docs/demo/video/misja-aed-demo.mp4` pokazuje cały przepływ z napisami po polsku. Pojedyncze kroki są w `docs/demo/video/kroki/`.
