"""Standard AED data schema ("wzorcowy zakres danych o defibrylatorach AED").

Single source of truth (DEC-004): the model columns, exports, API and every downloadable
artefact (xlsx, CSV template, JSON Schema, Table Schema) are generated from ``FIELDS``.

Conventions:
- column names: Polish, ASCII ``snake_case`` (no diacritics) - safe for every tool;
- coordinates: WGS84 (EPSG:4326), decimal degrees;
- address: TERYT-style split (``cecha_ulicy``, ``nazwa_ulicy``, ``nr_budynku``, ``kod_terc``,
  ``kod_simc``) as already used by AED publishers on dane.gov.pl (Legionowo);
- dates: ISO 8601 ``YYYY-MM-DD``; booleans: ``true`` / ``false``;
- availability hours: OpenStreetMap ``opening_hours`` syntax (e.g. ``24/7``).
"""

from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_NAME = "aed-pl"
SCHEMA_VERSION = "1.0.0"
SCHEMA_TITLE = "Wzorcowy zakres danych o defibrylatorach AED"
SCHEMA_TITLE_EN = "Standard data schema for AED defibrillators in Poland"
SCHEMA_DESCRIPTION = (
    "Jednolity zakres danych o automatycznych defibrylatorach zewnętrznych (AED) do "
    "udostępniania w portalu dane.gov.pl przez wszystkich dysponentów danych. "
    "Jeden wiersz = jedno urządzenie AED."
)

# Obligation levels (as in DCAT-AP: mandatory / recommended / optional).
REQUIRED = "wymagane"
RECOMMENDED = "zalecane"
OPTIONAL = "opcjonalne"
OBLIGATIONS = (REQUIRED, RECOMMENDED, OPTIONAL)

# Field types.
STRING = "string"
NUMBER = "number"
INTEGER = "integer"
BOOLEAN = "boolean"
DATE = "date"
TYPES = (STRING, NUMBER, INTEGER, BOOLEAN, DATE)

# Field groups (order = order of columns).
GROUPS = {
    "identyfikacja": "Identyfikacja",
    "lokalizacja": "Lokalizacja",
    "dostepnosc": "Dostępność",
    "urzadzenie": "Urządzenie",
    "dysponent": "Dysponent i kontakt",
    "metadane": "Metadane rekordu",
}

# Bounding box of Poland (used for validation of coordinates).
PL_LAT_MIN, PL_LAT_MAX = 49.0, 54.9
PL_LON_MIN, PL_LON_MAX = 14.1, 24.2


@dataclass(frozen=True)
class FieldSpec:
    """Specification of a single column of the standard AED schema."""

    name: str
    group: str
    type: str
    obligation: str
    label: str
    description: str
    description_en: str
    example: str | int | float | bool | None = None
    allowed_values: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    pattern: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    max_length: int | None = None
    osm_tag: str | None = None

    @property
    def required(self) -> bool:
        return self.obligation == REQUIRED

    @property
    def allowed_codes(self) -> list[str]:
        return [code for code, _ in self.allowed_values]


DOSTEP = (
    ("publiczny", "Dostępny dla każdego bez ograniczeń (w godzinach dostępności)"),
    ("ograniczony", "Dostępny dla klientów/pracowników obiektu lub po zgłoszeniu obsłudze"),
    ("prywatny", "Niedostępny publicznie"),
    ("nieznany", "Brak informacji"),
)

ZABEZPIECZENIE = (
    ("brak", "Urządzenie dostępne bez szafki"),
    ("szafka_otwarta", "W szafce bez zamka"),
    ("szafka_z_alarmem", "W szafce bez zamka, otwarcie uruchamia alarm"),
    ("szafka_na_kod", "W szafce zamykanej na kod (kod podaje np. dyspozytor 112)"),
    ("zamkniety_na_klucz", "Zamknięty na klucz - wymaga obsługi obiektu"),
    ("nieznany", "Brak informacji"),
)

STATUS = (
    ("sprawny", "Urządzenie sprawne i gotowe do użycia"),
    ("niesprawny", "Urządzenie niesprawne"),
    ("w_serwisie", "Czasowo wycofane (serwis, przegląd)"),
    ("do_weryfikacji", "Po użyciu lub zgłoszeniu - wymaga sprawdzenia przez opiekuna"),
    ("skradziony", "Urządzenie skradzione / brak urządzenia w lokalizacji"),
    ("wycofany", "Trwale wycofane z użytku"),
    ("nieznany", "Brak informacji"),
)

