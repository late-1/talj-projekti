# Arkkitehtuurikuvaus

Tämä dokumentti kuvaa, miten sovellus toimii, miten se on toteutettu ja miksi.
Käynnistys- ja testausohjeet ovat repositorion juuren `README.md`:ssä.

## 1. Yleiskuva

Kyseessä on Flask-sovellus, jolla käyttäjä tallentaa lähdeviitteitä lomakkeella,
selaa ja hakee omia viitteitään ja saa ne BibTeX-muodossa LaTeX-dokumenttia varten.
Jokaisella käyttäjällä on oma tunnus, ja käyttäjä näkee vain omat viitteensä.

## 2. Tekniikka

| Osa | Valinta | Peruste |
| --- | --- | --- |
| Web-kehys | Flask 3 | Kurssin speksi, boilerplate |
| Tietokanta | SQLite | Kurssin speksi, ei vaadi palvelinta |
| Tietokantakerros | Flask-SQLAlchemy, SQL käsin `text()`-kyselyinä | Boilerplaten tapa, ei ORM-malleja |
| Riippuvuudet | uv (`pyproject.toml`, `uv.lock`) | Boilerplate; uv asentaa myös oikean Python-version |
| Yksikkötestit | pytest + Flaskin testiasiakas | Boilerplate |
| Selaintestit | Robot Framework + Browser-kirjasto (Playwright) | Boilerplate, kurssin käytäntö |
| Koodin tyyli | pylint | Asetukset `pyproject.toml`:ssä |
| CI | GitHub Actions | Testit ja pylint ajetaan jokaisella pushilla |
| Julkaisu | Docker-kuva (GitHub Container Registry) ja OKD-klusteri (Kustomize) | Kurssin käytäntö, boilerplate |
| Salasanat | `werkzeug.security` (hajautus) | Tulee Flaskin mukana |

Python-versio: vähintään 3.12 (`pyproject.toml`).

## 3. Hakemistorakenne

```
run.sh                       sovelluksen käynnistys yhdellä komennolla
test.sh                      testien ajo yhdellä komennolla
pyproject.toml, uv.lock      riippuvuudet ja pylintin asetukset
.githooks/pre-commit         ennen committia ajettavat tarkistukset
.github/workflows/ci.yaml    GitHub Actions: testit ja pylint
.github/workflows/docker.yaml  GitHub Actions: Docker-kuvan julkaisu
.github/workflows/release.yaml  GitHub Actions: versiojulkaisu tagista
CHANGELOG.md                 muutosloki versioittain (julkaisujen kuvaukset)
Dockerfile, .dockerignore    sovelluksen Docker-kuva
kustomization.yaml           OKD-julkaisun asetukset (projekti, kuva, osoite)
manifests/                   OKD-resurssit (ks. luku 11)
src/
  index.py                   käynnistää palvelimen
  app.py                     reitit ja istunnon käsittely
  config.py                  Flask-sovellus, asetukset, tietokantayhteys
  db_helper.py               taulujen luonti, tyhjennys ja nollaus
  schema.sql                 tietokannan taulut
  util.py                    syötteiden validointi, viiteavaimen muodostus,
                             hakusanojen pilkkominen, hakuehtojen siivous
                             ja tarkistus, valittujen viitteiden tunnisteet,
                             UserInputError
  reference_types.py         viitetyypit ja niiden kentät (yksi totuuden lähde)
  bibtex.py                  viitteen muotoilu BibTeX-muotoon
  citation.py                viitteen muotoilu lähdeluettelon muotoon
  entities/
    user.py                  User-luokka
    reference.py             Reference-luokka
  repositories/
    user_repository.py       käyttäjiin liittyvät tietokantakyselyt
    reference_repository.py  viitteisiin liittyvät tietokantakyselyt
  templates/                 Jinja-sivupohjat
    layout.html              yhteinen runko, yläpalkki, ilmoitukset
    login.html, register.html
    add_reference.html       viitteen lisäyslomake
    reference_fields.html    viitteen kentät (lisäys- ja muokkauslomakkeen yhteinen osa)
    references.html          viitelistaus, haku, valittujen viitteiden poisto ja .bib-tiedosto
    show_reference.html      bibtex-sivu (painikkeet, BibTeX, lähdeviite, kentät)
                             ja muokkauslomake
    duplicate_dialog.html    vahvistusikkuna saman viitteen lisäämiselle tai tallentamiselle
  static/main.css            tyylit
  static/reference_form.js   lomakkeen kenttien vaihto viitetyypin mukaan
  static/copy.js             copy-painike (leikepöytä)
  static/dialog.js           saman viitteen vahvistusikkunan avaus
  static/select.js           listan valintaruudut: select all / unselect,
                             create .bib- ja delete-painikkeen tila, varmistus
  tests/                     pytest-testit
  story_tests/               Robot Framework -testit
  instance/                  SQLite-tiedostot (ei versionhallinnassa)
```

Kerrokset: `app.py` (HTTP, istunto, sivupohjat) → `util.py` (validointi) ja
`repositories/` (SQL) → `config.db`. Reitit eivät sisällä SQL:ää, eivätkä
repositoriot tiedä HTTP:stä mitään. Virheellinen käyttäjän syöte ilmaistaan
poikkeuksella `UserInputError`, jonka viesti näytetään käyttäjälle.

## 4. Asetukset

Asetukset luetaan ympäristömuuttujista; `config.py` lataa lisäksi projektin juuren
`.env`-tiedoston (ympäristömuuttuja voittaa `.env`:n arvon).

| Muuttuja | Merkitys | Oletus |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy-osoite, esim. `sqlite:///database.db` | pakollinen |
| `SECRET_KEY` | Flaskin istuntojen allekirjoitusavain | pakollinen |
| `TEST_ENV` | `true` = testitila: `/reset_db`-reitti käytössä | ei asetettu |
| `DEBUG` | `true` = Flaskin debug-tila päällä | ei asetettu (debug pois) |
| `HOST` | kuunneltava osoite | `127.0.0.1` |
| `PORT` | portti | `5001` |

* `run.sh` luo `.env`-tiedoston satunnaisella `SECRET_KEY`:llä, jos sitä ei ole.
* Suhteellinen SQLite-polku sijoittuu hakemistoon `src/instance/` (Flask-SQLAlchemyn
  käytäntö), eli kehitystietokanta on `src/instance/database.db`.
* Palvelin kuuntelee oletuksena vain omaa konetta. Boilerplatessa osoite on
  `0.0.0.0`, mutta Flaskin debuggeria ei pidä avata lähiverkkoon. Klusterilla
  kontti kuuntelee kaikkia osoitteita (`HOST=0.0.0.0` tiedostossa
  `manifests/configmap.yaml`), jotta OKD:n Service tavoittaa sen.
* Flaskin debug-tila on päällä vain, kun `DEBUG=true` (`src/index.py`).
  `run.sh` asettaa sen, joten paikallisessa kehityksessä debuggeri on käytössä.
  Klusterilla ja testeissä muuttujaa ei aseteta, joten virhetilanteessa
  käyttäjälle ei näytetä tracebackia eikä lähdekoodia.
* Klusterilla asetukset tulevat ympäristömuuttujina: `DATABASE_URL`,
  `TEST_ENV` ja `HOST` tiedostosta `manifests/configmap.yaml` ja `SECRET_KEY`
  tiedostosta `secret.env`, joka ei ole versionhallinnassa (ks. luku 11).

## 5. Tietokanta

`src/schema.sql` (lyhennettynä):

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL
);

