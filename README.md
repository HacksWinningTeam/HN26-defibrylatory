# Misja AED – dane na ratunek

## Co to jest

Portal **dane.gov.pl rozszerzony o moduł agregacji danych**.

Dane o defibrylatorach AED są w portalu rozproszone w wielu zbiorach różnych instytucji, każdy w innym formacie. Nasz moduł:

1. **Definiuje standardy danych.** Standard to zestaw reguł dla jednej grupy danych: pola wymagane, zalecane i opcjonalne, typy, słowniki wartości, wzorce oraz reguła scalania duplikatów. Każdy standard opisuje jeden plik JSON.
2. **Waliduje każdy nowy plik.** Plik niezgodny ze standardem jest odrzucany, a portal pokazuje błędne wiersze i pola.
3. **Agreguje dane automatycznie.** Dane z przyjętego pliku trafiają do wspólnego zbioru publikowanego w portalu (tabela, mapa, CSV, XLSX, GeoJSON, API). Duplikaty z różnych źródeł są scalane, a każdy rekord wskazuje swoje źródła.

Mechanizm jest **uniwersalny**. Działają dwa standardy: **defibrylatory AED** (18 776 urządzeń z 6 źródeł) i **żłobki** (85 placówek z 8 instytucji). Kolejną grupę danych dodaje się nowym plikiem standardu, bez programowania.

Dodatkowo **publiczna mapa AED** pokazuje mieszkańcom najbliższy defibrylator. Dane pobiera prosto z API portalu.

Film demonstracyjny (2 min): [docs/demo/video/misja-aed-demo.mp4](docs/demo/video/misja-aed-demo.mp4)

## Wersja online

| Co | Adres |
|---|---|
| Mapa AED dla mieszkańców | http://2.29.205.102:3002/ |
| Portal dane.gov.pl z modułem | https://mcod.2.29.205.102.sslip.io/pl |
| Wspólny zbiór AED | https://mcod.2.29.205.102.sslip.io/pl/dataset/4217 |
| Wspólny zbiór żłobków | https://mcod.2.29.205.102.sslip.io/pl/dataset/4226 |
| Wzorcowy zakres danych AED (XLSX) | https://api.mcod.2.29.205.102.sslip.io/1.4/aed/schema.xlsx |
| Panel administracyjny: standardy danych | https://admin.mcod.2.29.205.102.sslip.io/aed/datastandard/ |
| API standardów | https://api.mcod.2.29.205.102.sslip.io/1.4/standards |

Logowanie do panelu: `admin@mcod.local` / `testadmin123!` (konto testowe na czas oceny).

**Jak sprawdzić przepływ:** w panelu dodaj zasób z plikiem do zbioru „Defibrylatory zlokalizowane w Mieście Krosno” lub „Żłobki publiczne”. Przykładowe pliki są w [docs/demo/samples/](docs/demo/samples/): `*-krosno-nowe-bledny.csv` zostanie odrzucony, a `*-krosno-nowe-poprawiony.csv` po ok. minucie trafi do wspólnego zbioru.

**Walidacja przez API**, bez logowania:

```bash
curl -F file=@docs/demo/samples/aed-krosno-nowe-bledny.csv https://api.mcod.2.29.205.102.sslip.io/1.4/aed/validate
curl -F file=@docs/demo/samples/zlobki-krosno-nowe-bledny.csv https://api.mcod.2.29.205.102.sslip.io/1.4/standards/zlobki-pl/validate
```

## Uruchomienie lokalne

Wymagania: Linux, Docker z Compose, ok. 16 GB RAM, wolne porty 80, 443 i 3000.

### 1. Portal dane.gov.pl z modułem

Kod portalu dane.gov.pl umieść w katalogu `dane-gov-pl/` (podkatalogi `backend_latest/` i `frontend_latest/`). Katalog jest pominięty w repozytorium. Nie modyfikujemy kodu portalu: nasz moduł (`fork-config/mcod_aed/`) i konfiguracja są podpinane przez `fork-config/setup.sh`.

```bash
# jednorazowo
echo '127.0.0.1 mcod.local api.mcod.local admin.mcod.local cms.mcod.local aed.mcod.local' | sudo tee -a /etc/hosts
sudo sysctl -w vm.max_map_count=262144

fork-config/setup.sh        # budowa i start portalu (pierwszy raz ok. 25 min)
fork-config/aed-demo.sh     # import zbiorów AED z dane.gov.pl i OpenStreetMap + agregacja
                            # (--offline: z kopii zapisanej w repozytorium)

# standard „Żłobki”
docker exec mcod-admin python manage.py aed_load_standard
docker exec mcod-admin python manage.py aed_import_sources --standard zlobki-pl
docker exec mcod-admin python manage.py aed_aggregate --standard zlobki-pl
```

Adresy: https://mcod.local (portal), https://admin.mcod.local (panel, login jak wyżej), https://api.mcod.local/1.4/standards (API). Certyfikat jest lokalny, więc przeglądarka poprosi o jego akceptację.

Kolejne uruchomienia: `fork-config/start.sh`, zatrzymanie: `fork-config/stop.sh`. Szczegóły: [fork-config/README.md](fork-config/README.md).

### 2. Mapa AED (Next.js)

```bash
make up                     # http://localhost:3000 (dane z https://api.mcod.local)
```

## Struktura repozytorium

| Katalog | Zawartość |
|---|---|
| `fork-config/mcod_aed/` | moduł portalu: standardy, walidacja, konwersja, scalanie, agregacja, API |
| `fork-config/mcod_aed/standards/` | definicje standardów w JSON (AED jest w kodzie: `schema.py`) |
| `fork-config/` | konfiguracja i skrypty uruchomienia portalu |
| `frontend/` | publiczna mapa AED (Next.js) |
| `docs/deliverables/` | wzorcowy zakres danych AED: XLSX, szablon CSV, JSON Schema |
| `docs/demo/` | film, przykładowe pliki, zrzuty ekranu |
| `docs/` | brief, architektura, decyzje projektowe, plan |
