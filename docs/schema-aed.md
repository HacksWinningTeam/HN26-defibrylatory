# Wzorcowy zakres danych o defibrylatorach AED (`aed-pl` v1.0.0)

> Source of truth: `backend/apps/aed/schema.py` (DEC-004). Generated artefacts: `docs/deliverables/` (`aed-schema.xlsx` — submission deliverable, `aed-template.csv`, `aed-schema.json` — JSON Schema 2020-12, `table-schema.json` — Frictionless Table Schema) and live at `/api/schema-standard/...`.

## Design principles

1. **Low entry barrier, high value.** Only 8 fields are *wymagane* (required): `id_aed`, `nazwa`, `szerokosc_geograficzna`, `dlugosc_geograficzna`, `miejscowosc`, `dostep`, `zrodlo`, `data_aktualizacji`. Everything a small municipality already has (see Krosno/Marki: coordinates + name + address) covers the required set. The *zalecane* (recommended) fields are what saves time in an emergency. *Opcjonalne* (optional) fields support maintenance.
2. **Answer the three questions from the brief**: *where is the nearest AED* (coordinates + `opis_lokalizacji`), *is it accessible* (`dostep`, `godziny_dostepnosci`, `zabezpieczenie`: locked with a key or not, which is the 3 March Warsaw story), *does it work* (`status`, `data_ostatniego_przegladu`, expiry dates).
3. **Reuse existing standards instead of inventing new ones**: WGS84 coordinates; TERYT address split (`cecha_ulicy`, `nazwa_ulicy`, `nr_budynku`, `kod_terc`, `kod_simc`) already used by Legionowo on dane.gov.pl; ISO 8601 dates; OpenStreetMap `opening_hours` syntax; each field documents the matching OSM tag, so the community OSM data maps 1:1.
4. **Machine-readable and portal-friendly**: ASCII snake_case column names, UTF-8 CSV with comma separator, one row = one device, stable `id_aed`, controlled vocabularies (`dostep`, `zabezpieczenie`, `status`, `cecha_ulicy`, `wojewodztwo`) and validation rules (ranges for Poland, regex for postcode/TERYT), available as JSON Schema and Table Schema for automatic validation.
5. **Provenance in every record** (`zrodlo`, `zrodlo_url`, `data_aktualizacji`, `zweryfikowany`) so the merged national dataset stays traceable to each data owner.

## Field groups

| Group | Fields (obligation: **W** required, Z recommended, o optional) |
| --- | --- |
| Identyfikacja | **id_aed W**, **nazwa W** |
| Lokalizacja | **szerokosc_geograficzna W**, **dlugosc_geograficzna W**, opis_lokalizacji Z, w_budynku Z, pietro o, wojewodztwo o, powiat o, gmina o, **miejscowosc W**, kod_terc o, kod_simc o, cecha_ulicy Z, nazwa_ulicy Z, nr_budynku Z, nr_lokalu o, kod_pocztowy Z |
| Dostępność | **dostep W**, godziny_dostepnosci Z, zabezpieczenie Z, instrukcja_dojscia o |
| Urządzenie | status Z, data_ostatniego_uzycia o, producent o, model o, numer_seryjny o, data_instalacji o, elektrody_pediatryczne o, data_ostatniego_przegladu Z, data_nastepnego_przegladu Z, data_waznosci_elektrod o, data_waznosci_elektrod_pediatrycznych o, data_waznosci_baterii o |
| Dysponent i kontakt | dysponent Z, telefon_kontaktowy o, email_kontaktowy o |
| Metadane rekordu | **data_aktualizacji W**, zweryfikowany o, **zrodlo W**, zrodlo_url o, uwagi o |

## Compatibility with the London AED schema (DEC-007)

Mentor reference: the London AED dataset ("The Circuit"). Every element of that model has a counterpart in `aed-pl` except three that are deliberately excluded from open data:

