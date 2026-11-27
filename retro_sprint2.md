# Sprintin 2 retrospektiivi

### Retrospektiivin toteutus

Retrospektiivi pidettiin sprintin 2 päätteeksi käyttäen kierroksiin perustuvaa menetelmää. Tiimissä on neljä jäsentä. Retrospektiivissä käytiin läpi sprintin onnistumisia, kehityskohteita ja toimintatapoja, joista olisi hyvä luopua. Lisäksi arvioitiin ensimmäisessä retrospektiivissä sovittujen parannuskohteiden toteutumista.

---

### 1. Edellisen retrospektiivin parannuskohteet

Ensimmäisessä retrospektiivissä sovittiin kolmesta parannuskohteesta: käyttäjätarinoiden hyväksymiskriteerien määrittelystä, käyttäjätarinoiden yhteisestä katselmoinnista sekä tehtävien jakamisesta tarvittaessa pienempiin kokonaisuuksiin.

Parannuskohteet toteutuivat vain osittain. Sprintin 2 arvioinnissa todettiin, että käyttäjätarinoiden hyväksymiskriteerit oli kirjattu riittävän tarkasti käyttäjätarinoihin #10 ja #29, mutta osasta käyttäjätarinoita ne puuttuivat tai olivat edelleen liian yleisellä tasolla. Myös toteutuksen Definition of Done -määrittelystä puuttui hyväksymiskriteerejä osan käyttäjätarinoista osalta.

Keskeinen havainto oli, että sovittua toimintatapaa ei ollut vielä vakiinnutettu osaksi kaikkien käyttäjätarinoiden valmistelua. Pelkkä parannuskohteen kirjaaminen backlogiin ei siten riittänyt varmistamaan sen toteutumista.

### 2. Kierros: Mikä sujui sprintissä hyvin?

Tiimin jäsenet nostivat esille seuraavia onnistumisia:

* **Koodin kehittäminen:** Toteuttaminen sujui edelleen hyvin ja työ eteni suunnitellusti.
* **Tiimin yhteistyö:** Yhteistyö pysyi sujuvana ja tiimin jäsenet osallistuivat työskentelyyn tasapuolisesti.
* **Viestintä:** Discord toimi edelleen tarkoituksenmukaisena viestintäkanavana. Sen kautta pystyttiin keskustelemaan toteutuksesta ja ratkaisemaan esille tulleita ongelmia.
* **Ongelmanratkaisu:** Teknisiin ongelmiin löydettiin ratkaisuja yhteistyössä ilman merkittäviä viivästyksiä.

> **Yhteenveto:** Sprintin työskentely sujui kokonaisuutena hyvin ja pitkälti samalla tavalla kuin ensimmäisessä sprintissä. Tiimin yhteistyössä tai teknisessä toteutuksessa ei tunnistettu merkittäviä uusia ongelmia. Hyväksi havaittuja toimintatapoja, erityisesti Discordin käyttöä ja yhteistä ongelmanratkaisua, päätettiin jatkaa.

### 3. Kierros: Mitä olisi voinut tehdä paremmin?

Keskustelussa nousi edelleen esille käyttäjätarinoiden tarkkuus ja erityisesti ensimmäisessä retrospektiivissä sovittujen parannusten keskeneräisyys:

* Käyttäjätarinoiden hyväksymiskriteerejä ei ollut määritelty kaikille sprintin tehtäville riittävän tarkasti.
* Definition of Done -määrittelystä puuttui osan käyttäjätarinoista osalta hyväksymiskriteerejä.
* Ensimmäisessä retrospektiivissä sovittu hyväksymiskriteerien määrittely ei ollut toteutunut kaikissa käyttäjätarinoissa.
* Hyväksymiskriteerien kirjaamisessa olisi pitänyt varmistaa myös niiden yhteys mahdollisiin Robot Framework -testeihin.
* Sovittujen parannuskohteiden toteutumista olisi pitänyt seurata järjestelmällisemmin sprintin aikana.

> **Yhteenveto:** Käyttäjätarinoiden laadintaan liittyvät ongelmat jatkuivat myös toisessa sprintissä. Erityisesti hyväksymiskriteerien määrittelyyn ja niiden sisällyttämiseen Definition of Done -määrittelyyn tulee kiinnittää enemmän huomiota. Sovittujen parannusten toteutumista on myös seurattava aktiivisemmin.

### 4. Kierros: Mitä tekemistä pitäisi lopettaa?

