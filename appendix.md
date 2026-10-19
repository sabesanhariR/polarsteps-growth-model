# Appendix: learning log

Since I'm learning and building in parallel, this is a record of what I read, what I understood, what I took from it, what changed in the repo, and what I'm still unsure about.


| Source | What I took from it | What changed in the repo | Still unsure |
|---|---|---|---|
| Reforge, ["How to Choose & Measure North Star Metrics"](https://www.reforge.com/blog/north-star-metrics) (suggested by Laurens) | North Star metrics are outcome metrics, usually one each for acquisition, retention and monetization. Each has a unit of value, a quality filter and a frequency. Input metrics are the leading indicators below them. I had mixed up business-level KPIs with the inputs beneath them. | [docs/kpi_tree.md](docs/kpi_tree.md): the three North Stars with unit, quality and frequency, input metrics, and a map from each model input to the tree. | What counts as "active" at Polarsteps. Which frequency fits a product used in bursts around trips. |
| Lenny Rachitsky, ["Choosing Your North Star Metric"](https://future.a16z.com/north-star-metrics/) | Start from the question of which metric would most accelerate the flywheel. Consumer products with a large free base often pick engagement or customer growth over revenue. A cumulative sign-up count does not fit his categories, and an active-user count is closer. | The "Why this metric" section of the KPI tree, and the active-user output in v0.2 (cumulative users x `active_share`). | Whether a static ratio is a fair stand-in for activity. How well his survey of growth-stage companies applies to Polarsteps. |
| Reforge, ["Growth Loops are the New Funnels"](https://www.reforge.com/blog/growth-loops) | A funnel does not show how one cohort of users leads to the next. A loop feeds output back into input. Few loops, well understood, beat many shallow ones. | The "Growth structure: loops, not a funnel" section, and the loop cycle-time and paid-quality items under [Planned for v0.3](README.md#planned-for-v03). | How to quantify a loop from outside. The post is conceptual, so I do not yet know how to turn its ideas into calibrated inputs. |

## Also on my list

- Imbens and Rubin, *Causal Inference for Statistics, Social, and Biomedical Sciences* (Cambridge, 2015), suggested by John. Status: not started.
- Hernan and Robins, [*Causal Inference: What If*](https://miguelhernan.org/whatifbook) (free online), suggested by John. Status: not started.

## What the reading changed in my thinking

- The headline moved from "reaching 100M users" to "100M registered users is roughly 28M active users", which is a less dramatic and more honest statement.
- I removed a viral-style reading of `k`. In this model it is an annual growth rate, and I no longer describe it as a K-factor.
- I now treat the DiD incrementality demo as the next piece of work, because the paid-acquisition term in this model is a crude assumption and the right way to learn more is to measure it.