CREATE TABLE bib_references (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users,
  entry_type TEXT NOT NULL,          -- article | book | inproceedings
  cite_key TEXT NOT NULL,
  author TEXT NOT NULL, title TEXT NOT NULL, year TEXT NOT NULL,
  journal TEXT, booktitle TEXT, publisher TEXT, volume TEXT, number TEXT,
  pages TEXT, address TEXT, edition TEXT, isbn TEXT, doi TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, cite_key)
);
```

* Taulun nimi on `bib_references`, koska `references` on SQL:n varattu sana.
* Jokaisella BibTeX-kentällä on oma sarakkeensa (ei erillistä avain–arvo-taulua).
  Kenttiä on vähän, ja näin kenttäkohtainen haku on suoraviivainen.
  Kentät, jotka eivät kuulu viitteen tyyppiin tai ovat tyhjiä, ovat `NULL`.
* Kaikki kentät ovat tekstiä, myös `year`, `volume` ja `number`, koska BibTeX
  käsittelee niitä tekstinä (esim. `number = {3-4}`).
* `UNIQUE (user_id, cite_key)` takaa, että avain on uniikki käyttäjäkohtaisesti.
* SQLite tarkistaa viiteavaimet (foreign key) vain pyydettäessä, joten
  `config.py` asettaa jokaiselle yhteydelle `PRAGMA foreign_keys = ON`.
* Lauseet ovat muotoa `CREATE ... IF NOT EXISTS`, jotta skeeman voi ajaa
  olemassa olevaan tietokantaan.

`db_helper.py`:

| Funktio / komento | Toiminta |
| --- | --- |
| `setup_db()` / `uv run python src/db_helper.py` | Pudottaa taulut ja luo ne uudelleen (tyhjä tietokanta). |
| `setup_db_if_missing()` / `... db_helper.py --if-missing` | Luo puuttuvat taulut ja säilyttää olemassa olevan datan. `run.sh` käyttää tätä, joten data säilyy käynnistysten välillä ja uudet taulut ilmestyvät vanhaan tietokantaan itsestään. |
| `reset_db()` | Poistaa rivit kaikista tauluista. Robot-testit kutsuvat tätä reitin `/reset_db` kautta. |

Taulut pudotetaan ja tyhjennetään käänteisessä luontijärjestyksessä, jotta
viiteavaimet eivät estä sitä.

Varsinaisia migraatioita ei ole: uusi taulu syntyy automaattisesti, mutta jos
olemassa olevan taulun sarakkeet muuttuvat, tietokanta on luotava uudelleen
komennolla `uv run python src/db_helper.py` (data häviää).

Klusterilla `run.sh`:ää ei ajeta, joten tauluja ei luoda käynnistyksessä:
tietokanta alustetaan käsin, ks. luku 11.

## 6. Reitit

| Reitti | Metodi | Kirjautuminen | Toiminta |
| --- | --- | --- | --- |
| `/` | GET | – | Ohjaa: kirjautunut → `/references`, muuten → `/login` |
| `/login` | GET | ei | Kirjautumislomake (kirjautunut ohjataan `/`) |
| `/login` | POST | ei | Tarkistaa tunnukset, aloittaa istunnon, ohjaa `/` |
| `/register` | GET | ei | Rekisteröintilomake (kirjautunut ohjataan `/`) |
| `/register` | POST | ei | Luo käyttäjän, kirjaa sisään, ohjaa `/` |
| `/logout` | GET | – | Tyhjentää istunnon, ohjaa `/login` |
| `/add` | GET | vaaditaan | Viitteen lisäyslomake; `?type=book` valitsee tyypin valmiiksi |
| `/add` | POST | vaaditaan + CSRF | Validoi ja tallentaa viitteen, ohjaa `/add?type=<tyyppi>` |
| `/references` | GET | vaaditaan | Omien viitteiden listaus, uusin ensin. Hakuparametrit: `query`, `author`, `title`, `venue`, `key`, `year_from`, `year_to`, `type`. Tyhjät ja tuntemattomat parametrit pudotetaan osoitteesta uudelleenohjauksella |
| `/references/<id>` | GET | vaaditaan | Bibtex-sivu; `?back=<osoite>` kertoo, mihin back-painike palaa. Toisen käyttäjän tai olematon viite → 404 |
| `/references/<id>/edit` | GET | vaaditaan | Bibtex-sivu, jossa muokkauslomake on auki BibTeXin yläpuolella |
| `/references/<id>/edit` | POST | vaaditaan + CSRF | Validoi ja tallentaa muutokset, ohjaa `/references/<id>` |
| `/references/<id>/delete` | POST | vaaditaan + CSRF | Poistaa viitteen, ohjaa listaukseen (`back`-osoitteeseen) |
| `/references/delete` | POST | vaaditaan + CSRF | Poistaa listalla valitut viitteet (`reference_id`, useita), ohjaa listaukseen (`back`) |
| `/references/bib` | POST | vaaditaan + CSRF | Palauttaa listalla valitut viitteet ladattavana tiedostona `references.bib`; jos mitään ei valittu, ohjaa listaukseen (`back`) |
| `/reset_db` | GET | – | Vain testitilassa: tyhjentää tietokannan ja istunnon |

Epäonnistunut kirjautuminen tai rekisteröinti näyttää saman lomakkeen uudelleen
virheilmoituksen kanssa, ja käyttäjätunnus säilyy kentässä.

## 7. Käyttäjät ja istunto

* **Käyttäjätunnus:** 3–30 merkkiä, sallitut merkit kirjaimet a–z, numerot ja
  `_ - .`; uniikki (tietokannan `UNIQUE`-rajoite, isot ja pienet kirjaimet
  erotellaan). Alun ja lopun välilyönnit poistetaan.
* **Salasana:** 8–100 merkkiä, syötetään rekisteröityessä kahdesti. Tallennetaan
  vain hajautettuna.
* Rajat ovat vakioina `util.py`:ssä, ja lomakkeiden `minlength`/`maxlength` sekä
  ohjetekstit luetaan samoista vakioista. Validointi tehdään aina palvelimella;
  selaimen tarkistukset ovat vain mukavuutta.
* **Istunto:** Flaskin allekirjoitettu eväste, jossa `user_id`, `username` ja
  `csrf_token`. Istunto tyhjennetään ennen uuden aloittamista ja uloskirjautuessa.
* **Pääsynhallinta:** `@login_required` ohjaa kirjautumattoman kirjautumissivulle
  (ei 403-virhettä), koska kirjautumattoman on tarkoitus nähdä vain kirjautumissivu.
* `@login_required` tarkistaa myös, että istunnon käyttäjä on yhä tietokannassa;
  jos ei ole (esim. tietokanta on luotu uudelleen), istunto tyhjennetään.
* **CSRF:** jokainen istunto saa satunnaisen tunnisteen, joka on piilokenttänä
  kirjautuneen käyttäjän POST-lomakkeissa (lisäys, muokkaus, poisto,
  valittujen viitteiden poisto ja .bib-tiedosto) ja tarkistetaan funktiolla
  `check_csrf()` (virheellinen tai puuttuva → 403). Kirjautumis- ja
  rekisteröintilomakkeissa tunnistetta ei ole (istuntoa ei vielä ole).
* **Uloskirjautuminen** on tavallinen linkki (`GET /logout`). Haittana on, että
  ulkopuolinen sivu voi kirjata käyttäjän ulos linkillä; tämä on hyväksytty
  yksinkertaisuuden vuoksi.
* Kirjautumisvirheen ilmoitus on sama väärälle tunnukselle ja väärälle salasanalle,
  jotta tunnusten olemassaoloa ei voi päätellä.

## 8. Viitteet

### Tyypit ja kentät

Määritelty tiedostossa `src/reference_types.py`, josta lomake, validointi ja
tietokantakyselyt lukevat ne. Uuden tyypin tai kentän lisääminen: lisää se
sinne (ja uusi kenttä sarakkeeksi `schema.sql`:ään).

| Tyyppi | Pakolliset | Valinnaiset |
| --- | --- | --- |
| `article` | author, title, journal, year | volume, number, pages, doi |
| `book` | author, title, publisher, year | address, edition, isbn |
| `inproceedings` | author, title, booktitle, year | pages, publisher, doi |

### Validointi (`util.validate_reference`, `util.validate_cite_key`)

* Tyypin on oltava jokin tuetuista.
* Pakolliset kentät eivät saa olla tyhjiä.
* Arvoista poistetaan ylimääräiset välilyönnit ja rivinvaihdot.
* `year` on nelinumeroinen luku.
* Enimmäispituus: author, title, journal ja booktitle 1000 merkkiä, muut 200.
* Kentät, jotka eivät kuulu valittuun tyyppiin, jätetään tallentamatta, vaikka
  ne lähetettäisiin lomakkeessa.
* Kirjoittajat syötetään BibTeX-muodossa: useampi kirjoittaja erotetaan sanalla
  `and`, nimi joko `Sukunimi, Etunimi` tai `Etunimi Sukunimi`. Muotoa ei
  pakoteta; lomakkeessa on ohjeteksti.
* Aaltosulkeiden `{ }` on täsmättävä (ks. BibTeX-muotoilu).
* Itse annettu avain: enintään 50 merkkiä, sallitut merkit a–z, A–Z, 0–9 ja
  `_ - : . + /` (ei välilyöntejä, pilkkuja tai aaltosulkeita, jotka rikkoisivat
  BibTeXin).

### Viiteavaimen generointi

Kun key-kenttä jätetään tyhjäksi:

1. Otetaan ensimmäinen kirjoittaja (teksti ennen ensimmäistä `and`-sanaa).
2. Sukunimi on pilkkua edeltävä osa (`Martin, Robert`) tai pilkuttomassa
   muodossa viimeinen sana (`Robert Martin`).
3. Sukunimi muutetaan pieniksi kirjaimiksi, aksentit poistetaan (`Mäkelä` →
   `makela`) ja muut kuin a–z ja 0–9 pudotetaan (`van der Berg` → `vanderberg`).
   Jos mitään ei jää jäljelle, käytetään sanaa `ref`.
4. Perään lisätään vuosi: `martin2008`.
5. Jos avain on käyttäjällä jo käytössä, kokeillaan `martin2008a`, `…b`, …, `…z`,
   `…aa`, … kunnes löytyy vapaa.

Itse annettu, jo käytössä oleva avain hylätään virheilmoituksella (ei muuteta
automaattisesti). Samanaikaisten lisäysten varalta uniikkius varmistetaan
viime kädessä tietokannan rajoitteella.

### Lisäyslomake

* Tyyppi valitaan lomakkeen yläreunasta (radiopainikkeet, jotka näyttävät
  tekstilinkeiltä; valittu on alleviivattu kuten yläpalkissa).
* Kaikki kentät ovat sivulla; `reference_form.js` näyttää valitun tyypin kentät,
  piilottaa muut ja merkitsee ne `disabled`-tilaan (jolloin selain ei lähetä
  eikä vaadi niitä) sekä päivittää `required`-määreet ja "(optional)"-merkinnät.
  Palvelin renderöi saman alkutilan, joten sivu on oikein jo ennen skriptin
  ajoa, ja tyyppiä vaihdettaessa muihin kenttiin kirjoitettu teksti säilyy.
* Onnistuneen lisäyksen jälkeen näytetään ilmoitus `Reference added with the key
  <avain>` ja tyhjä lomake samalla tyypillä (helpottaa usean viitteen lisäämistä).
* Virhetilanteessa lomake näytetään uudelleen virheilmoituksen ja syötettyjen
  arvojen kanssa.
* Jos käyttäjällä on jo samanlainen viite, se kysytään ennen tallennusta (ks.
  Saman viitteen tunnistus).

### Saman viitteen tunnistus

* Viite on sama, jos sen tyyppi ja kaikki kentät ovat täsmälleen samat kuin
  jollakin käyttäjän omalla viitteellä. Avainta ei verrata, koska kahdella
  viitteellä ei voi olla samaa avainta. Tyhjät kentät (`NULL`) lasketaan
  samoiksi (`reference_repository.find_duplicate`, SQL:n `IS`-vertailu).
* Tarkistus tehdään validoinnin jälkeen sekä lisäyksessä että muokkauksessa;
  muokattavaa viitettä itseään ei lasketa (`exclude_id`).
* Jos sama viite löytyy, mitään ei tallenneta. Lomake näytetään uudelleen
  annetuilla arvoilla, ja sen päälle aukeaa ikkuna (`duplicate_dialog.html`,
  HTML:n `<dialog>`): `The same reference already exists (<avain>). Add it
  anyway?` (muokatessa `Save it anyway?`) ja painikkeet `add`/`save` ja
  `cancel`.
* `add`/`save` lähettää viitelomakkeen uudelleen kentällä
  `confirm_duplicate=yes`, jolloin tarkistus ohitetaan ja viite tallennetaan
  tavalliseen tapaan (uusi avain saa tarvittaessa kirjaimen, esim.
  `martin2008a`). `cancel` ja Esc sulkevat ikkunan, ja lomake jää täytetyksi.
* `dialog.js` avaa ikkunan modaalisena (`showModal`), joten taustalla olevaa
  sivua ei voi käyttää ennen valintaa. Ilman JavaScriptiä ikkuna näkyy silti,
  koska se renderöidään auki.
* Tietokannan rakenne ei muutu, joten klusterilla ei tarvita toimenpiteitä.

### Listaus (`/references`)

* Käyttäjän omat viitteet uusin ensin, kukin ohutreunaisessa laatikossa, joka on
  kokonaan linkki bibtex-sivulle. Yläpuolella viitteiden määrä.
* Laatikossa näytetään vain olennaisin: otsikko, kirjoittajat ja vuosi,
  julkaisupaikka (`Reference.venue`: journal, booktitle tai publisher) sekä
  oikeassa reunassa himmeämmällä tyyppi ja avain. Muut kentät (volume, pages,
  doi, …) näkyvät vain bibtex-sivulla.
* Tyhjässä listassa on linkki lisäyssivulle.

### Haku (perusversio)

* Listauksen yläreunassa on yksi hakukenttä ja `search`-painike. Lomake on
  GET-lomake, joten haku on osoitteessa (`/references?query=martin+2008`): sen voi
  tallentaa kirjanmerkiksi, ja bibtex-sivun `back` palaa samaan hakutulokseen.
* Haku jaetaan välilyönneistä sanoiksi. Viite löytyy, kun **jokainen** sana
  esiintyy jossakin sen kentässä (JA-ehto). Sanat voivat olla eri kentissä ja
  missä tahansa järjestyksessä, ja sanan osa riittää (`appren` löytää sanan
  *Apprenticeship*).
* Haku kohdistuu kaikkeen viitteen sisältöön: tyyppi, avain ja kaikki
  BibTeX-kentät (myös ne, joita listauksessa ei näytetä, kuten doi ja pages).
* Kirjainkoolla ei ole väliä, myöskään ääkkösissä. SQLite vertaa
  kirjainkoosta riippumatta vain kirjaimet a–z, joten `config.py` rekisteröi
  jokaiselle tietokantayhteydelle SQL-funktion `casefold()`, jota haku käyttää.
  Aksentteja ei poisteta: `makela` ei löydä nimeä *Mäkelä*.
* Toteutus (`reference_repository.get_references(user_id, query)`): kentät
  yhdistetään SQL:ssä rivinvaihdoilla yhdeksi tekstiksi, ja jokaiselle sanalle
  on ehto `instr(teksti, :sana) > 0`. Sanat ovat parametreja, eikä `instr`
  tunne jokerimerkkejä, joten `%`, `_` ja lainausmerkit ovat tavallisia
  merkkejä. Rivinvaihto kenttien välissä estää osumat kahden kentän rajan yli.
* Rajat: haku enintään 200 merkkiä ja 20 eri sanaa (`util.search_words`).
* Hakutuloksen yläpuolella lukee esim. `1 of 3 references` ja linkki `show all`,
  joka poistaa haun. Jos mitään ei löydy, näytetään `No references found`.
  Hakulomaketta ei näytetä käyttäjälle, jolla ei ole yhtään viitettä.

### Haku (advanced)

* Hakukentän oikealla puolella ovat allekkain samanlevyiset painikkeet
  `search`, `advanced` ja `delete` (ks. Valittujen viitteiden poisto).
  `advanced` avaa ja sulkee lisäkentät. Se on HTML:n
  `<details>`/`<summary>`-elementti painikkeen näköiseksi tyyliteltynä, joten se
  toimii ilman JavaScriptiä. Auki ollessaan painike on täytetty (musta).
* Lisäkentät eivät ole `<details>`-elementin sisällä vaan sen jälkeen omana
  elementtinään (`#advanced-fields`), jotta ne voivat aueta koko leveydelle
  `advanced`- ja `delete`-painikkeen väliin. CSS näyttää ne, kun `details` on
  auki (`.search-form:has(.advanced[open])`).
