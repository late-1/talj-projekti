# miniprojekti

[![CI](https://github.com/late-1/talj-projekti/actions/workflows/ci.yaml/badge.svg)](https://github.com/late-1/talj-projekti/actions/workflows/ci.yaml)

Web-sovellus lähdeviitteiden hallintaan ja niiden viemiseen BibTeX-muodossa
LaTeX-dokumentteihin. Toteutettu Flaskilla ja SQLitellä.

Lukekaa [pelisäännöt](pelisaannot.md).

Nykyiset ominaisuudet:

* käyttäjätunnuksen luominen, sisään- ja uloskirjautuminen
* viitteen lisääminen lomakkeella: artikkeli (`article`), kirja (`book`) tai
  konferenssijulkaisu (`inproceedings`)
* viiteavain (`\cite{avain}`) luodaan automaattisesti kirjoittajan ja vuoden
  perusteella, tai sen voi antaa itse
* omien viitteiden listaus; viitettä klikkaamalla aukeaa sen BibTeX-muoto, jonka
  saa leikepöydälle Copy-painikkeella

## Vaatimukset

* macOS tai Linux
* [uv](https://docs.astral.sh/uv/getting-started/installation/) (asentaa oikean Python-version ja kaikki riippuvuudet)
* `curl` (vain testien ajamiseen)

## Sovelluksen käynnistäminen

```
./run.sh
```

Sovellus aukeaa osoitteeseen http://localhost:5001. Pysäytä se näppäimillä `Ctrl+C`.

Ensimmäisellä kerralla skripti asentaa riippuvuudet, luo `.env`-tiedoston
satunnaisella salaisella avaimella ja luo tietokannan. Myöhemmillä kerroilla
olemassa oleva tietokanta säilyy, ja siihen lisätään puuttuvat taulut.

Toisen portin käyttäminen:

```
PORT=8000 ./run.sh
```

Tietokannan tyhjentäminen (pysäytä sovellus ensin):

```
uv run python src/db_helper.py
```

## Testien ajaminen

```
./test.sh
```

Komento ajaa sekä yksikkötestit (pytest) että selaintestit (Robot Framework).
Testit käyttävät omia väliaikaisia tietokantojaan, joten ne eivät muuta
sovelluksen tietoja. Ensimmäinen ajokerta lataa testiselaimen (Chromium), mikä
kestää hetken.

Testityypit voi ajaa myös erikseen:

```
./test.sh unit     # vain pytest, nopea
./test.sh robot    # vain Robot Framework
```

Selaintestit käynnistävät sovelluksen porttiin 5001, joten pysäytä sovellus
ennen niiden ajamista tai valitse toinen portti: `PORT=8000 ./test.sh`.
Selaintestien jälkeen yksityiskohtainen raportti on tiedostossa `report.html`.

## Koodin tyylin tarkistus

```
uv run pylint src
```

Pylintin asetukset ovat tiedostossa `pyproject.toml`.

GitHub Actions ajaa testit ja pylintin jokaisella pushilla ja pull requestilla.

## Ennen committia

Ota Git-hook käyttöön kerran tässä työkopiossa:

```bash
git config core.hooksPath .githooks
```

Tämän jälkeen `git commit` suorittaa ensin yksikkötestit (`./test.sh unit`) ja
pylintin (`uv run pylint src`). Commit hyväksytään vain, jos molemmat menevät
läpi. Selaintestejä ei ajeta commitin yhteydessä, koska ne ovat hitaampia; aja
ne komennolla `./test.sh` ennen pushia.

## Projektin rakenne

```
run.sh, test.sh         skriptit sovelluksen ja testien ajamiseen
.githooks/pre-commit    ennen committia ajettavat tarkistukset
src/index.py            käynnistää palvelimen
src/app.py              reitit
src/config.py           Flaskin ja tietokannan asetukset
src/db_helper.py        tietokannan luominen ja tyhjentäminen
src/schema.sql          tietokannan taulut
src/util.py             syötteiden validointi, viiteavaimen muodostus
src/reference_types.py  tuetut viitetyypit ja niiden kentät
src/bibtex.py           viitteen muotoilu BibTeX-muotoon
src/repositories/       tietokantakyselyt
src/entities/           tietoa kuvaavat luokat
src/templates/          HTML-sivut
src/static/             tyylit ja selaimessa ajettavat skriptit
src/tests/              yksikkötestit (pytest)
src/story_tests/        selaintestit (Robot Framework)
```
