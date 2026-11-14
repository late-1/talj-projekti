# miniprojekti

[![CI](https://github.com/late-1/talj-projekti/actions/workflows/ci.yaml/badge.svg)](https://github.com/late-1/talj-projekti/actions/workflows/ci.yaml)

Web-sovellus lähdeviitteiden hallintaan ja niiden viemiseen BibTeX-muodossa
LaTeX-dokumentteihin. Toteutettu Flaskilla ja SQLitellä.

Lukekaa [pelisäännöt](pelisaannot.md).

Nykyiset ominaisuudet:

* käyttäjätunnuksen luominen, sisään- ja uloskirjautuminen

## Vaatimukset

* macOS tai Linux
* [uv](https://docs.astral.sh/uv/getting-started/installation/) (asentaa oikean Python-version ja kaikki riippuvuudet)

## Sovelluksen käynnistäminen

```
./run.sh
```

Sovellus aukeaa osoitteeseen http://localhost:5001. Pysäytä se näppäimillä `Ctrl+C`.

Ensimmäisellä kerralla skripti asentaa riippuvuudet, luo `.env`-tiedoston
satunnaisella salaisella avaimella ja luo tietokannan. Myöhemmillä kerroilla
olemassa oleva tietokanta säilyy.

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

Komento ajaa yksikkötestit (pytest). Testit käyttävät omaa väliaikaista
tietokantaansa, joten ne eivät muuta sovelluksen tietoja.

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

Tämän jälkeen `git commit` suorittaa ensin yksikkötestit (`uv run pytest src/tests`)
ja pylintin (`uv run pylint src`). Jos `src/tests` sisältää Robot Frameworkin
`.robot`-testejä, myös ne suoritetaan. Commit hyväksytään vain, jos kaikki
menevät läpi.

## Projektin rakenne

```
run.sh, test.sh         skriptit sovelluksen ja testien ajamiseen
.githooks/pre-commit    ennen committia ajettavat tarkistukset
src/index.py            käynnistää palvelimen
src/app.py              reitit
src/config.py           Flaskin ja tietokannan asetukset
src/db_helper.py        tietokannan luominen ja tyhjentäminen
src/schema.sql          tietokannan taulut
src/util.py             syötteiden validointi
src/repositories/       tietokantakyselyt
src/entities/           tietoa kuvaavat luokat
src/templates/          HTML-sivut
src/static/main.css     tyylit
src/tests/              yksikkötestit (pytest)
```