* Kentät ja niiden osoiteparametrit:

  | Kenttä | Parametri | Kohdistuu | Ehto |
  | --- | --- | --- | --- |
  | author | `author` | author | jokainen sana löytyy |
  | title | `title` | title | jokainen sana löytyy |
  | published in | `venue` | journal, booktitle ja publisher | jokainen sana löytyy jostakin näistä |
  | key | `key` | viiteavain | jokainen sana löytyy |
  | from year | `year_from` | year | vuosi ≥ arvo |
  | to year | `year_to` | year | vuosi ≤ arvo |
  | type | `type` | viitteen tyyppi | täsmälleen sama (`any` = ei rajausta) |

* Kaikki ehdot yhdistetään JA-ehdoin keskenään ja perushakukentän kanssa.
  Tekstikentissä pätevät samat säännöt kuin perushaussa (sanan osa riittää,
  kirjainkoolla ei väliä), mutta haku kohdistuu vain kyseiseen kenttään:
  perushaku `dijkstra` löytää myös viitteen, jonka osoitteessa sana on,
  `author=dijkstra` vain kirjoittajan.
* Vuodet ovat tietokannassa nelinumeroista tekstiä, joten niitä voi verrata
  suoraan tekstinä. Molemmat päät kuuluvat väliin.
* Advanced-kentät ovat samassa GET-lomakkeessa kuin perushaku, joten koko haku
  on osoitteessa ja `back` palauttaa sen. Selain lähettää myös tyhjät kentät;
  palvelin ohjaa siistittyyn osoitteeseen (`/references?author=martin`), josta
  tyhjät ja tuntemattomat parametrit on pudotettu ja välilyönnit siivottu
  (`util.clean_search_params`).
