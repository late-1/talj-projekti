# miniprojekti

[![CI](https://github.com/late-1/talj-projekti/actions/workflows/ci.yaml/badge.svg)](https://github.com/late-1/talj-projekti/actions/workflows/ci.yaml)

[OKD](https://route-ohjelmistotuotanto-lahiopetus-2026-22.ext.okd-cs-test-0.k8s.cs.helsinki.fi/)

Web-sovellus lähdeviitteiden hallintaan ja niiden viemiseen BibTeX-muodossa
LaTeX-dokumentteihin. Toteutettu Flaskilla ja SQLitellä.

Sovelluksen rakenne ja tekniset ratkaisut on kuvattu
[arkkitehtuurikuvauksessa](docs/arkkitehtuurikuvaus/README.md).

Lukekaa [pelisäännöt](pelisaannot.md).

Nykyiset ominaisuudet:

* käyttäjätunnuksen luominen, sisään- ja uloskirjautuminen
* viitteen lisääminen lomakkeella: artikkeli (`article`), kirja (`book`) tai
  konferenssijulkaisu (`inproceedings`), ja `more`-valikosta muut BibTeXin
  vakiotyypit (`booklet`, `conference`, `inbook`, `incollection`, `manual`,
  `mastersthesis`, `misc`, `phdthesis`, `proceedings`, `techreport`,
  `unpublished`) niiden omine kenttineen
* viiteavain (`\cite{avain}`) luodaan automaattisesti kirjoittajan ja vuoden
  perusteella (ilman kirjoittajaa toimittajasta tai otsikon ensimmäisestä
  sanasta), tai sen voi antaa itse
* omien viitteiden listaus; viitettä klikkaamalla aukeaa sen BibTeX-muoto, jonka
  saa leikepöydälle `copy`-painikkeella
* viitteiden haku yhdellä hakukentällä, joka hakee viitteen kaikesta sisällöstä
  (kirjoittaja, otsikko, vuosi, julkaisu, avain jne.)
* tarkennettu haku `advanced`-painikkeen takana: kirjoittaja, otsikko,
  julkaisupaikka, avain, vuosiväli ja viitteen tyyppi
* viitteen muokkaaminen ja poistaminen sen BibTeX-sivulta (`edit` ja `delete`)
* useamman viitteen poistaminen kerralla: viitteet valitaan listalta
  valintaruuduilla (tai kaikki kerralla `select all` -painikkeella) ja
  poistetaan `delete`-painikkeella
* .bib-tiedoston luominen valituista viitteistä (`create .bib`)
* jos täsmälleen sama viite on jo olemassa, sen lisääminen tai tallentaminen
  varmistetaan ensin
* BibTeX-sivulla BibTeXin alla viitteen tiedot luettavassa muodossa:
  lähdeluettelotyylinen viite ja kaikki täytetyt kentät

## Definition of Done

Käyttäjätarina on valmis, jos
1) Hyväksymiskriteerit määritelty ja läpäisty, hyväksymiskriteerit määritellään Robot Framework- testeillä (jo 1. sprintissä)
2) Toiminnallisuuden sisältävä koodin ja siihen liittyvät testit (3 ja 4) on katselmoinut ryhmän jäsenistä joku muu kuin koodin luoja, katselmointi merkitään tarinan kommentteihin
3) Koodille on luotu yksikkötestit ja läpäisty (pytest)
4) Koodi noudattaa sovittua koodityyliä ja läpäisee kaikki testit täysillä pisteillä (pylint)
5) Koodi on työnnetty päärepositorioon ja CI (GitHub Actions) on vihreällä

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

`run.sh` käynnistää sovelluksen Flaskin debug-tilassa (`DEBUG=true`). Muuten,
esimerkiksi OKD-klusterilla, debug-tila on pois päältä.

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

## Julkaisut

Julkaisu luodaan semanttisen versionumeron tagilla:

1. Lisää [CHANGELOG.md](CHANGELOG.md)-tiedoston alkuun uuden version kohta
   muodossa `## 1.1.0 - vvvv-kk-pp`, commitoi ja pushaa se.
2. Tee tagi mainin uusimpaan committiin ja pushaa se:

```bash
git tag -a v1.1.0 -m "Release 1.1.0"
git push origin v1.1.0
```

Tagin push käynnistää `Create release`-työn, joka ajaa yksikkötestit,
Pylintin tarkistuksen ja julkaisee Docker-kuvat GitHub Container Registryyn.
GitHub Release luodaan automaattisesti tagille, ja sen kuvaus otetaan
CHANGELOG.md:n kyseisen version kohdasta. Jos kohta puuttuu, työ epäonnistuu.

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
src/citation.py         viitteen muotoilu lähdeluettelon muotoon
src/repositories/       tietokantakyselyt
src/entities/           tietoa kuvaavat luokat
src/templates/          HTML-sivut
src/static/             tyylit ja selaimessa ajettavat skriptit
src/tests/              yksikkötestit (pytest)
src/story_tests/        selaintestit (Robot Framework)
```
## Projektin linkit

[Pelisäännöt](https://github.com/late-1/talj-projekti/blob/main/pelisaannot.md)  
[OKD](https://route-ohjelmistotuotanto-lahiopetus-2026-22.ext.okd-cs-test-0.k8s.cs.helsinki.fi/)  
[Backlog](https://github.com/users/late-1/projects/2)