CECHA_ULICY = (
    ("ul.", "ulica"),
    ("al.", "aleja"),
    ("pl.", "plac"),
    ("os.", "osiedle"),
    ("rondo", "rondo"),
    ("skwer", "skwer"),
    ("rynek", "rynek"),
    ("bulw.", "bulwar"),
    ("wyb.", "wybrzeże"),
    ("droga", "droga"),
    ("park", "park"),
    ("inne", "inna cecha"),
)

WOJEWODZTWA = tuple(
    (name, name)
    for name in (
        "dolnośląskie",
        "kujawsko-pomorskie",
        "lubelskie",
        "lubuskie",
        "łódzkie",
        "małopolskie",
        "mazowieckie",
        "opolskie",
        "podkarpackie",
        "podlaskie",
        "pomorskie",
        "śląskie",
        "świętokrzyskie",
        "warmińsko-mazurskie",
        "wielkopolskie",
        "zachodniopomorskie",
    )
)


FIELDS: tuple[FieldSpec, ...] = (
    # --- Identyfikacja -------------------------------------------------------------------
    FieldSpec(
        "id_aed", "identyfikacja", STRING, REQUIRED,
        "Identyfikator AED",
        "Unikalny i niezmienny identyfikator urządzenia w zbiorze dysponenta danych "
        "(nie zmienia się przy aktualizacji zbioru).",
        "Unique, stable identifier of the device within the publisher's dataset.",
        example="LEGIONOWO-AED-001", max_length=64, pattern=r"^[A-Za-z0-9._\-]+$",
        osm_tag="ref",
    ),
    FieldSpec(
        "nazwa", "identyfikacja", STRING, REQUIRED,
        "Nazwa miejsca",
        "Nazwa obiektu lub miejsca, w którym znajduje się AED.",
        "Name of the place/building where the AED is located.",
        example="Urząd Miasta Legionowo", max_length=255, osm_tag="name",
    ),
    # --- Lokalizacja ---------------------------------------------------------------------
    FieldSpec(
        "szerokosc_geograficzna", "lokalizacja", NUMBER, REQUIRED,
        "Szerokość geograficzna",
        "Szerokość geograficzna AED w układzie WGS84 (EPSG:4326), stopnie dziesiętne, "
        "min. 5 miejsc po przecinku. Dla Polski ok. 49,0-54,9.",
        "Latitude, WGS84 decimal degrees (approx. 49.0-54.9 for Poland).",
        example=52.395198, minimum=PL_LAT_MIN, maximum=PL_LAT_MAX, osm_tag="lat",
    ),
    FieldSpec(
        "dlugosc_geograficzna", "lokalizacja", NUMBER, REQUIRED,
        "Długość geograficzna",
        "Długość geograficzna AED w układzie WGS84 (EPSG:4326), stopnie dziesiętne, "
        "min. 5 miejsc po przecinku. Dla Polski ok. 14,1-24,2.",
        "Longitude, WGS84 decimal degrees (approx. 14.1-24.2 for Poland).",
        example=20.931382, minimum=PL_LON_MIN, maximum=PL_LON_MAX, osm_tag="lon",
    ),
    FieldSpec(
        "opis_lokalizacji", "lokalizacja", STRING, RECOMMENDED,
        "Opis lokalizacji w obiekcie",
        "Gdzie dokładnie w obiekcie znajduje się AED - tak, by znalazła go osoba "
        "pierwszy raz w budynku.",
        "Exact placement inside the building/site, understandable for a first-time visitor.",
        example="Parter, hol główny, na ścianie obok portierni", max_length=500,
        osm_tag="defibrillator:location",
    ),
    FieldSpec(
        "w_budynku", "lokalizacja", BOOLEAN, RECOMMENDED,
        "Wewnątrz budynku",
        "Czy AED znajduje się wewnątrz budynku (true) czy na zewnątrz (false).",
        "Whether the AED is inside a building (true) or outdoors (false).",
        example=True, osm_tag="indoor",
    ),
    FieldSpec(
        "pietro", "lokalizacja", INTEGER, OPTIONAL,
        "Kondygnacja",
        "Numer kondygnacji: 0 = parter, liczby ujemne = piętra podziemne.",
        "Floor level: 0 = ground floor, negative = underground.",
        example=0, minimum=-10, maximum=200, osm_tag="level",
    ),
    FieldSpec(
        "wojewodztwo", "lokalizacja", STRING, OPTIONAL,
        "Województwo",
        "Nazwa województwa (małymi literami, jak w TERYT).",
        "Voivodeship name (lower case, as in TERYT).",
        example="mazowieckie", allowed_values=WOJEWODZTWA,
    ),
    FieldSpec(
        "powiat", "lokalizacja", STRING, OPTIONAL,
        "Powiat", "Nazwa powiatu.", "County (powiat) name.",
        example="legionowski", max_length=100,
    ),
    FieldSpec(
        "gmina", "lokalizacja", STRING, OPTIONAL,
        "Gmina", "Nazwa gminy.", "Municipality (gmina) name.",
        example="Legionowo", max_length=100,
    ),
    FieldSpec(
        "miejscowosc", "lokalizacja", STRING, REQUIRED,
        "Miejscowość", "Nazwa miejscowości.", "Locality (city/village) name.",
        example="Legionowo", max_length=100, osm_tag="addr:city",
    ),
    FieldSpec(
        "kod_terc", "lokalizacja", STRING, OPTIONAL,
        "Kod TERC gminy",
        "7-cyfrowy identyfikator gminy z rejestru TERYT (TERC), np. 1408011.",
        "7-digit TERYT TERC municipality code.",
        example="1408011", pattern=r"^\d{7}$",
    ),
    FieldSpec(
        "kod_simc", "lokalizacja", STRING, OPTIONAL,
        "Kod SIMC miejscowości",
        "7-cyfrowy identyfikator miejscowości z rejestru TERYT (SIMC).",
        "7-digit TERYT SIMC locality code.",
        example="0920806", pattern=r"^\d{7}$",
    ),
    FieldSpec(
        "cecha_ulicy", "lokalizacja", STRING, RECOMMENDED,
        "Cecha ulicy",
        "Rodzaj ulicy zgodnie z TERYT (ul., al., pl., ...).",
        "Street type as in TERYT ULIC (ul., al., pl., ...).",
        example="ul.", allowed_values=CECHA_ULICY,
    ),
    FieldSpec(
        "nazwa_ulicy", "lokalizacja", STRING, RECOMMENDED,
        "Nazwa ulicy", "Nazwa ulicy bez cechy.", "Street name without the street type.",
        example="Piłsudskiego", max_length=150, osm_tag="addr:street",
    ),
    FieldSpec(
        "nr_budynku", "lokalizacja", STRING, RECOMMENDED,
        "Numer budynku", "Numer porządkowy budynku.", "Building number.",
        example="41", max_length=20, osm_tag="addr:housenumber",
    ),
    FieldSpec(
        "nr_lokalu", "lokalizacja", STRING, OPTIONAL,
        "Numer lokalu", "Numer lokalu (jeśli dotyczy).", "Unit/apartment number.",
        example="", max_length=20,
    ),
    FieldSpec(
        "kod_pocztowy", "lokalizacja", STRING, RECOMMENDED,
        "Kod pocztowy", "Kod pocztowy w formacie NN-NNN.", "Postal code NN-NNN.",
        example="05-120", pattern=r"^\d{2}-\d{3}$", osm_tag="addr:postcode",
    ),
    # --- Dostępność ----------------------------------------------------------------------
    FieldSpec(
        "dostep", "dostepnosc", STRING, REQUIRED,
        "Rodzaj dostępu",
        "Kto może skorzystać z AED. Gdy brak informacji: nieznany.",
        "Who can use the AED; 'nieznany' when unknown.",
        example="publiczny", allowed_values=DOSTEP, osm_tag="access",
    ),
    FieldSpec(
        "godziny_dostepnosci", "dostepnosc", STRING, RECOMMENDED,
        "Godziny dostępności",
        "Kiedy AED jest dostępny, w składni opening_hours (OpenStreetMap), "
        "np. 24/7 lub Mo-Fr 07:30-15:30.",
        "Availability hours in OpenStreetMap opening_hours syntax, e.g. 24/7.",
        example="Mo-Fr 07:30-17:00", max_length=255, osm_tag="opening_hours",
    ),
    FieldSpec(
        "zabezpieczenie", "dostepnosc", STRING, RECOMMENDED,
        "Zabezpieczenie urządzenia",
        "Czy AED jest w szafce i czy jest zamknięty - kluczowe, by nie tracić "
        "czasu na urządzenie zamknięte na klucz.",
        "Whether the AED is in a cabinet and whether it is locked.",
        example="szafka_z_alarmem", allowed_values=ZABEZPIECZENIE,
    ),
    FieldSpec(
        "instrukcja_dojscia", "dostepnosc", STRING, OPTIONAL,
        "Instrukcja dostępu",
        "Dodatkowe informacje, jak uzyskać dostęp (np. klucz u ochrony, zadzwoń "
        "domofonem).",
        "Extra access instructions (e.g. key at the security desk).",
        example="Poza godzinami pracy klucz u ochrony, wejście od ul. Piłsudskiego",
        max_length=500, osm_tag="description",
    ),
    # --- Urządzenie ----------------------------------------------------------------------
    FieldSpec(
        "status", "urzadzenie", STRING, RECOMMENDED,
        "Status urządzenia",
        "Aktualny stan urządzenia.", "Current device status.",
        example="sprawny", allowed_values=STATUS,
    ),
    FieldSpec(
        "data_ostatniego_uzycia", "urzadzenie", DATE, OPTIONAL,
        "Data ostatniego użycia",
        "Data ostatniego użycia lub zadysponowania urządzenia (YYYY-MM-DD); po użyciu "
        "status powinien mieć wartość do_weryfikacji do czasu sprawdzenia.",
        "Date the device was last used/deployed.",
        example="",
    ),
    FieldSpec(
        "producent", "urzadzenie", STRING, OPTIONAL,
        "Producent", "Producent urządzenia.", "Device manufacturer.",
        example="Philips", max_length=100, osm_tag="manufacturer",
    ),
    FieldSpec(
        "model", "urzadzenie", STRING, OPTIONAL,
        "Model", "Model urządzenia.", "Device model.",
        example="HeartStart FRx", max_length=100, osm_tag="model",
    ),
    FieldSpec(
        "numer_seryjny", "urzadzenie", STRING, OPTIONAL,
        "Numer seryjny", "Numer seryjny urządzenia nadany przez producenta.",
        "Manufacturer serial number.",
        example="B21K-00123", max_length=100,
    ),
    FieldSpec(
        "data_instalacji", "urzadzenie", DATE, OPTIONAL,
        "Data instalacji", "Data instalacji urządzenia w tej lokalizacji (YYYY-MM-DD).",
        "Installation date at this location.",
        example="2021-09-01",
    ),
    FieldSpec(
        "elektrody_pediatryczne", "urzadzenie", BOOLEAN, OPTIONAL,
        "Elektrody pediatryczne",
        "Czy przy urządzeniu są elektrody/klucz pediatryczny (dla dzieci).",
        "Whether paediatric pads/key are available.",
        example=True,
    ),
    FieldSpec(
        "data_ostatniego_przegladu", "urzadzenie", DATE, RECOMMENDED,
        "Data ostatniego przeglądu",
        "Data ostatniego przeglądu technicznego (YYYY-MM-DD).",
        "Date of the last technical inspection.",
        example="2026-05-12",
    ),
    FieldSpec(
        "data_nastepnego_przegladu", "urzadzenie", DATE, RECOMMENDED,
        "Data następnego przeglądu",
        "Planowana data kolejnego przeglądu technicznego (YYYY-MM-DD).",
        "Next inspection due date.",
        example="2027-05-12",
    ),
    FieldSpec(
        "data_waznosci_elektrod", "urzadzenie", DATE, OPTIONAL,
        "Data ważności elektrod", "Data ważności elektrod (YYYY-MM-DD).",
        "Pads expiry date.",
        example="2028-03-31",
    ),
    FieldSpec(
        "data_waznosci_elektrod_pediatrycznych", "urzadzenie", DATE, OPTIONAL,
        "Data ważności elektrod pediatrycznych",
        "Data ważności elektrod pediatrycznych (YYYY-MM-DD), jeśli są na wyposażeniu.",
        "Paediatric pads expiry date.",
        example="2028-06-30",
    ),
    FieldSpec(
        "data_waznosci_baterii", "urzadzenie", DATE, OPTIONAL,
        "Data ważności baterii", "Data ważności baterii (YYYY-MM-DD).",
        "Battery expiry date.",
        example="2029-01-31",
    ),
    # --- Dysponent i kontakt -------------------------------------------------------------
    FieldSpec(
        "dysponent", "dysponent", STRING, RECOMMENDED,
        "Dysponent urządzenia",
        "Instytucja lub firma odpowiedzialna za urządzenie (właściciel/zarządca).",
        "Organisation responsible for the device (owner/operator).",
        example="Urząd Miasta Legionowo", max_length=255, osm_tag="operator",
    ),
    FieldSpec(
        "telefon_kontaktowy", "dysponent", STRING, OPTIONAL,
        "Telefon kontaktowy",
        "Telefon do dysponenta/obsługi obiektu w formacie międzynarodowym.",
        "Contact phone in international format.",
        example="+48 22 766 40 00", max_length=30, pattern=r"^\+?[0-9 ()\-]{7,30}$",
        osm_tag="phone",
    ),
    FieldSpec(
        "email_kontaktowy", "dysponent", STRING, OPTIONAL,
        "E-mail kontaktowy", "Adres e-mail do dysponenta.", "Contact e-mail.",
        example="aed@example.gov.pl", max_length=254,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", osm_tag="email",
    ),
    # --- Metadane rekordu ----------------------------------------------------------------
    FieldSpec(
        "data_aktualizacji", "metadane", DATE, REQUIRED,
        "Data aktualizacji",
        "Data ostatniej aktualizacji lub weryfikacji danych tego rekordu (YYYY-MM-DD).",
        "Date of the last update/verification of this record.",
        example="2026-11-21",
    ),
    FieldSpec(
        "zweryfikowany", "metadane", BOOLEAN, OPTIONAL,
        "Zweryfikowany na miejscu",
        "Czy obecność i dostępność AED potwierdzono na miejscu.",
        "Whether presence/availability was confirmed on site.",
        example=True,
    ),
    FieldSpec(
        "zrodlo", "metadane", STRING, REQUIRED,
        "Źródło danych",
        "Nazwa dysponenta danych / źródła, z którego pochodzi rekord.",
        "Name of the data publisher/source of the record.",
        example="Gmina Miejska Legionowo", max_length=255,
    ),
    FieldSpec(
        "zrodlo_url", "metadane", STRING, OPTIONAL,
        "Adres źródła",
        "Adres URL zbioru lub zasobu źródłowego (np. w dane.gov.pl).",
        "URL of the source dataset/resource.",
        example="https://dane.gov.pl/pl/dataset/40593", max_length=500,
        pattern=r"^https?://",
    ),
    FieldSpec(
        "uwagi", "metadane", STRING, OPTIONAL,
        "Uwagi", "Dodatkowe uwagi.", "Additional notes.",
        example="", max_length=1000, osm_tag="note",
    ),
)