* Advanced-osio renderöidään auki aina, kun jokin sen parametreista on
  osoitteessa, ja kentät säilyttävät arvonsa.
* Virheellinen vuosi (ei nelinumeroinen) tai tuntematon tyyppi: näytetään
  virheilmoitus ja kyseinen ehto jätetään huomiotta, muut ehdot pätevät
  (`util.search_filters`). Selain estää virheellisen vuoden jo lomakkeessa
  (`pattern`).
* `show all` poistaa sekä perushaun että advanced-ehdot.
* Repositorio: `get_references(user_id, query, filters)`; ehdot rakennetaan
  kiinteistä SQL-lausekkeista (`FILTER_TEXTS`) ja arvot ovat aina parametreja.
* Kumpikaan haku ei muuta tietokannan rakennetta, joten klusterin tietokantaa
  ei tarvitse luoda uudelleen (ks. luku 11).

### Bibtex-sivu (`/references/<id>`)

* Sivu on yksi 46 rem:n levyinen keskitetty palsta, jossa ovat ylhäältä alas
  painikerivi, muokkauslomake (vain muokatessa), BibTeX-laatikko,
  lähdeviitelaatikko ja kenttälaatikko. Painikerivillä `back` on vasemmassa
  reunassa ja `copy`, `edit` ja `delete` oikeassa reunassa. Painikkeet pysyvät
  laatikoiden reunojen sisäpuolella myös kapealla näytöllä (flexbox, rivitys
  tarvittaessa).
* BibTeX on `<pre>`-laatikossa. Sen alla on viite luettavassa muodossa kahdessa
  erillisessä, samannäköisessä laatikossa (yhteinen luokka `reference-box`):
  ensin lähdeluettelotyylinen viite (`#citation`, `citation.to_citation`, ks.
  alla) ja sitten tyyppi, avain ja jokainen täytetty kenttä samassa
  järjestyksessä kuin lomakkeessa (`#details`, `<dl>`). Kenttien nimet ovat
  lomakkeen nimiä ilman sulkeissa olevaa selitystä
  (`reference_types.SHORT_LABELS`), esim. `book title`. Kapealla näytöllä nimi
  on arvon yläpuolella.
* `copy` kopioi tekstin leikepöydälle (`copy.js`): ensisijaisesti
  `navigator.clipboard`, ja jos se ei ole käytettävissä (esim. sivu avattu
  muulla kuin localhost-osoitteella ilman HTTPS:ää), varamenetelmänä
  piilotettu tekstikenttä ja `document.execCommand("copy")`. Painikkeen teksti
  vaihtuu hetkeksi muotoon `copied`.
* `back`: listauksen linkit vievät mukanaan nykyisen osoitteensa
  (`?back=/references?...`), joten paluu säilyttää haun.
  `get_back_url()` hyväksyy vain listaussivun osoitteet, jottei parametrilla voi
  ohjata muualle (open redirect).
* Viite haetaan aina ehdolla `user_id = kirjautunut käyttäjä`. Toisen käyttäjän
  viite antaa saman 404-vastauksen kuin olematon, eikä paljasta viitteen
  olemassaoloa.
* Yläpalkissa `view / search` on alleviivattu myös bibtex-sivulla.

### Muokkaus (`/references/<id>/edit`)

* `edit` avaa saman bibtex-sivun osoitteessa `/references/<id>/edit`: BibTeXin
  yläpuolelle tulee muokkauslomake nykyisillä arvoilla, ja `edit`-painike on
  täytetty mustaksi. Painikerivi pysyy lomakkeen yläpuolella.
* Lomake käyttää samoja kenttiä kuin lisäyslomake (`reference_fields.html`,
  `reference_form.js`) ja samaa validointia. Kentät ovat kahdessa sarakkeessa,
  pitkät kentät (kirjoittaja, otsikko, julkaisu, avain) koko leveydellä.
  Myös tyypin voi vaihtaa; tällöin vanhan tyypin kentät tyhjennetään
  (`update_reference` asettaa jokaisen kenttäsarakkeen, puuttuvat `NULL`iksi).
* Lomakkeen alla `save` ja `cancel`. `save` tallentaa ja ohjaa takaisin
  bibtex-sivulle (lomake poissa, BibTeX päivittynyt). `cancel` on linkki samalle
  sivulle, eli mitään ei tallenneta.
* Avain: jos kenttä tyhjennetään, avain generoidaan uudelleen kirjoittajasta
  ja vuodesta. Viitteen oma nykyinen avain ei tällöin ole "varattu"
  (`get_cite_keys(..., exclude_id)`), joten `martin2008` ei muutu muotoon
  `martin2008a`. Toisen oman viitteen avain hylätään kuten lisäyksessä.
