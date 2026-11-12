# miniprojekti

Lukekaa pelisäännöt.

## Ennen committia

Ota Git-hook käyttöön kerran tässä työkopiossa:

```bash
git config core.hooksPath .githooks
```

Tämän jälkeen `git commit` suorittaa ensin yksikkötestit (`uv run pytest src/tests`). Jos `src/tests` sisältää Robot Frameworkin `.robot`-testejä, myös ne suoritetaan ennen commitin hyväksymistä.