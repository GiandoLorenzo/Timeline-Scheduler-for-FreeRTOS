# Pubblicazione su GitHub

La cartella scaricata non contiene la cronologia Git. I comandi seguenti creano un nuovo repository locale e un primo commit; non recuperano i commit del progetto originario.

1. Verifica il README e la relazione pubblica. La copia originale della relazione, se presente in `private/`, e i file temporanei sono esclusi da Git e dal contesto Docker. Non caricare la cartella tramite trascinamento nel browser e non condividerne uno ZIP completo: questi metodi non applicano `.gitignore`.
2. Esegui i test Python e, con Linux/WSL o Docker, i test QEMU descritti nel README. I test del firmware richiedono una toolchain ARM e non possono essere confermati dalle sole verifiche Python.
3. Controlla che tu e gli altri contributori possiate pubblicare codice e documentazione del corso. Conserva le attribuzioni e le licenze incluse.
4. In GitHub crea un repository vuoto. Per verificare la CI prima di renderlo pubblico, inizialmente scegli **Private**. Non aggiungere README, licenza o `.gitignore` tramite GitHub: sono già nella cartella.

In PowerShell, dentro la cartella del progetto:

```powershell
git init -b main
git config user.name "IL TUO NOME PUBBLICO"
git config user.email "LA TUA EMAIL NOREPLY DI GITHUB"
git add .
git status --short
git diff --cached --stat
git diff --cached --check
git check-ignore private/ tmp/ artifacts/
```

Sostituisci nome ed email con i tuoi dati. Puoi copiare l'indirizzo noreply dalle impostazioni email di GitHub, per evitare di pubblicare l'email personale nei commit. Queste impostazioni valgono solo per questo repository.

Controlla i file in staging, quindi:

```powershell
git commit -m "Prepare timeline scheduler for publication"
git remote add origin https://github.com/TUO-USERNAME/NOME-REPOSITORY.git
git push -u origin main
```

Sostituisci l'URL con quello del repository appena creato. Usa l'autenticazione tramite browser/Git Credential Manager; non inserire token nell'URL, nei sorgenti o nel README.

Dopo il push, apri **Actions** e controlla tutti i job. Se un test fallisce, mantieni il repository privato e correggi il problema: non considerare un semplice messaggio nel log come prova di successo. La CI controlla risultati espliciti e conserva i log.

Quando i controlli sono verdi, completa descrizione e argomenti del repository, abilita la segnalazione privata delle vulnerabilità se disponibile e cambia la visibilità in Public dalle impostazioni. La modifica della visibilità rende pubblici anche i commit: evita di committare dati personali fin dal primo commit.

Se invece desideri preservare la cronologia originale, parti da un clone autentico e analizza anche tutti i commit prima del push. `.gitignore` non rimuove file già tracciati o segreti già presenti nella cronologia.
