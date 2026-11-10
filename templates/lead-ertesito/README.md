# Lead-értesítő (sablon)

Ügyfélfüggetlen n8n csomag. Ügyfélenként klónozd a két workflow-t, és cseréld a placeholdereket meg a credentialeket. A JSON-ban nincs kulcs, token, sheet ID, chat ID és nincs belső URL.

v1 belépési pont: **Form Trigger** és **Webhook**. A Gmail Trigger, az SMS-ág és a double-submit deduplikáció nincs benne.

| Fájl | Szerep |
| --- | --- |
| `lead-ertesito.json` | Űrlap + POST webhook → normalizálás → párhuzamos válaszlevél, Google Sheet, Telegram, opcionális tulajdonosi e-mail |
| `lead-ertesito-hibakezelo.json` | Error Trigger és ághiba-hívás → tulajdonosi Telegram és e-mail |

Időzóna: `Europe/Budapest`.

## Import

1. n8n → Workflows → Import from File → `lead-ertesito-hibakezelo.json`. Aktiváld.
2. Másold ki a hibakezelő workflow ID-ját a böngésző URL-jéből.
3. Importáld a `lead-ertesito.json` fájlt.
4. A fő workflow-ban cseréld az `ERROR_WORKFLOW_ID` mindkét előfordulását erre az ID-ra: a Settings → Error Workflow mezőt, és az **Ághiba jelzése** node Workflow mezőjét.
5. Minden Gmail / Google Sheets / Telegram node-on válaszd ki a valódi credentialt. A JSON-beli `GMAIL_OAUTH2`, `GOOGLE_SHEETS_OAUTH2` és `TELEGRAM_BOT_TOKEN` csak placeholder név és id.

A hibakezelő **Ághiba hívás** triggerén az input mode **Accept all data**. Az Ághiba jelzése ezért nem küld külön mezőlistát.

## Placeholderek

Keresd meg és cseréld mindkét fájlban (vagy már az importált node-okban):

| Placeholder | Hol | Mit írj helyette |
| --- | --- | --- |
| `COMPANY_NAME` | válaszlevél, tulajdonosi üzenet, hibaüzenet | a cég neve, ahogy az aláírásban látszik |
| `FROM_NAME` | Gmail Sender Name és az aláírás | a feladó megjelenő neve |
| `REPLY_SUBJECT` | automatikus válasz tárgya | a leadnek küldött tárgy |
| `REPLY_BODY_TEMPLATE` | automatikus válasz törzse | a köszönő szöveg a név és az aláírás között |
| `OWNER_EMAIL` | tulajdonosi e-mail címzettje | a tulajdonos címe |
| `YOUR_SHEET_ID` | Google Sheets document id | a táblázat ID-ja |
| `YOUR_CHAT_ID` | Telegram chat id | a tulajdonos vagy a csoport chat ID-ja |
| `FORM_TITLE` | űrlap címe | amit a kitöltő lát |
| `FORM_DESCRIPTION` | űrlap leírása | rövid instrukció |
| `FORM_THANK_YOU` | űrlap köszönő szövege | a beküldés utáni üzenet |
| `FIELD_NAME` `FIELD_EMAIL` `FIELD_PHONE` `FIELD_MESSAGE` `FIELD_SOURCE` | Adatok normalizálása, a kulcslista első eleme | a bejövő mező kulcsa, ha nem a beépített alias |
| `ERROR_WORKFLOW_ID` | fő workflow settings + Ághiba jelzése | a hibakezelő workflow ID-ja |
| `GMAIL_OAUTH2` | Gmail credential hivatkozás | a példányban létrehozott Gmail OAuth2 credential |
| `GOOGLE_SHEETS_OAUTH2` | Sheets credential hivatkozás | a Google Sheets OAuth2 credential |
| `TELEGRAM_BOT_TOKEN` | Telegram credential hivatkozás | a bot API credential (a tokent a credential tárolja, nem a workflow) |

A Sheet fül neve a sablonban `Leadek`. Ha más a fül, a **Lead mentése (Google Sheets)** node `sheetName` értékét írd át.

