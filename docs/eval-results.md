# Evaluation results

Generated 2026-09-29T03:16:51+00:00 from the deployed API. POST /api/v1/bulletins/read-known and read-latest on the deployed API (Gemini on Agent Platform); labels are hand-entered drafts pending human confirmation.

## Bulletin Reader (AI_AGENTS §9)

| Bulletin | Pages | Label agreement | Checks failed | Needs review |
| --- | --- | --- | --- | --- |
| Montha · National Bulletin No. 19 | 16 | 48/49 | none | no |
| Montha · National Bulletin No. 21 | 17 | 48/49 | quote_verbatim | yes |
| Live · IMD National Bulletin No. 4 (2026, BOB/07/2026) | 8 | no labels | none | no |

Differences from the labels are listed per bulletin in `apps/web/src/data/eval_bulletins.json`. The Montha labels are drafts (hand-entered from the PDF text layer); they are not yet confirmed by a second person.

Ask AURORA scripted questions and advisory back-translation scores are pending.
