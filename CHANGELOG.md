# Muutosloki

## 1.3.0

### Ominaisuudet

- Viitteen voi lisätä kaikilla BibTeXin vakiotyypeillä: article-, book- ja
  inproceedings-tyyppien vieressä olevasta `more`-valikosta löytyvät
  `booklet`, `conference`, `inbook`, `incollection`, `manual`,
  `mastersthesis`, `misc`, `phdthesis`, `proceedings`, `techreport` ja
  `unpublished` omine kenttineen
- Uudet kentät: editor, chapter, school, institution, organization,
  howpublished, month, series, url ja note
- Viiteavain muodostetaan ilman kirjoittajaa toimittajasta tai otsikon
  ensimmäisestä sanasta, ja vuoden puuttuessa ilman vuotta
- Uudet tyypit näkyvät listauksessa, BibTeXissä ja lähdeluettelomuodossa, ja
  tarkennetun haun tyyppisuodattimessa on sama `more`-valikko

### Muutokset

- Tietokannan rakenne päivittyy olemassa olevaan tietokantaan datan
  säilyttäen (`db_helper.py --if-missing`); klusterilla komento ajetaan
  julkaisun jälkeen

### Laadunvarmistus

- Yksikkö- ja Robot Framework -testit uusille tyypeille ja tietokannan
  rakenteen päivitykselle

## 1.2.0 - 2026-11-23

### Ominaisuudet

- Vahvistusikkuna, kun lisättävä viite on sama kuin jo olemassa oleva viite
  (sama tyyppi ja samat kentät avaimesta riippumatta)
- Sama vahvistus viitettä muokattaessa, jos muutettu viite on sama kuin jokin
  toinen viite

### Laadunvarmistus

- Yksikkö- ja Robot Framework -testit saman viitteen tunnistukselle ja
  vahvistusikkunalle

## 1.1.0 - 2026-11-23

### Ominaisuudet

- .bib-tiedoston luominen valituista viitteistä (`create .bib`)

### Muutokset

- BibTeX-sivun kopiointipainikkeen teksti on `copy bibtex`, eikä painikkeen
  koko muutu kopioinnin jälkeen
- Harmaa teksti ja lomakkeiden viivat ovat tummempia
- Viitelistan viitetyyppi ja julkaisupaikka näytetään mustalla

### Laadunvarmistus

- Yksikkö- ja Robot Framework -testit .bib-tiedoston luomiselle
- GitHub Releasen kuvaus luodaan CHANGELOG.md:n perusteella

## 1.0.0 - 2026-11-23

Ensimmäinen GitHub Release -julkaisu.

### Ominaisuudet

- Käyttäjätunnusten luominen sekä sisään- ja uloskirjautuminen
- Viitteiden lisääminen, muokkaaminen, haku, listaus ja poistaminen
- Tuki artikkeli-, kirja- ja konferenssiviitteille
- Yksittäisen viitteen BibTeX-vienti (kopiointi)
- Yksinkertainen ja tarkennettu haku
- Docker-kuva ja OKD-kubernetesmanifestit

### Laadunvarmistus

- Yksikkötestit ajetaan pytestillä
- Robot Framework -selaintestit ajetaan CI:ssa
- Pylintin laaduntarkistus on CI:n osa