* Virhetilanteessa lomake pysyy auki annetuilla arvoilla, ja BibTeX sekä
  viitteen tiedot näyttävät edelleen tallennetun version.
* Jos muutettu viite on sama kuin jokin toinen käyttäjän viite, tallennus
  kysytään ensin (ks. Saman viitteen tunnistus).
* `back`-parametri kulkee mukana muokkauksen läpi, joten haku säilyy.

### Poisto (`/references/<id>/delete`)

* `delete` on oma POST-lomakkeensa CSRF-tunnisteella. Selain kysyy
  varmistuksen (`confirm`), koska poistoa ei voi perua.
* Poiston jälkeen ohjataan listaukseen (`back`-osoitteeseen) ja näytetään
  ilmoitus `Reference <avain> deleted`.
* Sekä muokkaus että poisto kohdistuvat aina ehdolla `user_id = kirjautunut
  käyttäjä`; toisen käyttäjän viite antaa 404.
* Muokkaus ja poisto eivät muuta tietokannan rakennetta, joten klusterin
  tietokantaa ei tarvitse luoda uudelleen (ks. luku 11).

### Valittujen viitteiden poisto (`/references/delete`)

* Jokaisen viitelaatikon oikeassa alakulmassa on valintaruutu. Ruudun viiva on
  sama kuin laatikon, ja se on noin välilyönnin levyisen marginaalin päässä
  laatikon reunasta. Valittuna ruudussa on kulmasta kulmaan ulottuva rasti,
  joka piirretään samalla viivalla (CSS-gradientit, `appearance: none`).
* Viitelaatikko on kokonaan linkki, eikä linkin sisällä saa olla lomakekenttiä.
  Siksi valintaruutu on linkin vieressä yhteisessä `.reference-item`-elementissä
  ja asemoitu laatikon päälle. Ruudun klikkaus vain valitsee viitteen.
* Hakupainikkeiden alla on `delete`, joka poistaa kaikki valitut viitteet. Se
  on oma POST-lomakkeensa (`#delete-selected-form`, CSRF-tunniste ja nykyinen
  listan osoite `back`). Valintaruudut ja painike ovat lomakkeen ulkopuolella
  ja liitetään siihen HTML:n `form`-attribuutilla.
* `select.js` pitää painikkeen harmaana ja poissa käytöstä, kun yhtään viitettä
  ei ole valittu, ja kysyy varmistuksen (`Delete 2 references?`). Ilman
  JavaScriptiä painike pysyy poissa käytöstä.
* `delete`-painikkeen vasemmalla puolella on `select all`, joka valitsee kaikki
  listalla näkyvät viitteet (haun tulokset). Kun kaikki on valittu, painikkeen
  teksti on `unselect`, ja se poistaa kaikki valinnat. Painike toimii
  `select.js`:llä eikä lähetä lomaketta (`type="button"`). Se on poissa
  käytöstä, kun haku ei löytänyt yhtään viitettä.
* Palvelin hyväksyy vain positiiviset kokonaislukutunnisteet, kunkin kerran ja
  enintään 500 (`util.selected_ids`), ja poistaa ne yhdellä kyselyllä ehdolla
  `user_id = kirjautunut käyttäjä` (`reference_repository.delete_references`).
  Toisen käyttäjän viitteiden tunnisteet ohitetaan.
* Poiston jälkeen palataan samaan listaan hakuineen ja näytetään
  `2 references deleted`. Jos mitään ei valittu, näytetään `No references
  selected`, ja jos mikään valituista ei ollut käyttäjän, `No references
  deleted`.
* Tietokannan rakenne ei muutu, joten klusterin tietokantaa ei tarvitse luoda
  uudelleen (ks. luku 11).

### .bib-tiedosto valituista viitteistä (`/references/bib`)

* `select all`- ja `delete`-painikkeen välissä on `create .bib`. Se on harmaa ja
  poissa käytöstä, kun yhtään viitettä ei ole valittu (`select.js`).
* Painike lähettää saman lomakkeen kuin `delete` (valintaruudut, CSRF-tunniste
  ja `back`), mutta `formaction`-attribuutti ohjaa sen osoitteeseen
  `/references/bib`. Varmistusta ei kysytä, koska mitään ei muuteta.
* Palvelin hakee valitut viitteet yhdellä kyselyllä vain käyttäjän omista
  (`reference_repository.get_references_by_ids`, uusin ensin, samassa
  järjestyksessä kuin listalla) ja palauttaa ne BibTeX-muodossa
  (`bibtex.to_bibtex`) tyhjällä rivillä erotettuina. Vastauksen tyyppi on
  `application/x-bibtex`, ja `Content-Disposition: attachment` saa selaimen
  tallentamaan sen tiedostoon `references.bib`. Sivu ja valinnat pysyvät
  ennallaan.
* Jos yhtään omaa viitettä ei valittu, palataan listaan ilmoituksella
  `No references selected`.
* Tietokannan rakenne ei muutu tässäkään, joten klusterilla ei tarvita toimenpiteitä.

### BibTeX-muotoilu (`bibtex.to_bibtex`)

```
@article{dijkstra1968,
  author  = {Dijkstra, Edsger W.},
  title   = {Go To Statement Considered Harmful},
  journal = {Communications of the ACM},
  year    = {1968},
  pages   = {147--148}
}
```

* Kentät samassa järjestyksessä kuin lomakkeessa, vain täytetyt kentät,
  `=`-merkit tasattuna, arvot aaltosulkeissa.
* Sivuvälin yksittäinen viiva numeroiden välissä muutetaan BibTeXin
  kaksoisviivaksi (`12-34` → `12--34`).
* Merkit `&`, `%` ja `#` escapoidaan (`\&`), ellei käyttäjä ole jo tehnyt sitä.
  Kentät `doi` ja `isbn` kirjoitetaan sellaisinaan.
* Muuhun sisältöön ei kosketa: ääkköset säilyvät UTF-8:na (toimii nykyisillä
  LaTeX-asennuksilla), ja käyttäjä voi kirjoittaa itse LaTeX-merkintää, esim.
  `{UNIX}` isojen kirjainten suojaamiseksi tai `$O(n)$`.
* Koska arvot kääritään aaltosulkeisiin, pariton `{` tai `}` rikkoisi tietueen.
  Siksi lisäyksen validointi hylkää kentät, joiden aaltosulkeet eivät täsmää.

### Lähdeluettelomuoto (`citation.to_citation`)

Bibtex-sivun lähdeviitelaatikon viite on APA:n kaltaisessa muodossa:

| Tyyppi | Muoto |
| --- | --- |
| article | Kirjoittajat (vuosi). Otsikko. *Journal*, *volume*(number), sivut. DOI |
| book | Kirjoittajat (vuosi). *Otsikko* (edition ed.). Address: Publisher. ISBN |
| inproceedings | Kirjoittajat (vuosi). Otsikko. In *Booktitle* (pp. sivut). Publisher. DOI |

* Valinnaiset kentät jätetään pois, jos ne ovat tyhjiä.
* Kirjoittajat erotetaan `and`-sanan kohdalta ja yhdistetään muotoon
  `A & B` tai `A, B, & C`. Nimet näytetään sellaisinaan, eikä etunimiä
  lyhennetä.
* Sivuvälin viiva muutetaan ajatusviivaksi (`12-34` → `12–34`), ja DOI:n eteen
  lisätään `https://doi.org/`, ellei se jo ole osoite.
* Pistettä ei lisätä, jos teksti päättyy jo pisteeseen, kysymys- tai
  huutomerkkiin.
* Funktio palauttaa valmiin HTML:n (`Markup`), jossa kursivointi on
  `<i>`-elementteinä. Jokainen kentän arvo escapoidaan (`markupsafe.escape`),
  joten käyttäjän syöttämä HTML näkyy tekstinä. LaTeX-merkintää ei muunneta.

