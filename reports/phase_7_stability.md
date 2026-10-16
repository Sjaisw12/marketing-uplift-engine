# Phase 7 — descriptive stability

Five splits overlap. No pooled independent-replication confidence interval or final winner is computed.

| Reach | Method | Point-estimate order by split | Mean T−S [min,max] /1,000 | Positive simultaneous bands |
|---|---|---|---:|---:|
| 10% | ipw | s_learner>t_learner>response>random; s_learner>t_learner>response>random; s_learner>t_learner>response>random; s_learner>t_learner>response>random; s_learner>t_learner>response>random | -0.3641 [-0.5467, -0.2376] | 0/5 |
| 10% | dr | s_learner>t_learner>response>random; s_learner>t_learner>response>random; s_learner>t_learner>response>random; s_learner>t_learner>response>random; s_learner>t_learner>response>random | -0.1962 [-0.2797, -0.0938] | 0/5 |
| 20% | ipw | s_learner>t_learner>response>random; t_learner>s_learner>response>random; s_learner>t_learner>response>random; s_learner>t_learner>response>random; s_learner>t_learner>response>random | -0.2250 [-0.3789, 0.1078] | 0/5 |
| 20% | dr | s_learner>response>t_learner>random; s_learner>t_learner>response>random; s_learner>response>t_learner>random; s_learner>response>t_learner>random; s_learner>response>t_learner>random | -0.2104 [-0.3311, -0.0100] | 0/5 |
| 30% | ipw | s_learner>response>t_learner>random; t_learner>s_learner>response>random; s_learner>response>t_learner>random; s_learner>t_learner>response>random; s_learner>response>t_learner>random | -0.0947 [-0.2348, 0.2239] | 0/5 |
| 30% | dr | response>s_learner>t_learner>random; t_learner>s_learner>response>random; s_learner>response>t_learner>random; response>s_learner>t_learner>random; s_learner>response>t_learner>random | -0.1963 [-0.3072, 0.0292] | 0/5 |
| 40% | ipw | s_learner>response>t_learner>random; t_learner>s_learner>response>random; s_learner>response>t_learner>random; s_learner>response>t_learner>random; response>s_learner>t_learner>random | -0.0918 [-0.2970, 0.2789] | 0/5 |
| 40% | dr | response>s_learner>t_learner>random; t_learner>response>s_learner>random; s_learner>response>t_learner>random; response>s_learner>t_learner>random; response>s_learner>t_learner>random | -0.2107 [-0.3656, 0.0706] | 0/5 |
| 50% | ipw | s_learner>response>t_learner>random; t_learner>s_learner>response>random; s_learner>response>t_learner>random; s_learner>t_learner>response>random; s_learner>response>t_learner>random | -0.0920 [-0.2507, 0.2441] | 0/5 |
| 50% | dr | response>s_learner>t_learner>random; response>t_learner>s_learner>random; s_learner>response>t_learner>random; response>s_learner>t_learner>random; response>s_learner>t_learner>random | -0.2453 [-0.3872, 0.0045] | 0/5 |

A band containing zero supports no reliable difference detected under that working model. A positive band does not establish causal superiority. Propensity/nuisance sensitivity and unknown dependence can matter more than conditional sampling precision.