| London schema | `aed-pl` |
| --- | --- |
| `id`, `serialNumber`, `manufacturer`, `model` | `id_aed`, `numer_seryjny`, `producent`, `model` |
| `status` (active, pending_check, maintenance, out_of_service, stolen, retired) | `status` (sprawny, do_weryfikacji, w_serwisie, niesprawny, skradziony, wycofany, nieznany) |
| `lastDeployedAt`, `installationDate`, `updatedAt` | `data_ostatniego_uzycia`, `data_instalacji`, `data_aktualizacji` |
| `isOutdoor`, `hasPediatricCapability` | `w_budynku` (inverse), `elektrody_pediatryczne` |
| `access.type`, `access.schedule`, `access.closedDates` | `dostep` + `godziny_dostepnosci` (opening_hours syntax covers weekly schedule and exceptions, e.g. `Mo-Fr 08:00-16:00; PH off`) |
| `access.isLocked`, `access.notes` | `zabezpieczenie` (6 values, finer than a boolean), `instrukcja_dojscia` |
| `location.*` (buildingName, streetAddress, city, postalCode, floor, placementDetails, coordinates) | `nazwa`, TERYT address fields, `miejscowosc`, `kod_pocztowy`, `pietro`, `opis_lokalizacji`, `szerokosc_geograficzna` / `dlugosc_geograficzna` |
| `owner.organizationName`, `phone`, `email` | `dysponent`, `telefon_kontaktowy`, `email_kontaktowy` |
| `consumables[]` | `data_waznosci_baterii`, `data_waznosci_elektrod`, `data_waznosci_elektrod_pediatrycznych` |
| `maintenanceLogs[]` | `data_ostatniego_przegladu`, `data_nastepnego_przegladu` (full log stays with the device owner) |
| **Not published:** `access.accessCode` | security: a public cabinet code defeats the lock — only `zabezpieczenie = szafka_na_kod`; the code is given by the 112 dispatcher |
| **Not published:** `owner.contactPerson`, `maintenanceLogs.inspectorName` | personal data (RODO) — organisation contacts only |
| **Not adopted:** `location.what3words` | proprietary service; coordinates are the open standard |

Why flat instead of nested: dane.gov.pl previews tables and maps from flat CSV/XLSX, and municipalities maintain spreadsheets — one row = one device.

## How the existing sources map onto the schema (dane.gov.pl, checked 2026-11-21)

| Source (dane.gov.pl) | Format | Source columns → standard fields | Gaps / problems |
| --- | --- | --- | --- |
| Krosno (dataset 3624) | CSV `,` | `Długość geograficzna`→`dlugosc_geograficzna`, `Szerokość geograficzna`→`szerokosc_geograficzna`, `Lokalizacja`→`nazwa`, `Adres`→ split into `cecha_ulicy`/`nazwa_ulicy`/`nr_budynku`/`kod_pocztowy`/`miejscowosc`, `Numer Id`→`id_aed` | no access/hours/status; `Nazwa` is always "Defibrylator" |
| Marki (dataset 4955) | CSV + XLSX | same headers as Krosno | each row wrapped in quotes (broken CSV); values are **lat, lon** under lon/lat headers (swapped) |
| Przemyśl (dataset 4581) | CSV `;`, GeoJSON, JSON, GML | `name`→`nazwa`, `city`/`street`/`home_number`/`postcode`, `phone`, `geometry`→coordinates, `description` | long marketing description instead of location detail |
| Legionowo (dataset 40593) | CSV `,` | `nazwa`, `cecha_ulicy`, `nazwa_ulicy`, `nr_budynku`, `nr_lokalu`, `kod_pocztowy`, `miejscowosc`, `kod_terc`, `kod_simc`, `szerokosc_geograficzna`, `dlugosc_geograficzna` — almost 1:1 | `kod_terc` 6 digits (TERC gmina is 7: `1408011`); `cecha_ulicy` written as `ulica` instead of `ul.` |
| Warszawa (dataset 39512) | link to city catalogue | — | not a direct file; harvested only if a machine-readable resource is reachable |
| OpenStreetMap | Overpass JSON | `name`, `defibrillator:location`→`opis_lokalizacji`, `indoor`→`w_budynku`, `level`→`pietro`, `access`→`dostep`, `opening_hours`→`godziny_dostepnosci`, `operator`→`dysponent`, `phone`, `addr:*`, `description`→`instrukcja_dojscia` | volunteer data, no device status |

**Conclusion for the pitch:** every publisher uses different column names, separators, coordinate order and level of detail; none publishes access security, device status or inspection dates. The standard fixes this with one table, clear required minimum, and validators.
