# Scoring details

Score = skills + experience + location + company + pay, using the weights in `config.json → scoring.weights` (defaults below). Scale each part to its weight.

## Skills (40)
| Points | When |
|---|---|
| 36–40 | The core of the job is work the candidate has evidenced, in the same domain |
| 28–35 | Most of the core is evidenced; one important area is claimed or learning |
| 15–27 | Adjacent: transferable skills, but the main stack or domain is new |
| 0–14 | Mostly skills the candidate doesn't have |
Only `evidenced` skills count fully. `claimed` counts half. `learning`, `none` and not-yet-assessed skills count zero. A required skill the candidate doesn't have is a hard-filter skip only when the posting makes it central ("must have", the main stack); otherwise it just lowers the skills points and goes in the gap line.

## Experience (20)
| Minimum years asked vs candidate's stated years | Points |
|---|---|
| at or below | 20 |
| 1 year above | 14 |
| 2 years above | 8 |
| 3+ years above | 0, and a hard-filter skip unless `PREFERENCES.md` says the candidate wants stretch roles |
| not stated | 12 |

## Location (15)
Preferred city or preferred remote setup 15 · acceptable 10 · relocation under the candidate's condition 7 · anything else: a hard-filter skip if the candidate listed location as a hard filter, otherwise 5.

## Company (15)
Matches the candidate's "great employer" description 13–15 · unknown 8 · weak fit 4 · on their avoid list: skip.

## Pay (10)
Band covers their range 10 · overlaps 7 · not stated, or the candidate's range is unknown 5 · below floor: skip. Use the expected range in `PREFERENCES.md` (private, stays in `profile/`); never copy pay from `ANSWERS.md`.

## Bands (defaults, changeable in config)
- **≥ 70:** prepare and apply (in the platform's mode).
- **60–69:** show the candidate; they decide.
- **< 60:** skip, recorded with the reason.

## Gap line examples
"asks 4+ years vs 2", "Kubernetes in production is core; candidate has none", "on-site 5 days; candidate prefers hybrid", "pay not stated".