## 9. Käyttöliittymä

* **Yläpalkki** (vain kirjautuneelle, kaikilla sivuilla): vasemmalla `add` ja
  `view / search`, keskellä sovelluksen nimi, oikealla `log out`. Sivu, jolla
  ollaan, on alleviivattu (luokka `active`, päätellään `request.endpoint`ista).
* **Kirjautumis- ja rekisteröintisivu:** ei yläpalkkia, vain sovelluksen nimi
  lomakkeen yläpuolella. Kirjautumissivulla `register`-painike vie
  rekisteröintisivulle, jolta pääsee takaisin painikkeella `back to log in`.
* Käyttöliittymän tekstit ovat englanniksi ja pienellä kirjoitettuja.
* Virheilmoitukset ovat punaisia; onnistumisilmoitukset
  (`.flash.notice`) ovat tavallisen tekstin värisiä.
* Listaus ja bibtex-sivu käyttävät samaa 46 rem:n keskitettyä palstaa;
  bibtex-sivun painikkeet ovat palstan sisällä BibTeX-laatikon yläpuolella.
* Yläpalkillisilla sivuilla (listaus, lisäys, bibtex-sivu) sisällön yläpuolella
  on noin painikkeen korkeuden verran lisätilaa.
* Advanced-haun kentät ovat kahdessa sarakkeessa samalla lomaketyylillä kuin
  lisäyslomake; tyyppi valitaan samanlaisilla tekstivalinnoilla kuin
  lisäyslomakkeessa.

## 10. Testaus ja CI

### pytest (`src/tests/`)

| Tiedosto | Kattaa |
| --- | --- |
| `validation_test.py` | Käyttäjätunnuksen ja salasanan säännöt |
| `user_repository_test.py` | Käyttäjän luonti, hajautus, uniikkius, kirjautumisen tarkistus |
| `db_helper_test.py` | Taulujen luonti, nollaus ja tyhjennys |
| `login_test.py` | Reitit Flaskin testiasiakkaalla: ohjaukset, rekisteröinti, kirjautuminen, uloskirjautuminen, yläpalkki, `/reset_db` |
| `reference_validation_test.py` | Tyyppimäärittelyt, viitteen ja avaimen validointi, aaltosulkeiden täsmäys, sukunimen poiminta, avaimen generointi |
| `reference_repository_test.py` | Viitteen tallennus ja luku, avaimen uniikkius ja generointi, käyttäjäkohtaisuus, erikoismerkit, viiteavainrajoite |
| `bibtex_test.py` | BibTeX-muotoilu kaikille tyypeille, erikoismerkit, sivuvälit |
| `citation_test.py` | Lähdeluettelomuoto kaikille tyypeille pakollisilla ja kaikilla kentillä, kirjoittajien yhdistäminen, pisteet, sivuvälit, escapointi |
| `references_test.py` | Listaus (sisältö, järjestys, vain omat viitteet, escapointi), bibtex-sivu (sisältö, painikkeiden järjestys, lähdeviite- ja kenttälaatikko sekä niiden escapointi, 404 toisen käyttäjän viitteelle), back-osoitteen rajaus |
| `edit_reference_test.py` | Bibtex-sivun edit- ja delete-painikkeet, muokkauslomake (nykyiset arvot, sijainti, back-osoitteen säilyminen), tallennus (kentät, tyypin vaihto, avaimen vaihto ja uudelleengenerointi, virhetilanteet), poisto, kirjautumis- ja CSRF-vaatimus, toisen käyttäjän viitteet |
| `add_reference_test.py` | Lisäysreitti: lomake, kaikki kolme tyyppiä, virhetilanteet, arvojen säilyminen ja escapointi, kirjautumis- ja CSRF-vaatimus |
| `search_test.py` | Hakusanojen pilkkominen, haku jokaisesta kentästä, kirjainkoko ja ääkköset, usea sana, erikoismerkit, vain omat viitteet, listaussivun hakulomake ja tulokset, paluu hakuun |
| `advanced_search_test.py` | Hakuparametrien siivous ja validointi, jokainen suodatin erikseen ja yhdessä, ero perushakuun, erikoismerkit, vain omat viitteet, listaussivun advanced-osio (auki/kiinni, arvojen säilyminen), osoitteen siistiminen, virheelliset arvot, paluu hakuun |
| `bib_file_test.py` | .bib-tiedosto valituista viitteistä: painike listalla, tiedoston sisältö ja järjestys, lataus (`Content-Disposition`), erikoismerkit, ei muutoksia, ei valintoja, vain omat viitteet, CSRF, kirjautuminen, repositorio |
| `duplicate_test.py` | Saman viitteen tunnistus (sama tyyppi ja kentät, avaimesta riippumatta; yksi kenttä, tyyppi tai käyttäjä eri; muokattava viite ohitetaan), vahvistusikkuna lisäyksessä ja muokkauksessa, mitään ei tallenneta ennen vahvistusta, arvojen säilyminen, `confirm_duplicate`, ei ikkunaa tavallisesti |
| `delete_selected_test.py` | Valittujen viitteiden tunnisteiden siivous, listan delete- ja select all -painike, lomake ja valintaruudut, poisto (yksi, useita, kaikki), ilmoitukset, paluu hakuun, back-osoitteen rajaus, ei valintoja, tuntemattomat tunnisteet, CSRF, kirjautuminen, toisen käyttäjän viitteet, repositorio |

`conftest.py` asettaa `DATABASE_URL`:n väliaikaistiedostoon ennen sovelluksen
importtaamista, joten testit eivät koske kehitystietokantaan. Jokainen testi
alkaa tyhjästä tietokannasta (`setup_db()` automaattisessa fixturessa).
Fixture `actions` tarjoaa apumetodit `register`, `login`, `logout`, `session` ja
`add_reference` (lähettää oletuksena kelvollisen artikkelin CSRF-tunnisteineen).

### Robot Framework (`src/story_tests/`)

`login.robot` testaa samat käyttäjätarinat oikealla selaimella (Chromium):
ohjaus kirjautumissivulle, rekisteröinti ja sen virhetilanteet, kirjautuminen,
uloskirjautuminen sekä yläpalkin linkit ja alleviivaus. Yhteiset avainsanat ovat
`resource.robot`issa. Tietokanta tyhjennetään ennen jokaista testiä (`/reset_db`).

`add_reference.robot` testaa lisäyslomakkeen: kenttien vaihtuminen tyypin
mukaan, "(optional)"-merkinnät, kaikkien kolmen tyypin lisääminen, oma ja
generoitu avain, käytössä oleva avain, selaimen pakollisuus- ja
vuosilukutarkistukset sekä se, etteivät piilotetut kentät estä lähetystä.

`references.robot` testaa listauksen ja bibtex-sivun: tyhjä lista, järjestys,
laatikon reunus, laatikon klikkaus, copy-painike (leikepöydän sisältö luetaan
selaimesta ja verrataan sivun BibTeXiin; selainkontekstille annetaan
leikepöytäoikeudet), painikkeiden sijainti BibTeX-laatikon yläpuolella sen
reunojen sisällä (myös 360 px leveällä näytöllä), lähdeviite- ja kenttälaatikko
BibTeXin alla erillisinä ja samanlevyisinä sekä niiden sisältö, back-painike ja
se, ettei toisen käyttäjän viitettä näe.

`search.robot` testaa haun selaimessa: yksi hakukenttä listan yläpuolella,
haku otsikolla, kirjoittajalla ja vuodella, kirjainkoko ja ääkköset,
enter-näppäin, tulokseton haku, `show all` ja paluu hakutulokseen
bibtex-sivulta.

