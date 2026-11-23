# Muutosloki

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