A `REPLY_SUBJECT`, `REPLY_BODY_TEMPLATE`, `FROM_NAME` és `COMPANY_NAME` a Gmail node kifejezésében szimpla idézőjelben áll. A csere szövegében ne legyen aposztróf, vagy írd át a kifejezést.

## Sheet fejlécek

Az első sor, ebben a sorrendben:

`Időpont | Név | Email | Telefon | Üzenet | Forrás`

Az időpont `Europe/Budapest` szerinti `yyyy-MM-dd HH:mm:ss`. A node szövegként írja az oszlopokat.

## Mit csinál a fő workflow

1. **Új lead (űrlap)** — mezők: Név (kötelező), Email, Telefon, Üzenet. A válasz a beküldés pillanatában a `FORM_THANK_YOU` szöveg. Teszt: a node Test URL-je.
2. **Webhook (POST)** — path: `lead`. A válasz node azonnal `200` és `{"ok":true}`; utána fut a mentés. A két belépés ugyanabba a normalizálásba megy.
3. **Adatok normalizálása** — `name`, `email` (trim + kisbetű), `phone`, `message`, `source`, `received_at`. Az űrlap magyar címkéit és a webhook lapos kulcsait (`name`, `email`, …) is felismeri, valamint egy borítékot: `fields`, `data`, `form_fields`, `payload`.
4. Párhuzamos ágak, mindegyik `onError: continueErrorOutput`, hogy az egyik hibája ne állítsa meg a többit:
   - **Van érvényes e-mail?** — ha a cím üres vagy nem e-mail alakú, nincs válaszlevél. Különben **Automatikus válasz a leadnek** (Gmail, feladó neve `FROM_NAME`, aláírás `COMPANY_NAME`).
   - **Lead mentése (Google Sheets)** — append a `Leadek` fülre.
   - **Értesítés a tulajdonosnak** — Telegram HTML üzenet a lead adataival.
   - **Értesítés a tulajdonosnak (e-mail)** — alapból kikapcsolva. Bekapcsolás után a `OWNER_EMAIL` címre küld.
5. Ághiba esetén az **Ághiba jelzése** meghívja a hibakezelőt. Amíg az `ERROR_WORKFLOW_ID` nincs kicserélve, ez a hívás csendben elhasal, a lead ágai ettől még lefutnak.
6. Ami így sem kezelt hiba (a normalizálás vagy a webhook-válasz elszáll), a workflow Error Workflow beállítása indítja a hibakezelőt. Ehhez a hibakezelőnek aktívnak kell lennie.

A tulajdonosi e-mail és a Telegram a hibakezelőben egymás mellett fut; az egyik hibája nem blokkolja a másikat.

## Webhook próba

A production URL a webhook node-on látszik, import és aktiválás után. Példa törzs:

```bash
curl -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Teszt Elek","email":"te@example.com","phone":"+361234567","message":"Helló","source":"curl"}'
```

Elvárt HTTP válasz: `200` és `{"ok":true}`. Érvénytelen vagy hiányzó `email` mellett nincs válaszlevél, a Sheet-sor és a Telegram ettől még lefut.

## Offline ellenőrzés

Élő n8n példány nélkül, a repó gyökeréből:

```bash
python3 n8n-workflow-builder/scripts/validate_workflow.py templates/lead-ertesito/lead-ertesito.json
python3 n8n-workflow-builder/scripts/validate_workflow.py templates/lead-ertesito/lead-ertesito-hibakezelo.json
python3 templates/lead-ertesito/check_template.py
```

A community node-séma a Gmail node-ot még 1-es verziónak ismeri. A sablon a jelenlegi n8n Gmail v2.1 send paramétereit használja (`sendTo`, `emailType`, `senderName`); a `check_template.py` ezt az egy ismert eltérést engedi át.

## v1-ből szándékosan kimaradt

- Gmail Trigger (`info@` / `ajanlat@`)
- SMS (Twilio / MessageBird)
- deduplikáció újratöltés / double-submit ellen

Ezek külön bővítésként tehetők a normalizálás után, a párhuzamos ágak elé.