FIELD_NAMES: tuple[str, ...] = tuple(f.name for f in FIELDS)
FIELDS_BY_NAME: dict[str, FieldSpec] = {f.name: f for f in FIELDS}
REQUIRED_FIELDS: tuple[str, ...] = tuple(f.name for f in FIELDS if f.required)


def example_rows() -> list[dict[str, object]]:
    """Return illustrative example rows (clearly marked as examples in every artefact)."""
    first = {f.name: f.example for f in FIELDS}
    second = dict(first)
    second.update(
        {
            "id_aed": "LEGIONOWO-AED-002",
            "nazwa": "Arena Legionowo",
            "szerokosc_geograficzna": 52.400177,
            "dlugosc_geograficzna": 20.917295,
            "opis_lokalizacji": "Wejście główne, na zewnątrz budynku, przy kasach",
            "w_budynku": False,
            "pietro": 0,
            "nazwa_ulicy": "Chrobrego",
            "nr_budynku": "50B",
            "godziny_dostepnosci": "24/7",
            "zabezpieczenie": "szafka_z_alarmem",
            "instrukcja_dojscia": "",
            "producent": "",
            "model": "",
            "elektrody_pediatryczne": False,
            "numer_seryjny": "",
            "data_instalacji": "",
            "data_nastepnego_przegladu": "",
            "data_waznosci_elektrod": "",
            "data_waznosci_elektrod_pediatrycznych": "",
            "data_waznosci_baterii": "",
            "dysponent": "Arena Legionowo",
            "telefon_kontaktowy": "",
            "email_kontaktowy": "",
            "zweryfikowany": False,
        }
    )
    return [first, second]
