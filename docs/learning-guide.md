# Learn, reproduce and defend the decisions

This is a practical guide, not a script for pretending to know work you have not studied. AI tools can accelerate implementation; statistical judgment still has to survive questions, changed assumptions and debugging.

## Two-day sequence

### Day 1 — own the statistical reasoning

1. **First hour: trace one cell.** Load Wholesale, select a Region/Channel group and manually sum the Fresh values. Calculate contributor count, largest contribution and top-two dominance. Explain why the largest cell need not be the riskiest.
2. **Second hour: trace the keyed method.** Follow one contributor through HMAC, modular aggregation, lookup and magnitude scaling. Change row order and grouping order. Explain why the output stays fixed. Explain why a public seed is not a production secret.
3. **Third hour: reproduce all comparators.** Run the pipeline. Compare error, withholding coverage and risk proxy together. Find a case where capping reduces usefulness. Do not memorize only the most favorable result.
4. **Fourth hour: recover a suppressed value.** Work through the 2×2 unit-test example with a pen. Explain why hiding one entry while publishing exact margins fails. Run the real 3×6 wholesale case. Inspect feasible intervals before and after extra suppression.
5. **Fifth hour: challenge the metrics.** Explain a case with no sensitive cells, full withholding, zero sums and a zero lookup value. Tell a reviewer why a low direct risk proxy does not prove confidentiality.
6. **Final exercise: change the hypothesis.** Modify the dominance threshold and delta in a separate branch. Predict the likely direction before running. Record whether your prediction was correct and what surprised you.

### Day 2 — own the software and project delivery

1. **API and boundaries:** run the HTTP service, make a valid request and submit an invalid grouping/seed. Explain what is allowlisted, why raw diagnostics are withheld, and what linked-query risk remains.
2. **Debugging:** copy a processed file, modify one byte and trigger the checksum test. Add a duplicate contributor and trigger validation. Change the noise scale above its supported bound and explain the failure.
3. **Geography:** explain why great-circle neighbour ordering is used, what Moran's I measures, why k=2/4/8 changes the question, and why non-significant p does not prove absence of risk. Explain the settlement-data limitations.
4. **Reproduction:** execute the independent full rerun. Explain random seed uncertainty versus population uncertainty. Read the paired capping contrast and identify the actual unit of replication.
5. **Code change:** make one substantive improvement yourself, such as an additional failure-case test or a clearly separated measure of signed bias. Show the before/after behavior, explain your test and commit the change.
6. **Communication:** give a five-minute explanation to a non-specialist, then a ten-minute technical walkthrough. Ask the listener to identify a limitation you missed. Record real feedback and changes, if any.

## Interview questions worth being able to answer

1. What is a magnitude table, and how does it differ from a count table?
2. What exactly is a contributor in each of your three datasets?
3. Why use public data, and what does this stop you claiming?
4. Why might two contributors dominate a cell with a fairly large count?
5. Why is confidentiality a property of a release system rather than one isolated output?
6. How do exact margins defeat primary suppression?
7. What are the variables, constraints and objective in your reconstruction linear programs?
8. Does a zero-width interval imply recovery under every possible attacker model?
9. Why can complementary suppression be expensive or wasteful?
10. Why does fresh random noise lose protection when identical outputs are averaged?
11. What does fixed-key consistency solve, and what does it leave unsolved?
12. Why is your lookup distribution illustrative rather than official?
13. How do you guarantee nonnegative released values without clipping?
14. What happens if the data include negative amounts or repeated contributors?
15. Why scale noise to a largest contribution rather than add a fixed monetary amount?
16. Why might capping introduce bias even when the noise is centered?
17. Why is the 95th percentile itself a sensitive setting on confidential data?
18. Why keep coverage separate from error on visible cells?
19. What happens when a denominator is zero?
20. What is the difference between your near-truth indicator and an estimated re-identification probability?
21. Why are 30 key seeds not 30 independent population datasets?
22. What does a 95% interval in this experiment actually describe?
23. Why is one query family not independent of another?
24. Why use real geographic coordinates and great-circle distances?
25. What would make a point-neighbour graph unsuitable for a particular statistical release?
26. Why do overlapping settlement definitions prevent treating their sum as national population?
27. What changed when you varied the neighbourhood size?
28. Which API fields would accidentally expose confidential diagnostics?
29. How would you version keys and releases when the underlying dataset updates?
30. What would a production integration require beyond your prototype?
31. Which result challenges your original expectation?
32. What did you personally change, verify and learn after the AI-assisted build?

## A truthful five-minute project narrative

Use the structure: problem → contributor unit → threat assumptions → comparator design → measured result → failure case → limitations → next experiment. Use only results in the recorded files. State that the implementation used AI support when relevant. Distinguish your own reviewed changes from generated starting code. Do not present a learning prototype as past client work or agency employment.

## Evidence of learning to add later

Keep a short dated decision log of actual work: predicted outcome, command or code change, observed result, interpretation and remaining question. An honest follow-up commit with your reasoning is stronger evidence of ownership than claiming instant expertise from a generated repository.
