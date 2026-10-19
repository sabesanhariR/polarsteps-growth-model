# KPI tree (v0.2)

Every metric below is a **hypothesis**. This is an outside-in model built on public data. I have no Polarsteps internal data, and the metric choices are not Polarsteps' actual KPIs, just my proposals for discussion.

Framework: Adopted from Reforge, "North Star metrics" (NSMs). A North Star has a unit of value, a quality filter and a frequency. Input metrics are the leading indicators that drive it.

Source: Reforge: ["How to Choose & Measure North Star Metrics: Acquisition, Retention, & Monetization"](https://www.reforge.com/blog/north-star-metrics)


## What this model targets

The model targets the **acquisition** North Star. It does not model retention or monetization (see "Not modelled" below).

v0.1 counted cumulative users. v0.2 also reports active users, calculated as cumulative users × `active_share`. This is a static ratio with no churn, so it is a rescaling of the same growth curve and not a retention model. The active-user target used in the model is a placeholder.


## 1. Acquisition

| Component | Hypothesis |
|---|---|
| Unit of value | New users |
| Quality | New users who go on to create a trip and stay active (not installs or sign-ups) |
| Frequency | Monthly. Travel is seasonal, so compare like periods year on year. |


Input metrics (hypotheses):

| Input metric | Why it drives acquisition | Model input |
|---|---|---|
| Invites sent per trip | Starts the referral loop | `invites_per_trip` |
| Invitee conversion (invite to install or join) | Turns invites into users | `conversion` |
| Share of users who are active trip creators | Decides which users send invites | `active_share` |
| Paid share of new users | Adds acquisition on top of the loop | `paid_share_start` |
| Decline in the paid boost over time | Describes how fast the paid boost fades (per year) | `paid_decay` |
| Addressable travellers | Upper limit on reachable users | `addressable_m` |

Derived: `k` is the model's annual logistic growth rate, not a viral K-factor. In the forward model, `k_t = active_share × invites_per_trip × conversion × (1 + paid_share_start × (1 − paid_decay)^t)`. Growth data identifies only this product. `conversion` is solved from `k` in each draw, so it absorbs any growth that the other inputs do not explain (for example word of mouth).


## 2. Retention (not modelled)

| Component | Hypothesis |
|---|---|
| Unit of value | Active users |
| Quality | Breadth: a meaningful action (logging a trip step or photo) rather than an app open. Depth: how many such actions. |
| Frequency | Trip-based. A monthly window may fit poorly, since use is bursty. Open question. |

Input metrics (hypotheses): trip creation within the first week, trip steps logged per active trip, second-trip creation, return after a trip ends.

Model link: only `active_share` touches this level, as a static ratio, not a retention curve.


## 3. Monetization (not modelled)

| Component | Hypothesis |
|---|---|
| Unit of value | Revenue |
| Quality | Revenue by stream: Travel Books, booking affiliate commissions, Polarsteps Plus. Recurring versus one-off. |
| Frequency | Irregular for books and affiliate, so a longer window than monthly. |

Input metrics (hypotheses): share of completed trips that lead to a book, bookings started in the app, Plus conversion.

Source for the revenue streams: Clare Jones, ["How does Polarsteps make money?"](https://lnkd.in/p/et28vG4M).


## Why this metric

**The question.** Following Lenny Rachitsky's framing ("Choosing Your North Star Metric"), I started from this question: which metric, if it increased today, would most accelerate Polarsteps' flywheel? Polarsteps has a free app and several revenue streams (Travel Books, booking affiliate commissions, Plus). In consumer products with a large free base, he describes teams choosing engagement or customer growth as the North Star, and not revenue. Polarsteps is not in his survey, so I treat this as an analogy, more than a rule.

**v0.1 counted cumulative users.** That is a total of all sign-ups ever made. None of the six North Star categories in the article is cumulative sign-ups. The closest, **engagement growth**, counts users who are active. A cumulative count can rise while the product gets no better, because every inactive user stays in the total. Some companies track weekly active paid users rather than paid users for a similar reason: inactive users soon churn.

**v0.2 reports active users alongside it.** I use `active_share` to turn cumulative users into an estimate of active users. This moves the model closer to the quality filter that Reforge and Lenny both argue for.

| Candidate | What it measures | Fit | Verdict |
|---|---|---|---|
| Cumulative sign-ups (v0.1 output) | Total users ever registered | Cannot fall, ignores quality | Kept for comparison only |
| Active users (v0.2 output) | Users who currently use the product | Closer to value delivered | Model output |
| Active trip creators (hypothesis) | Users who create or log trips in the period | Matches the product's core job; needs internal data | Proposed as the full-product acquisition quality metric |
| Revenue | Money earned | Spiky, lagging, and dependent on three streams | Not modelled |


**Tradeoffs and caveats.**
- `active_share` is a single static ratio. A real active-user metric needs a time window and a definition of "active", and I do not know Polarsteps' definition.
- Active share is a judgement prior that calibration only filters. It is not a measurement of Polarsteps' activity.
- A single number can be gamed. If a team were rewarded on active users, a quality metric such as trips logged per active user would be needed next to it.
- This is a proposal for discussion. I have no access to Polarsteps' internal data, and the right metric may differ (to be more specific, yes it will differ - I'm just hoping that it doesn't vary by too much).

**Input metrics.** Following the article's habit of splitting a North Star into its drivers, the acquisition inputs are in the model input map below: invites per trip, invitee conversion, active share, paid share and paid decay.

Source: Lenny Rachitsky, ["Choosing Your North Star Metric"](https://future.a16z.com/north-star-metrics/) (a16z Future).


## Model input map

| Model input | Level in tree | Basis | Calibrated p10 / p50 / p90 |
|---|---|---|---|
| `addressable_m` | Acquisition ceiling | Eurostat EU27 travellers × adoption share (judgement) × rest-of-world multiplier (placeholder) | 128.7 / 172.6 / 239.3 |
| `active_share` | Acquisition quality | Judgement prior, filtered by calibration | 0.210 / 0.270 / 0.343 |
| `invites_per_trip` | Acquisition input | Judgement prior (mode 5, in line with a press-reported figure of about 5, unverified), filtered by calibration | 3.77 / 5.19 / 6.75 |
| `conversion` | Acquisition input | Solved from `k` in each draw (prior range 0.02 to 0.12, not used directly) | 0.192 / 0.291 / 0.428 |
| `paid_share_start` | Acquisition input | Judgement prior, filtered by calibration | 0.075 / 0.166 / 0.269 |
| `paid_decay` | Acquisition input | Judgement prior, filtered by calibration | 0.100 / 0.163 / 0.238 |
| `k` | Annual logistic growth rate | Calibrated to the 15M and 25M user counts | 0.404 / 0.460 / 0.524 |

After calibration only `k` (the product of the loop inputs) is identified, so individual values should not be read on their own. Note that the solved `conversion` (median 0.29) is well above its prior range (0.02 to 0.12). I read this as `conversion` absorbing all growth beyond the modelled invite loop, such as word of mouth and search, so it should not be read as a literal invite-to-install rate.


## Not modelled
- Retention curves by cohort.
- Revenue and unit economics.
- Differences by country (relevant for a wild card such as India).
- Seasonality of trips.


## Data I would ask for
Referral-attributed installs, paid versus organic split, trip-creation rate by cohort, invites sent per trip.