Keskustelussa tunnistettiin seuraavia toimintatapoja, joita tulisi välttää:

* Käyttäjätarinoiden siirtäminen sprintin backlogiin ilman riittävän tarkkoja hyväksymiskriteerejä.
* Olettaminen, että käyttäjätarinan sisältö on riittävän selkeä ilman yhteistä tarkistamista.
* Parannuskohteiden kirjaaminen backlogiin ilman, että niiden toteutumiselle määritellään selkeä vastuu ja seuranta.
* Käyttäjätarinoiden ja Robot Framework -testien välisen yhteyden jättäminen epäselväksi.

> **Yhteenveto:** Epäselvien käyttäjätarinoiden siirtämistä toteutukseen ja sovittujen parannusten jättämistä ilman seurantaa tulee välttää. Käyttäjätarinoiden vaatimukset ja niiden toteutumisen todentaminen on varmistettava ennen varsinaisen kehitystyön aloittamista.

### 5. Päätetyt parannuskohteet seuraavaan sprinttiin

Seuraavat kolme parannuskohdetta valittiin seuraavaan sprinttiin:

* **Hyväksymiskriteerien kattavuuden varmistaminen:** Jokaiselle sprinttiin valittavalle käyttäjätarinalle määritellään riittävän tarkat ja testattavissa olevat hyväksymiskriteerit ennen sprintin aloittamista. Hyväksymiskriteerien puuttuminen tarkistetaan osana sprintin suunnittelua.
* **Definition of Done -määrittelyn täydentäminen:** Käyttäjätarinoiden Definition of Done -määrittelyyn sisällytetään tarvittavat hyväksymiskriteerit. Lisäksi varmistetaan, että mahdolliset Robot Framework -testit on yhdistetty selkeästi niitä vastaaviin käyttäjätarinoihin ja että product backlogista löytyy linkki testitiedostoihin.
* **Parannuskohteiden toteutumisen seuranta:** Retrospektiivissä sovitut parannuskohteet lisätään sprintin backlogiin erillisinä tehtävinä. Niille nimetään vastuuhenkilöt ja niiden toteutuminen tarkistetaan sprintin aikana sekä seuraavan retrospektiivin alussa.

Parannuskohteille nimetään vastuuhenkilöt seuraavan sprintin suunnittelun yhteydessä.

### 6. Muita tunnistettuja mahdollisia parannuskohteita

Keskustelussa nousi esille myös seuraavia toimintatapoja, joita voidaan hyödyntää tulevissa sprinteissä:

* Käyttäjätarinoiden hyväksymiskriteerien riittävyys tarkistetaan ennen niiden hyväksymistä sprintin backlogiin.
* Robot Framework -testien yhteydessä dokumentoidaan selkeästi, mitä käyttäjätarinaa kukin testi koskee.
* Sprintin aikana seurataan säännöllisesti, ovatko sovitut parannuskohteet toteutumassa.
* Käyttäjätarinoiden valmistumisen yhteydessä tarkistetaan, että hyväksymiskriteerit ja Definition of Done täyttyvät.
* Tiimin yhteisiä katselmointeja hyödynnetään erityisesti silloin, kun käyttäjätarinan vaatimukset tai toteutustapa ovat epäselviä.

---

### 7. Yhteenveto

Toinen sprintti onnistui kokonaisuutena hyvin ja työskentely sujui pitkälti ensimmäisen sprintin tapaan. Tiimin yhteistyö, viestintä ja tekninen toteutus toimivat edelleen hyvin. Merkittäviä muutoksia tiimin työskentelytavoissa ei tapahtunut.

Keskeiseksi kehityskohteeksi nousi kuitenkin ensimmäisessä retrospektiivissä sovittujen parannusten puutteellinen toteutuminen. Erityisesti käyttäjätarinoiden hyväksymiskriteerit olivat edelleen osittain puutteellisia, eikä Definition of Done -määrittely ollut kaikilta osin riittävä.

Seuraavassa sprintissä keskitytään hyväksymiskriteerien kattavuuden varmistamiseen, Definition of Done -määrittelyn täydentämiseen sekä sovittujen parannuskohteiden järjestelmälliseen seurantaan. Tavoitteena on, että retrospektiiveissä tunnistetut kehityskohteet muuttuvat konkreettisiksi muutoksiksi tiimin työskentelytavoissa.

Seuraavan retrospektiivin alussa arvioidaan sekä ensimmäisen että toisen retrospektiivin parannuskohteiden toteutumista.