`advanced_search.robot` testaa advanced-haun selaimessa: painikkeen sijainti
hakukentän alla, kenttien avaaminen ja sulkeminen, haku jokaisella kentällä,
ehtojen yhdistäminen, osion pysyminen auki haun jälkeen, virheellinen vuosi,
`show all` ja paluu hakutulokseen bibtex-sivulta.

`edit_reference.robot` testaa muokkauksen ja poiston selaimessa: lomakkeen
avautuminen BibTeXin yläpuolelle nykyisillä arvoilla, painikkeet lomakkeen
yläpuolella, save ja cancel, tyypin ja avaimen vaihto, virheellinen arvo,
muutoksen näkyminen BibTeXissä, tiedoissa ja listassa, paluu hakuun
sekä poisto varmistuksineen (hyväksytty ja peruttu).

`delete_selected.robot` testaa valittujen viitteiden poiston selaimessa:
`search`, `advanced` ja `delete` samanlevyisinä allekkain ja niiden välit,
`delete` advanced-kenttien alapuolella, harmaa painike ilman valintoja,
valintaruudun paikka laatikon oikeassa alakulmassa ja sen viiva, rasti
valittuna, se ettei valinta avaa viitettä, poisto varmistuksineen
(hyväksytty ja peruttu) ja paluu hakuun sekä `select all` / `unselect`
(sijainti, kaikkien valinta ja valintojen poisto, tekstin vaihtuminen käsin
valittaessa, vain hakutulokset, poissa käytöstä ilman tuloksia).

`bib_file.robot` testaa .bib-tiedoston selaimessa: `create .bib` -painikkeen
paikka `select all`- ja `delete`-painikkeen välissä, harmaannus valintojen
mukaan, ladatun tiedoston nimi ja sisältö (valitut ja kaikki viitteet) sekä se,
ettei lataus kysy varmistusta, poista mitään tai muuta sivua.
Selainkonteksti hyväksyy lataukset (`acceptDownloads`), ja tiedosto
tallennetaan väliaikaishakemistoon.

`duplicate.robot` testaa saman viitteen vahvistusikkunan selaimessa: teksti ja
painikkeet, modaalisuus, painikkeiden tyyli (ei selaimen kohdistusreunusta),
`add` lisää viitteen uudella avaimella, `cancel` ja Esc sulkevat ikkunan
lomakkeen jäädessä täytetyksi, erilainen viite lisätään kysymättä sekä
muokkauksen `save`- ja `cancel`-valinnat.

### Skriptit

* `./test.sh` ajaa molemmat, `./test.sh unit` vain pytestin ja `./test.sh robot`
  vain Robot-testit. Robot-testejä varten skripti asentaa testiselaimen, luo
  tietokannan `robot_test.db`, käynnistää sovelluksen testitilassa taustalle,
  odottaa että se vastaa, ajaa testit ja pysäyttää sovelluksen aina lopuksi
  (myös virhetilanteessa). Jos portti on jo käytössä, skripti keskeytyy
  selkeään virheilmoitukseen.
* `./run.sh` asentaa riippuvuudet, luo tarvittaessa `.env`:n ja tietokannan ja
  käynnistää sovelluksen debug-tilassa (`DEBUG=true`).
* Skriptit ovat bashia, käyttävät vain `uv`:tä ja `curl`ia ja toimivat macOS:llä
  ja Linuxilla. Ne poistavat `VIRTUAL_ENV`-muuttujan, jotta toisen projektin
  aktiivinen virtuaaliympäristö ei sotke uv:tä.

### pylint ja Git-hook

* `uv run pylint src` tarkistaa koodin tyylin. Asetukset ovat `pyproject.toml`:ssä:
  rivin enimmäispituus 100 merkkiä, ja docstring-vaatimukset sekä pytestin
  fixtureihin liittyvät huomautukset on poistettu käytöstä. Lyhyet toistuvat
  koodilohkot (alle 8 riviä) sallitaan.
* `.githooks/pre-commit` ajaa ennen jokaista committia `./test.sh unit` ja
  pylintin; commit hyväksytään vain, jos molemmat menevät läpi. Robot-testejä ei
  ajeta hookissa, koska ne ovat hitaita ja tarvitsevat vapaan portin. Hook
  otetaan käyttöön kerran työkopiossa: `git config core.hooksPath .githooks`.

### GitHub Actions

`.github/workflows/ci.yaml` ajaa jokaisella pushilla (kaikki haarat) ja mainiin
kohdistuvalla pull requestilla: `./test.sh unit`, selaimen asennus,
`./test.sh robot` ja pylint. Epäonnistuessa Robot-raportti tallennetaan
artefaktiksi.

`.github/workflows/docker.yaml` käynnistyy, kun CI-ajo main-haarassa on
valmis, ja vain jos se onnistui. Se rakentaa Docker-kuvan ja julkaisee sen
osoitteeseen `ghcr.io/late-1/talj-projekti:latest` (ks. luku 11).

`.github/workflows/release.yaml` käynnistyy, kun pushataan tagi `v*` (esim.
`v1.1.0`). Se ajaa yksikkötestit ja pylintin, julkaisee Docker-kuvan
tunnisteilla `<tagi>` ja `latest` ja luo tagille GitHub Releasen. Releasen
kuvaus on `CHANGELOG.md`:n kohta `## <versio> - <päivämäärä>` seuraavaan
`## `-otsikkoon asti, ja perään lisätään linkit (README, arkkitehtuurikuvaus,
muutosloki, pelisäännöt, Docker-kuva). Jos kohtaa ei ole tai se on tyhjä, työ
epäonnistuu. Uuden version kohta lisätään siis CHANGELOGiin ennen tagia.
Koska kuva julkaistaan myös tunnisteella `latest`, jota klusteri seuraa, tagi
tehdään mainin uusimpaan committiin; vanhemman commitin tagi palauttaisi
klusterille vanhan version.

Epäonnistunut ajo merkitsee commitin punaisella rastilla. GitHub ei voi perua jo
pushattua committia; jos virheellisten muutosten pääsy mainiin halutaan estää
kokonaan, repositorion asetuksista on lisättävä main-haaralle branch protection
-sääntö (*Require status checks to pass* → `test`) ja tehtävä muutokset pull
requestien kautta. Tätä ei voi asettaa koodista.

## 11. Julkaisu (OKD)

