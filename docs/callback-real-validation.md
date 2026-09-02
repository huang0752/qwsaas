# v0.4.0 real callback validation

Final `v0.4.0` is blocked until every row below has a complete, sanitized callback fixture and an approved assertion. Super Mate code and database rows are consumer evidence, not protocol truth.

| Area | Required evidence | RC status |
| --- | --- | --- |
| Private inbound | complete 11010 with current account, sender, receiver, roomid, send_flag | blocked |
| Private desktop outbound | complete 11010 | blocked |
| Private mobile outbound | complete 11010 | blocked |
| Private API outbound | send response plus complete resulting callback | blocked |
| Interleaving and two contacts | ordered complete callbacks | blocked |
| Two accounts, one contact | both account identities and callback sequences | blocked |
| Room inbound/desktop/mobile/API | four complete callbacks and direction truth table | blocked |
| 11013 | complete real batch callback | blocked |
| Text/image/file/voice/video | complete callback per type | blocked |
| Mixed/merge | complete nested payloads | blocked |
| Quote/revoke/read | original and subsidiary sequences | blocked |
| Non-message events | complete 11002/11003/11004/11011/2166 callbacks | blocked |
| Sync | complete `/sync/sync_msg` response captured separately from callbacks | blocked |

Before review, replace stable identities consistently with placeholders such as `ACCOUNT_A`, `CONTACT_A`, and `ROOM_A`; replace names and every secret/query value with `REDACTED`. Then run:

```bash
uv run python scripts/check_callback_fixtures.py
uv run pytest
```

Passing synthetic and public-document fixtures proves static behavior only. It does not satisfy this matrix.