Sovellus julkaistaan kurssin OKD-klusterille boilerplaten ohjeen
[DEPLOYMENT.md](https://github.com/ohjelmistotuotanto-hy/miniprojekti-boilerplate/blob/main/DEPLOYMENT.md)
mukaisesti.

### Docker-kuva

`Dockerfile` perustuu kuvaan `python:3.12-slim`, asentaa riippuvuudet uv:llä
ilman kehitysriippuvuuksia (`uv sync --no-dev`), kopioi hakemiston `src/` ja
käynnistää sovelluksen komennolla `python src/index.py` porttiin 5001.
`.dockerignore` pitää virtuaaliympäristön, `.env`:n, tietokannat ja
testiraportit poissa kuvasta.

### Klusterin resurssit

`kustomization.yaml` kokoaa resurssit, asettaa OKD-projektin (`namespace`),
Docker-kuvan osoitteen ja sovelluksen julkisen osoitteen sekä luo
salaisuuden `secret` tiedostosta `secret.env`.

| Tiedosto | Resurssi | Tehtävä |
| --- | --- | --- |
| `manifests/configmap.yaml` | ConfigMap `config` | Ympäristömuuttujat: `DATABASE_URL=sqlite:////app/data/database.db`, `TEST_ENV=false`, `HOST=0.0.0.0` |
| `manifests/imagestream.yaml` | ImageStream `app` | Seuraa kuvaa `ghcr.io/late-1/talj-projekti:latest` ja tarkistaa ajoittain (noin vartin välein), onko siitä uusi versio |
| `manifests/deployment.yaml` | Deployment `dep` | Yksi kontti; käynnistyy uudelleen, kun ImageStreamiin tulee uusi kuva. Ympäristö ConfigMapista ja salaisuudesta, pysyvä levy hakemistoon `/app/data`, muistiraja 256 Mi |
| `manifests/service.yaml` | Service `svc` | Klusterin sisäinen osoite, portti 80 → kontin portti 5001 |
| `manifests/route.yaml` | Route `route` | Julkinen HTTPS-osoite (`kustomization.yaml` asettaa osoitteen); HTTP ohjataan HTTPS:ään |
| `manifests/volumeclaim.yaml` | PersistentVolumeClaim `claim` | 1 Gi:n pysyvä levy SQLite-tietokannalle |
| `manifests/kustomizeconfig.yaml` | – | Kertoo Kustomizelle, mistä ImageStreamin kuvan osoite löytyy |

### Päivittyminen

1. Muutos pushataan main-haaraan, ja CI ajaa testit ja pylintin.
2. Jos CI onnistuu, `docker.yaml` julkaisee uuden kuvan.
3. ImageStream huomaa uuden kuvan, ja Deployment käynnistää sovelluksen
   uudelleen. Heti päivittäminen: `oc import-image app:latest`.

Muutokset tiedostoihin `kustomization.yaml`, `manifests/` ja `secret.env`
eivät päivity pushaamalla, vaan ne viedään klusterille komennolla
`oc apply -k .`. Kuvan on oltava GitHubissa julkinen, jotta klusteri voi
hakea sen.

### Tietokanta klusterilla

Tietokanta on pysyvällä levyllä ja säilyy päivitysten ja uudelleenkäynnistysten
yli, mutta tauluja ei luoda automaattisesti. Ne luodaan ensimmäisen
julkaisun jälkeen ja aina, kun `src/schema.sql` on muuttunut ja uusi versio on
käynnissä (`oc rollout status deploy/dep`):

```sh
oc exec deploy/dep -- python src/db_helper.py
```

Komento pudottaa taulut ja luo ne uudelleen, joten **kaikki klusterin data
häviää**.

## 12. Päätökset

Keskeiset valinnat koottuna; yksityiskohdat ovat viitatuissa luvuissa.

**Käyttäjät**

* Rekisteröinti on omalla sivullaan eikä kirjautumissivun sisällä, ja
  onnistunut rekisteröinti kirjaa suoraan sisään.
* Kirjautumisen jälkeen avautuu viitelistaus.
* Uloskirjautuminen on tavallinen linkki ilman CSRF-suojausta
  (yksinkertaisuus, ks. luku 7).

**Viitteet**

* Samanlaisen viitteen voi lisätä tai tallentaa, mutta vasta vahvistuksen
  jälkeen. Viite on sama, kun tyyppi ja kaikki kentät ovat samat avaimesta
  riippumatta; tarkistus tehdään palvelimella, jotta se koskee kaikkia
  tallennuksia.

* Tuetut tyypit ovat `article`, `book` ja `inproceedings`; lomakkeen kentät
  vaihtuvat valitun tyypin mukaan. Tyypit ja kentät on määritelty yhdessä
  paikassa (`reference_types.py`), joten uuden tyypin lisääminen on pieni muutos.
* Viiteavain on automaattinen mutta muokattavissa: tyhjäksi jätettynä se
  generoidaan muodossa ensimmäisen kirjoittajan sukunimi + vuosi
  (`martin2008`), ja törmäyksessä perään lisätään kirjain (`martin2008a`,
  `martin2008b`, …). Avain on uniikki käyttäjäkohtaisesti.
* Kirjoittajat ovat vapaata tekstiä BibTeX-muodossa (`and`-sanalla eroteltuna)
  eivätkä omia tietueitaan; muotoa ei pakoteta.
* Vuosi on nelinumeroinen ja tallennetaan tekstinä, kuten muutkin kentät.
* Jokainen BibTeX-kenttä on oma sarakkeensa taulussa `bib_references` (ei
  avain–arvo-taulua), mikä pitää kyselyt yksinkertaisina.
* Lisäyksen jälkeen palataan tyhjään lisäyslomakkeeseen sama tyyppi valittuna,
  mikä helpottaa usean viitteen lisäämistä peräkkäin.
* BibTeX-muotoilu escapoi vain merkit `&`, `%` ja `#`; muu sisältö jätetään
  ennalleen, jotta käyttäjä voi kirjoittaa itse LaTeX-merkintää.

**Listaus ja haku**

* Listauksen laatikossa näytetään vain olennaisin (otsikko, kirjoittajat,
  vuosi, julkaisupaikka, tyyppi ja avain).
* Listauksessa ei ole sivutusta; kaikki käyttäjän viitteet näytetään kerralla.
* Haku on osoitteessa (GET-lomake), joten sen voi tallentaa kirjanmerkiksi ja
  bibtex-sivulta palataan samaan hakutulokseen.
* Hakusanat yhdistetään JA-ehdolla, sanan osa riittää, kirjainkoolla ei ole
  väliä, eikä aksentteja poisteta.
* Haku tehdään yhdellä SQL-kyselyllä tietokannassa eikä Pythonissa, joten
  kaikkia viitteitä ei tarvitse hakea muistiin.
* Advanced-haku on samassa lomakkeessa kuin perushaku ja toimii ilman
  JavaScriptiä (`<details>`), joten koko haku on osoitteessa.
* Advanced-haussa journal, booktitle ja publisher on yhdistetty yhdeksi
  "published in" -kentäksi; harvinaisemmille kentille (volume, pages, doi, …)
  ei ole omaa hakukenttää, mutta perushaku kattaa ne.

* Useamman viitteen poisto tehdään listalta valintaruuduilla ja yhdellä
  `delete`-painikkeella, joka on hakupainikkeiden alla. `select all` valitsee
  kerralla kaikki listalla näkyvät viitteet, eli hakua voi käyttää poistettavien
  rajaamiseen. Poisto vaatii varmistuksen, ja se kohdistuu vain käyttäjän
  omiin viitteisiin.

* Valituista viitteistä voi ladata .bib-tiedoston (`create .bib`), jonka voi
  liittää LaTeX-dokumenttiin sellaisenaan. Tiedosto luodaan palvelimella samalla
  BibTeX-muotoilulla kuin bibtex-sivulla, eikä sitä tallenneta.

**Bibtex-sivu**

* Muokkaus ja poisto tehdään bibtex-sivulta; poisto vaatii varmistuksen,
  koska sitä ei voi perua.
* Painikkeet ovat BibTeX-laatikon yläpuolella palstan sisällä eivätkä sen
  sivuilla, joten sivu mahtuu kapeallekin näytölle samassa järjestyksessä.
* BibTeXin alla näytetään viite myös luettavassa muodossa omissa laatikoissaan:
  lähdeluettelotyylinen viite (APA:n kaltainen, yksi kiinteä tyyli) ja
  kenttäluettelo. Tyylin valintaa ei ole, koska BibTeX on sovelluksen
  varsinainen tuotos ja LaTeX muotoilee lähdeluettelon itse.

**Ympäristö**

* Flaskin debug-tila on oletuksena pois ja otetaan käyttöön erikseen
  muuttujalla `DEBUG=true` (`run.sh` tekee sen paikallisesti). Debug-tila ei saa
  olla päällä julkisessa osoitteessa, koska se näyttää virhetilanteessa
  tracebackin ja lähdekoodia. Debug-tilaa ei sidota `TEST_ENV`-muuttujaan,
  koska `TEST_ENV=true` avaa myös reitin `/reset_db`.
